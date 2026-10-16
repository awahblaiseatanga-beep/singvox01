# SignVox — production model delivery: custom-domain + cache design and performance validation plan (2026-10-16)

Status: **design and plan only. Nothing created, changed or applied.** No custom domain, no DNS change,
no cache rule, no purge, no Vercel change, no deploy, no file staged or committed. Every model artifact is
untouched and still matches `docs/migration/local-only-assets-sha256.txt`. This document stops at the
point where the next step needs your account and your approval.

Companion to `docs/migration/r2-hosting-runbook-2026-10-16.md` (§4 upload method, §8 verified results,
§9 Vercel values) and `docs/migration/onnx-hosting-contract-test-2026-10-16.md` (loopback contract proof).

---

## 1. Why this work is needed

All four objects are live and verified on the bucket's `r2.dev` development host, and hosted inference is
bit-identical to local inference (runbook §8). What is *not* acceptable for production is the delivery
cost, measured in a real browser on 2026-10-16:

| Transfer | Same-origin local dev server | Hosted `r2.dev` |
|---|---|---|
| `spoter_v2_model.onnx.data` (187.7 MB) | 1,614.8 ms | **357.0 s** |
| `spoter_pilot.onnx.data` (187.6 MB) | 1,639.1 ms | **297.7 s** |

≈526–630 KB/s from the browser (≈4.2–5.0 Mbps), i.e. **about six minutes** before the default model can
classify anything. This is not an accident of that one run:

* Cloudflare documents `r2.dev` as **"rate-limited and should only be used for development purposes"**
  ([Public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/)) and says it
  **"does not support caching, WAF, or bot management"**
  ([Enable cache in an R2 bucket](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/)).
* Three consecutive identical `GET`s of the graph object returned **no `cf-cache-status` and no `Age`**
  header — no edge cache is involved at all.
* A production hostname therefore is not cosmetic: it is the only way to put Cloudflare's cache, and its
  much larger footprint, in front of a 375.3 MB cold visit.

The rollout must not disturb what already works: **the four objects and their `r2.dev` URLs stay exactly
as they are** (§7), and both access methods can serve at the same time.

## 2. Measured vs estimated vs unknown

Kept deliberately separate, because two of the three are not evidence yet.

**Measured today (this machine / this browser):**

| Fact | Value |
|---|---|
| Cold hosted sidecar fetch (baseline / pilot) | 357,015.6 ms / 297,702.3 ms |
| Effective hosted throughput | ≈526 KB/s and ≈630 KB/s |
| Same files, same-origin local disk | 1,614.8 ms / 1,639.1 ms |
| ORT session init, hosted / local (baseline) | 359,471.9 ms / 3,583.7 ms |
| Inference latency, hosted / local (baseline) | 366.4 ms / 399.1 ms |
| `cf-cache-status` / `Age` on `r2.dev` | never present (no edge cache) |
| `Timing-Allow-Origin` | never present (cross-origin byte counts read 0) |
| `Content-Encoding` | never present (no compression of `application/octet-stream`) |
| TTFB, graph object | 0.34–0.53 s over TLS |
| Digest verification through the public host | 4/4 MATCH, verifier exit 0 |
| Hosted vs local logits | max abs diff 0 (79 and 3 logits) |

**Estimated (arithmetic on the measured payload, no protocol overhead, no latency, ideal sustained rate):**

| Sustained rate | Default pair (187.8 MB) | Both pairs (375.3 MB) |
|---|---|---|
| 1.6 Mbps (Lighthouse "Slow 4G") | ~15.7 min | ~31.3 min |
| 4 Mbps | ~6.3 min | ~12.5 min |
| 9 Mbps (WebPageTest "4G") | ~2.8 min | ~5.6 min |
| 12 Mbps (WebPageTest "LTE") | ~2.1 min | ~4.2 min |
| 25 Mbps | ~1.0 min | ~2.0 min |
| 100 Mbps | ~15 s | ~30 s |

For context — **not** a preset — Ookla's US H1 2025 medians were 245.48 Mbps (T-Mobile, all technologies),
116.34 Mbps (Verizon) and 115.09 Mbps (AT&T), with 5G medians of 299.36 / 214.58 / 158.56 Mbps
([Ookla report](https://www.ookla.com/research/reports/united-states-speedtest-connectivity-report-h1-2025)).
So a median modern US mobile link is not the problem; congestion, throttling, roaming, low signal and
non-US networks are.

**Unknown until measured:** how much a custom domain plus a cache rule actually improves first load
(expected large, magnitude unmeasured); the steady-state edge hit rate; behaviour of browsers other than
the one used today; HTTP/2 vs HTTP/3 (the local `curl` cannot test it).

## 3. Custom-domain + cache design

### 3.1 Prerequisite — a zone in the same account (your action)

Cloudflare documents that the hostname for an R2 custom domain must
**"have been added as a zone in the same account as the R2 bucket"**, and that Cloudflare
**"automatically adds a CNAME record that maps your domain to the bucket"**
([Public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/)). Two viable shapes:

* **Preferred — a subdomain of a domain already managed by the bucket's account**, e.g.
  `models.<yourdomain>`. Nothing changes at a registrar; this is a dashboard step.
* Otherwise, add a domain to the account first (a nameserver change at your registrar — **your** action,
  not mine), or use the documented partial/CNAME setup if the DNS lives elsewhere.

Bucket account for reference: `530150911781c2a542a4785049edc988` (from `wrangler whoami`). I can read zone
metadata only; I cannot create zones or rules (§8).

### 3.2 Custom-domain steps (dashboard; approval required)

1. R2 → **signvox-models** → *Settings* → **Public access** → **Custom Domains** → **Add** → enter the
   hostname → connect. Cloudflare adds the CNAME.
2. Confirm that CNAME is **proxied** (orange cloud). Cache Rules only apply to proxied hostnames
   ([Cache Rules](https://developers.cloudflare.com/cache/how-to/cache-rules/)).
3. **Leave `r2.dev` enabled.** Cloudflare documents the two access methods as independent
   ("enabling custom domains does not require enabling r2.dev access"), which is what keeps the current
   URLs valid as a fallback.
4. **No CORS change needed** — the existing `Access-Control-Allow-Origin: *` policy is host-agnostic.

### 3.3 The cache rule is required — otherwise the objects are never cached

Cloudflare's default cache eligibility is decided by **file extension, not MIME type**
([Default cache behavior](https://developers.cloudflare.com/cache/concepts/default-cache-behavior/)):
"Cloudflare only caches based on file extension and not by MIME type." `.onnx` and `.onnx.data` are not on
that default list, so `Content-Type: application/octet-stream` does **not** make them cacheable and the
documented default outcome is a `DYNAMIC` (uncached) response — every visitor pulling 375 MB from the
bucket, exactly as today. **That is a documented inference, not a measurement on our own zone**: it
cannot be measured until the custom domain exists, so the rule is specified up front and P1 in §4.2 is
what confirms it (`MISS` then `HIT`).

Proposed rule (**one** rule; Caching → Cache Rules → Create rule):

| Setting | Value |
|---|---|
| Name | `signvox-model-objects-immutable` |
| Expression | `(http.host eq "models.<yourdomain>") and (ends_with(http.request.uri.path, ".onnx") or ends_with(http.request.uri.path, ".onnx.data"))` |
| Cache eligibility | **Eligible for cache** |
| Edge TTL | **Use cache-control header if present** (API mode `respect_origin`) |
| Browser TTL | **Respect origin** |

Why these values: the objects already carry `Cache-Control: public, max-age=31536000, immutable`, so
`respect_origin` gives them a one-year edge lifetime without an override, and browser behaviour keeps the
origin's policy. Note that `immutable` has **no effect on Cloudflare's edge cache** — edge freshness comes
from `max-age`
([Origin Cache Control](https://developers.cloudflare.com/cache/concepts/cache-control/)). Plan fit:
Cache Rules exist on the Free plan with a **10-rule** allowance, and the cacheable-object ceiling on
Free/Pro/Business is **512 MB per file**, which our 187 MB objects are under
([Default cache behavior](https://developers.cloudflare.com/cache/concepts/default-cache-behavior/)).

Ruleset API sketch (for review — **not to be run without your approval**, and not possible with any
credential currently on this machine):

```json
{
  "rules": [{
    "expression": "(http.host eq \"models.<yourdomain>\") and (ends_with(http.request.uri.path, \".onnx\") or ends_with(http.request.uri.path, \".onnx.data\"))",
    "action": "set_cache_settings",
    "action_parameters": {
      "cache": true,
      "edge_ttl": { "mode": "respect_origin" },
      "browser_ttl": { "mode": "respect_origin" }
    }
  }]
}
```

### 3.4 Deliberately not proposed

* **No "Cache Everything" page rules** (legacy mechanism; Cache Rules cover it).
* **No compression of the model objects.** Cloudflare's documented compressible content-type list does not
  include `application/octet-stream`
  ([Content compression](https://developers.cloudflare.com/speed/optimization/content/compression/)), and
  enabling a compression rule over digest-verified binaries buys little on ONNX data while adding a way for
  the served bytes to diverge from what we hashed. Cloudflare documents `no-transform` as the way to forbid
  it if a compression rule is ever enabled — **that would require re-uploading metadata and therefore your
  approval**, and it is unnecessary today.
* **No cache-rule change to the `r2.dev` hostname** — it cannot cache, so a rule there is pointless.
* **No purge, no CORS edit, no bucket change, no object overwrite** as part of this design.

### 3.5 Optional measurement aid (approval required)

R2 sends no `Timing-Allow-Origin`, which is why browser byte counters read 0 (§2). A **Response Header
Transform Rule** on the custom domain (free) adding `Timing-Allow-Origin: https://<app-origin>` would make
`transferSize`/`encodedBodySize` readable in real-user measurement for these public, non-secret objects.
Recommended as a *measurement* aid, not required for delivery; add it in the same change window if you
approve it.

## 4. Performance validation plan

### 4.1 Acceptance criteria (proposed — please confirm or set your own)

| # | Criterion | Proposed threshold |
|---|---|---|
| AC1 | Warm edge load, default pair, browser disk cache enabled | ≤ 2 s; browser bytes ≈ 0; `cf-cache-status: HIT` with `Age > 0` |
| AC2 | Cold first load, healthy link (≥ 25 Mbps) | ≤ 60 s default pair; ≤ 120 s both pairs |
| AC3 | Cold first load, WebPageTest "4G" (9 Mbps) | ≤ 3 min default pair |
| AC4 | Digest integrity **through the custom domain** | 4/4 MATCH; verifier exit 0 |
| AC5 | Inference equality through the custom domain | max abs logit diff 0 for both models |
| AC6 | ORT init, hosted warm cache | ≤ local-file init (3,583.7 ms / 2,774.1 ms measured today) |
| AC7 | Low-bandwidth behaviour (≤ 4 Mbps, incl. Lighthouse "Slow 4G") | **Product decision required** — the default pair physically needs ≥ 6 min at 4 Mbps and ~16 min at 1.6 Mbps, so either the UI must carry the wait or the payload/serving strategy must change |

AC7 is a finding, not a pass/fail: 179 MB cannot be made fast on a constrained link by caching alone. If
mobile-first matters, the alternatives are progressive/background prefetch of the default model only, a
smaller or quantised model, or an explicit "preparing recognition" state. Each of those touches frozen
artifacts or product behaviour and needs its own approval.

### 4.2 Phases

| Phase | What it establishes |
|---|---|
| **P0 — local reference (done)** | Same-origin 1.6 s per sidecar; the upper bound caching can approach |
| **P1 — custom domain, unthrottled** | The real improvement; first `MISS`, then `HIT` |
| **P2 — cold vs warm** | Cold after purge vs `HIT`; byte accounting; hit rate under repetition |
| **P3 — throttled profiles** | Behaviour on constrained links; time-to-first-recognition, not just bytes |
| **P4 — real device on cellular** | The only test that includes radio behaviour; needs a phone and mobile data, outside this machine |

### 4.3 How each metric is measured (so no number is folklore)

* **Cold**: purge the object's URL (single-file purge by full hostname) or use a fresh browser profile, then
  measure. **Do not** cache-bust with query strings — that changes the cache key and measures the origin,
  not the cache.
* **Warm**: repeat the same URL and require `cf-cache-status: HIT` with `Age > 0`
  ([cache responses](https://developers.cloudflare.com/cache/concepts/cache-responses/)). Range behaviour
  must still return `206` through the cache; Cloudflare may fetch origin ranges aligned to 1 MiB
  ([Range requests](https://developers.cloudflare.com/cache/reference/range-requests/)).
* **Actual transferred bytes**, three independent views:
  1. **Cloudflare analytics** (our own zone): cached vs origin bytes and cache hit rate — the authoritative
     view of what the edge served.
  2. **CDP / Playwright instrumentation**: `Network.dataReceived` + `loadingFinished` encoded lengths, or
     `Request.sizes()`, which the page-level `PerformanceResourceTiming` cannot provide when
     `Timing-Allow-Origin` is absent ([MDN `transferSize`](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceResourceTiming/transferSize)).
  3. **Browser timing** (`responseEnd - startTime`, already reliable cross-origin) with sizes read only if
     §3.5 is approved.
* **ORT initialisation**: instrument `SpoterInferenceSession.create()` and `warmup()`, as done in the
  runbook §8.2 run, and compare hosted vs local on the same machine.
* **Sampling**: at least **5 cold and 5 warm runs per profile**, reporting median and p95 — a single sample
  will not be quoted as a result.
* **Correctness gate**: `node tools/verify_onnx_hosting.mjs --base https://<model-host> --origin <app origin>`
  plus the browser equality test must pass **before** any app points at the new host, and again after.

### 4.4 Throttling approach

* **Preferred**: packet-level shaping, which reproduces latency and loss and is what Lighthouse's guidance
  treats as the more realistic option (proxy-level tools "do not affect UDP"; Linux `netem` documents
  delay/loss/jitter and their limits — [Lighthouse throttling](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md),
  [`tc-netem`](https://man7.org/linux/man-pages/man8/tc-netem.8.html)). On Windows a shaping tool is needed;
  loopback shaping is fiddly.
* **Practical fallback on this machine**: a local rate-limiting reverse proxy in front of the model host
  (token bucket) which the browser is pointed at. It caps sustained throughput reproducibly, but it does
  **not** model TCP slow start, radio conditions, handovers, variable latency or QUIC/UDP — so results from
  it are a lower-bound approximation and must be labelled as such.
* **Profiles** (documented values, not invented):

| Profile | Down | Up | Latency | Source |
|---|---|---|---|---|
| Lighthouse / Chrome "Slow 4G" (formerly Fast 3G) | 1.6 Mbps | 750 Kbps | 150 ms | [Lighthouse throttling](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md) |
| WebPageTest "3G" | 1.6 Mbps | 768 Kbps | 300 ms | [connectivity.ini.sample](https://github.com/WPO-Foundation/webpagetest/blob/master/www/settings/connectivity.ini.sample) |
| WebPageTest "4G" | 9 Mbps | 9 Mbps | 170 ms | same |
| WebPageTest "LTE" | 12 Mbps | 12 Mbps | 70 ms | same |
| WebPageTest "4G Fast" | 10.24 Mbps | 10.24 Mbps | 40 ms | same |

  Chrome DevTools does expose a "slow 4G" preset, but its numeric values are not published in Google's
  documentation, so the Lighthouse-configuration row above is what will be quoted.
* **Also record** `navigator.connection.effectiveType` / `downlink` and **time-to-first-recognition**
  (model download + ORT init + first successful window) — bytes alone do not describe the user experience.

### 4.5 Output of the validation run

One results table per profile — cold ms, warm ms, bytes cold/warm, `cf-cache-status`, ORT init, first
inference, plus the digest and equality gates — appended to this document (or a dated results doc, matching
the repo's contract-test convention). Unmeasured cells stay explicitly empty rather than estimated.

## 5. Cutover and rollback

1. Custom domain connected, cache rule live, `r2.dev` untouched.
2. Run the full gate against `https://<model-host>`: verifier (AC4) + browser equality (AC5) + P1/P2.
3. Only if P1–P2 are acceptable: set the two `VITE_SPOTER_*` variables to the new host (runbook §9),
   redeploy **preview**, repeat the gate, then production.
4. **Rollback is a two-variable revert** — both hosts serve simultaneously and the objects never moved, so
   no rollback touches R2, the cache rule (which can stay), or the model files.

## 6. Risks and open decisions

| # | Item | Decision needed |
|---|---|---|
| R1 | Zone/domain choice (§3.1) | Yours: which hostname, and whether it needs a registrar nameserver change |
| R2 | Cache rule configuration (§3.3) | Yours: approve as specified |
| R3 | `Timing-Allow-Origin` transform rule (§3.5) | Yours: measure better vs leave headers untouched |
| R4 | Low-bandwidth behaviour (AC7) | Yours: accept the wait, or change payload/UX strategy |
| R5 | Keep or disable `r2.dev` after cutover | Yours; keeping it preserves the fallback and the same public exposure as today |
| R6 | Cache correctness | Mitigated by re-verifying digests *through* the new host before anyone uses it; a cache that alters bytes would fail AC4 |
| R7 | Cost | Unchanged at $0 storage/egress; caching strictly reduces Class B origin reads (runbook §6) |

## 7. Preserved invariants (nothing in this plan changes these)

The four objects and their digests, as verified on the live `r2.dev` host today:

| Object | Bytes | SHA-256 vs ledger |
|---|---|---|
| `spoter_v2_model.onnx` | 121,801 | MATCH `2f97a595e0e96eea…` |
| `spoter_v2_model.onnx.data` | 187,711,488 | MATCH `b0f2e924105fdac6…` |
| `spoter_pilot.onnx` | 1,711,205 | MATCH `cd1b9f8c418c46c7…` |
| `spoter_pilot.onnx.data` | 187,580,416 | MATCH `18a08aa8b5055ef6…` |

Current app-facing URLs (unchanged until a verified cutover):

```
https://pub-c3d9cf94b0d94a8d96b6b0816d15c41e.r2.dev/spoter_v2_model.onnx
https://pub-c3d9cf94b0d94a8d96b6b0816d15c41e.r2.dev/spoter_pilot.onnx
```

No object will be re-uploaded, moved, overwritten or deleted; the frozen vocabulary, model artifacts,
SPOTER V2 pipeline, preprocessing and production avatar are out of scope for this work.

## 8. Exact actions needed, and who can perform them

| Action | Who | Why not me |
|---|---|---|
| Choose the hostname; confirm the zone exists in bucket account `530150911781c2a542a4785049edc988` (or add it, incl. any registrar nameserver change) | **You** | Creating zones and changing DNS is account/registrar-level and explicitly excluded by your instruction |
| Connect the custom domain to the bucket | **You**, or a scoped API token | The `wrangler` OAuth session on this machine carries `zone (read)` only — **no cache-rule or purge write scope**, and the R2 API token is bucket-scoped Object Read & Write, which the Cloudflare API does not accept for zone settings |
| Create the cache rule (§3.3) and purge when measuring cold | **You**, or a scoped API token | Same permission boundary as above |
| Approve (or decline) the `Timing-Allow-Origin` transform rule (§3.5) | **You** | It changes account configuration |
| Confirm AC1–AC7 thresholds, especially AC7 | **You** | It is a product decision about a 179 MB first load |
| Run P1–P3 measurements and the correctness gates once the domain exists | **Me** | Needs only the hostname; no account access |
| P4 (real cellular device) | **You** or a device I can drive | Requires a phone on mobile data |

If you would rather I drive the dashboard-work via API, create a **zone-scoped token** with
`Zone → Cache Rules (Edit)`, `Zone → Cache Purge (Purge)`, and `Zone → DNS (Edit)` (read-only zone access
is enough for verification), save it to a file outside the repository in the same shape as the R2 token,
and tell me only its path — the values stay out of this chat and out of the repo.

## 9. Sources

Cloudflare — [Public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/) ·
[Enable cache in an R2 bucket](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/) ·
[Default cache behavior](https://developers.cloudflare.com/cache/concepts/default-cache-behavior/) ·
[Cache Rules](https://developers.cloudflare.com/cache/how-to/cache-rules/) ·
[Cache Rules settings](https://developers.cloudflare.com/cache/how-to/cache-rules/settings/) ·
[Origin Cache Control](https://developers.cloudflare.com/cache/concepts/cache-control/) ·
[Edge and Browser Cache TTL](https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/) ·
[Cache responses](https://developers.cloudflare.com/cache/concepts/cache-responses/) ·
[Range requests](https://developers.cloudflare.com/cache/reference/range-requests/) ·
[Content compression](https://developers.cloudflare.com/speed/optimization/content/compression/) ·
[Purge by single file](https://developers.cloudflare.com/cache/how-to/purge-cache/purge-by-single-file/) ·
[R2 CORS](https://developers.cloudflare.com/r2/buckets/cors/).

Throttling — [Lighthouse throttling](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md) ·
[Chrome DevTools network reference](https://developer.chrome.com/docs/devtools/network/reference) ·
[WebPageTest connectivity profiles](https://github.com/WPO-Foundation/webpagetest/blob/master/www/settings/connectivity.ini.sample) ·
[`tc-netem`](https://man7.org/linux/man-pages/man8/tc-netem.8.html) ·
[Ookla US H1 2025](https://www.ookla.com/research/reports/united-states-speedtest-connectivity-report-h1-2025) ·
[MDN `PerformanceResourceTiming.transferSize`](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceResourceTiming/transferSize).
