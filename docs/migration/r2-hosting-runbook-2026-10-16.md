# SignVox — external ONNX hosting runbook: Cloudflare R2 (2026-10-16)

Status: **bucket created, all four objects uploaded and verified, hosted inference proven bit-identical
to local inference.** The development hostname `https://pub-c3d9cf94b0d94a8d96b6b0816d15c41e.r2.dev`
serves all four objects; §8 records the verified results. The custom domain chosen in D-A is **still
pending** and is the outstanding production item (§9.1). §4 was **corrected on 2026-10-16 after
measurement disproved its original single-request upload instruction**.

Related: `docs/migration/v2-model-hosting-requirements-2026-10-16.md` (requirements),
`docs/migration/onnx-hosting-contract-test-2026-10-16.md` (loopback contract proof: HTTP, CORS,
byte-range, and **bit-identical inference over HTTP**),
`docs/migration/model-delivery-performance-plan-2026-10-16.md` (custom-domain + cache design, and the
cold/warm/mobile performance validation plan).

---

## 1. Provider decision — Cloudflare R2

Evaluated against the two things that dominate this workload (≈375 MB of rarely-changing objects,
read in full by every cold visitor, from arbitrary browser origins):

| Requirement | R2 status | Source |
|---|---|---|
| Storage cost | **$0.015/GB-month** Standard | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) |
| **Egress cost** | **$0** — "no charges for egress bandwidth", any storage class | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) |
| Class A ops (writes/list) | $4.50 per million; free tier **1 M/month** | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) |
| Class B ops (reads; HEAD/GET count here) | $0.36 per million; free tier **10 M/month** | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) |
| Free allowance | **10 GB-month** storage + the op allowances above | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) |
| Max object size | **5 TiB** (single-part 5 GiB) — our 179 MB files are routine | [R2 limits](https://developers.cloudflare.com/r2/platform/limits/) |
| Public read without signed URLs | yes — public bucket + hostname | [Public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/) |
| **Specifying headers the browser must read** | yes, via CORS `ExposeHeaders` (`Content-Range`, `Content-Length`, `Accept-Ranges`, `ETag`) | [Configure CORS](https://developers.cloudflare.com/r2/buckets/cors/) |
| Preflight (`OPTIONS`) | yes — CORS handled by the bucket policy for public/custom-domain access; Cloudflare documents CORS preflight responses as implemented | [Configure CORS](https://developers.cloudflare.com/r2/buckets/cors/) · [Release notes](https://developers.cloudflare.com/r2/platform/release-notes/) |
| Byte ranges / `206` | documented supported (`GetObject` `Range`, ranged requests return 206) | [S3 API compatibility](https://developers.cloudflare.com/r2/api/s3/api/) · [Release notes](https://developers.cloudflare.com/r2/platform/release-notes/) |
| Per-object `Content-Type` / `Cache-Control` | supported as upload metadata (implemented `PutObject` system metadata) | [S3 API compatibility](https://developers.cloudflare.com/r2/api/s3/api/) |
| Upload from this machine | `npx wrangler r2 object put …` (account login, no S3 keys, ≤315 MB/file) or AWS CLI against `https://<account_id>.r2.cloudflarestorage.com` with an R2 API token | [CLI guide](https://developers.cloudflare.com/r2/get-started/cli/) · [Tokens](https://developers.cloudflare.com/r2/api/tokens/) |

Why it wins here: **zero egress** is the only line item that scales with the workload (179.1 MiB per
cold visitor), the objects sit far inside the free storage tier, and the serving origin is independent
of Vercel, so model traffic never touches the Vercel plan.

**Not chosen:** Vercel Blob couples model delivery to the web host and bills egress. S3/GCS/Azure bill
egress (~$0.09/GB ⇒ ~$16 per 1,000 cold visitors at 179 MiB each). Supabase Storage's metered free
egress (~5 GB/month per the earlier plan) would cover only ~28 cold visitors/month.

### 1.1 Interim host in use today: `r2.dev` (development access, not production)

The bucket's **Public Development URL** is enabled and serving all four objects. Cloudflare's documented
status for that access method is:

> "Public access through r2.dev subdomains is rate-limited and should only be used for development
> purposes." — [Public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/)

and, separately, that it **"does not support caching, WAF, or bot management"**
([Enable cache in an R2 bucket](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/)).
The documentation says *rate-limited*, not "bandwidth-throttled" — the cost below is measured, not
quoted.

Measured consequence (§8.3): in a real browser a cold load of the 187.7 MB baseline sidecar took
**357.0 s** (≈526 KB/s) and the 187.6 MB pilot sidecar **297.7 s** (≈630 KB/s) — roughly **six minutes**
before the default model can classify anything. Three consecutive identical `GET`s of the graph object
returned **no `cf-cache-status` and no `Age` header at all**, i.e. no edge cache is involved, exactly as
the "does not support caching" note implies.

So the custom domain in D-A is not cosmetic polish: it is the difference between an edge-cached and an
uncached 375 MB cold visit. Cloudflare documents both access methods as independently usable
("enabling custom domains does not require enabling r2.dev access"), so adding the custom domain keeps
the current URLs working (§9).

## 2. Decisions — ANSWERED by the owner on 2026-10-16

| # | Decision | Your answer | Consequence |
|---|---|---|---|
| **D-A** | Production hostname for the models | **Custom domain on R2** — chosen, **not yet created** | You connect e.g. `models.<yourdomain>` to the bucket; the domain must exist as a zone **in the same Cloudflare account** (a free zone is fine). Until that lands, the bucket is served only by its `r2.dev` development URL (§1.1), which is what the app is built against today. |
| **D-B** | How I get write access | **`wrangler login` on this machine**, extended by an **R2 API token** for the chunked upload | OAuth alone could not move the sidecars: `wrangler r2 object put` cannot complete a 187 MB request on this link, and its callback flow timed out (§4.2, §4.3). Token scope = **Object Read & Write on `signvox-models` only**; it lives at `%USERPROFILE%\.signvox-r2\credentials.env`, outside the repository, and its values were never printed, copied into the repo, or committed. |
| **D-C** | R2 subscription activation | **You activate R2 yourself** | I will not create the subscription or accept paid terms. Expected usage is **$0** (§6); Cloudflare may still ask for a payment method before enabling the usage-billed subscription. |

### 2.1 Setup checklist — status as of 2026-10-16

| # | Step | Status |
|---|---|---|
| 1 | Activate the R2 subscription | **done** (owner) |
| 2 | Create bucket `signvox-models` | **done** (owner; created 2026-10-16T12:42:24Z) |
| 3 | Connect the custom domain `models.<yourdomain>` (D-A) | **pending** — not created; needs a zone in your account (§9.1) |
| 4 | Paste the CORS policy (§7) | **done** — confirmed live on the real host by preflight and exposed headers (§8.1) |
| 5 | Enable the `r2.dev` Public Development URL | **done** (owner) — this is the interim host in §1.1 |
| 6 | Grant write access | **done** — `wrangler login --device` for the small objects, then an R2 API token for the chunked multipart uploads (§4.1) |
| 7 | Upload the four objects | **done** — all four; sidecars via resumable multipart (§4.1) |
| 8 | Verify host contract + hosted inference (§8) | **done** — PASS, 4/4 digests, bit-identical logits |
| 9 | Point `VITE_SPOTER_*` at the custom domain and re-verify | **pending**, only after step 3 (§9.1) |

CLI availability on this machine was verified on 2026-10-16: `npx wrangler@latest --version` → **4.151.1**, with `r2 object put` exposing `--file`, `--content-type`, `--cache-control` and `--remote`, `r2 bucket cors set <bucket> --file <json>`, `login --browser` (default `true`) and `login --device`.

## 3. Exact setup steps (dashboard, ~5 minutes)

1. Cloudflare dashboard → **R2** → *Purchase/Enable R2* (accepts the free tier; add the payment
   method only if you approve it — see D-C).
2. **Create bucket**: name `signvox-models`, location **Automatic**, storage class **Standard**.
3. **Upload** the four objects. Keep all four at the **bucket root**: `inference.ts` derives the
   sidecar URL as `${modelUrl}.data`, so graph and sidecar must share one prefix and the names must be
   exactly `spoter_v2_model.onnx[.data]` and `spoter_pilot.onnx[.data]`. **Use the chunked path in §4
   for the two `.data` files** — one `wrangler r2 object put` does not complete for a 187 MB object on
   a link like this one (§4.2).
4. **Public access**: bucket → **Settings → Public access**. For D-A(a): *Custom Domains → Add* and
   connect `models.<yourdomain>`; for D-A(b): enable the **r2.dev** managed URL (development only).
5. **CORS policy**: bucket → **Settings → CORS Policy → Add** and paste the policy from §7.
   CLI alternative: `npx wrangler r2 bucket cors set signvox-models --file cors.json`, then confirm with
   `npx wrangler r2 bucket cors list signvox-models`. The dashboard accepts the capitalised array in
   §7; wrangler's own file format is documented differently (a `rules` wrapper with lower-case keys),
   so **verify with `cors list` whichever route you use** rather than assuming the file shape.
6. Send me the resulting base URL (e.g. `https://models.yourdomain.com`). I then run Phase 2 (upload if
   you gave me access, otherwise verify what you uploaded) and Phase 3 (verification) and report.

## 4. Upload method — corrected 2026-10-16 (chunked and resumable)

The previous version of this section said a single `npx wrangler r2 object put` per file was
sufficient. **That was wrong for the two 187 MB sidecars**, and this section now records what actually
worked. The two small objects did upload that way, and re-sending one of them through the multipart path
left it byte-identical (its digest still matches the ledger).

### 4.1 What actually worked

1. `npx wrangler login --device` — the browser-callback login is unusable here (§4.3).
2. Small objects via `wrangler r2 object put` (fine up to a few MB), with the explicit `--remote` so a
   stray local R2 dev bucket can never silently receive the objects:

   ```bash
   npx wrangler@latest r2 object put signvox-models/spoter_pilot.onnx \
     --file web/public/spoter_pilot.onnx \
     --content-type application/octet-stream \
     --cache-control "public, max-age=31536000, immutable" \
     --remote --force
   ```

3. The two sidecars via a **resumable S3-multipart upload** using an R2 API token (Object Read & Write,
   scoped to `signvox-models`), with credentials read from `%USERPROFILE%\.signvox-r2\credentials.env`
   — never printed, never copied into the repository:

   ```bash
   node upload_resumable.mjs --file web/public/spoter_v2_model.onnx.data \
     --key spoter_v2_model.onnx.data        # 5 MiB parts; resumes from parts R2 already holds
   node upload_resumable.mjs --file web/public/spoter_pilot.onnx.data \
     --key spoter_pilot.onnx.data
   ```

   Result: **36 parts of 5 MiB per file, zero retries, 254 s and 286 s** (≈790 KB/s sustained), each
   reporting a server-side size exactly equal to the local file. The uploader supports `--dry-run`
   (validates the part plan and reads the first part with no network calls) and `--abort` (discards a
   recorded partial upload). It deliberately lives **outside** the repository, next to the credentials.

Why parts are the fix: R2 retains completed parts server-side, so an interrupted run resumes instead of
restarting, and no single request has to survive the whole 187 MB.

### 4.2 Why the single-request instruction failed (measured, not inferred)

* `wrangler r2 object put --file` on `spoter_v2_model.onnx.data` → `X [ERROR] fetch failed` after ~69 s;
  on the smaller sidecar after ~25 s; `--pipe` failed the same way. The wrangler logs carry no HTTP
  status — just undici `fetch failed`.
* Wrangler's documented ceiling is **315 MB**, so 187 MB was never over a documented limit; the link
  drops long requests instead.
* A 10 MB probe to Cloudflare was **reset after 368 KB** (~20 KB/s), while a 5 MiB upload completed in
  52 s. Single large requests died repeatedly; chunked ones did not.

### 4.3 Two host-boundary traps on this machine (each cost a failed attempt)

* **`wrangler login`'s callback server has a hard 120 s window** and binds IPv6 loopback only
  (`[::1]:8976`). Approving the Cloudflare page later than that yields exactly
  `localhost refused to connect`, because the process has already exited — confirmed in the wrangler log
  (`Timed out waiting for authorization code` at +120 s). **Use `npx wrangler login --device`**: RFC 8628
  device flow, no localhost callback, a 5-minute approval window, same session.
* **Vite dev also binds `[::1]` by default here**, so `http://127.0.0.1:5199` is refused unless it is
  started as `npx vite --host 127.0.0.1 --port 5199 --strictPort`.

### 4.4 S3-compatible alternative

If you prefer the AWS CLI to the Node uploader, `aws s3 cp` switches to multipart above its documented
8 MB default threshold:

```bash
aws s3 cp web/public/spoter_v2_model.onnx.data s3://signvox-models/spoter_v2_model.onnx.data \
  --endpoint-url https://<ACCOUNT_ID>.r2.cloudflarestorage.com \
  --content-type application/octet-stream \
  --cache-control "public, max-age=31536000, immutable"
```

`application/octet-stream` and the immutable `Cache-Control` are set **as object metadata at upload**;
S3-style `response-*-` query overrides on public URLs are not documented for R2, so do not rely on them.
Immutable caching is only correct because these URLs will never be overwritten — if a model is ever
re-exported, upload it under a **new** path. **Do not re-upload or overwrite the current four objects**:
all four are verified and in use (§8, §9).

## 5. Handing me access safely

Status: **this is the route that was used.** The R2 token file exists at the path below, outside the
repository, and was read by the uploader into memory only — never printed, never copied into the repo,
never echoed in a report, never committed.

* Never paste tokens, keys, or passwords into this chat, and never commit them. No credential file
  belongs inside the repository.
* If you choose **D-B**, write exactly this shape to a file outside the repo, e.g.
  `%USERPROFILE%\.signvox-r2\credentials.env`:

  ```
  CLOUDFLARE_ACCOUNT_ID=<account id>
  CLOUDFLARE_R2_ACCESS_KEY_ID=<access key id>
  CLOUDFLARE_R2_SECRET_ACCESS_KEY=<secret>
  R2_BUCKET_NAME=signvox-models
  ```

  Then tell me the path only. I will source it in the shell for the upload commands and never print
  the values, never copy it into the repo, and never echo it in a report.
* If you choose **D-A**, run `npx wrangler login` yourself (it opens a browser OAuth flow against your
  account); I will reuse the stored session for `r2 object put` and nothing else.
* Least privilege: token scope = **Object Read & Write** on `signvox-models` only.

## 6. Cost model (verified pricing, arithmetic on measured sizes)

Measured footprint: 4 objects, **375.3 MB** = 0.367 GiB. Each cold visitor loads the two 79-class
objects = **179.1 MiB**; a HEAD/GET of each object is one **Class B** operation; only uploads are
Class A.

| Scale (unique cold visitors/month) | Storage | Class B reads | Egress | Monthly cost |
|---|---|---|---|---|
| 100 | 0.367 of 10 GB-month free | 200 (0.002% of free tier) | 17.5 GiB | **$0** |
| 1,000 | same | 2,000 (0.02%) | 175 GiB | **$0** |
| 10,000 | same | 20,000 (0.2%) | 1.71 TiB | **$0** |
| 100,000 | same | 200,000 (2%) | 17.1 TiB | **$0** |

Charging only begins beyond the free tier: storage >10 GB-month (would need ~27 copies of this
dataset) or >10 M Class B ops/month (≈5 M cold loads), after which the rate is **$0.36 per million**
Class B ops (**≈$3.60** for an extra 10 M reads) and **$0.015/GB-month** storage. **Egress stays $0 at
any volume.** Cloudflare Cache in front of a custom-domain bucket serves repeat requests without
hitting R2, so real Class B counts are lower than the table. These figures are the provider's
published rates, not a quote or a bill.

## 7. CORS policy (paste as the bucket policy)

Recommended — the objects are public, non-secret model weights, the app already serves them with
`Access-Control-Allow-Origin: *` in `web/vercel.json`, and `*` avoids a CORS change when the Vercel
origin appears:

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["range"],
    "ExposeHeaders": ["Content-Range", "Content-Length", "Accept-Ranges", "ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Tighter variant (if you prefer to name origins) — replace with the deployed origin(s) once known, and
**remember the change needed later**: add the Vercel production domain *and* any custom domain, or
browsers will fail CORS while `curl` still looks fine:

```json
[
  {
    "AllowedOrigins": ["http://127.0.0.1:5199", "https://<project>.vercel.app"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["range"],
    "ExposeHeaders": ["Content-Range", "Content-Length", "Accept-Ranges", "ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Temporary testing origin until the app is deployed: **`http://127.0.0.1:5199`** (the loopback origin
used in the contract test). If the CORS policy is edited after traffic has been served, purge the
bucket hostname's cache so the new headers are applied.

## 8. Verification results — executed 2026-10-16 against the live host

Every number below is a measurement from this machine or from a real browser on it, not a projection.

### 8.1 Object contract — PASS

`node tools/verify_onnx_hosting.mjs --base https://pub-c3d9cf94b0d94a8d96b6b0816d15c41e.r2.dev --origin http://127.0.0.1:5199`
exited **0** with `required checks: PASS` and **zero informational notes**.

| Object | Bytes | Hosted SHA-256 vs ledger | HEAD | Ranged GET |
|---|---|---|---|---|
| `spoter_v2_model.onnx` | 121,801 | MATCH `2f97a595…` | 200 | 206 prefix + suffix |
| `spoter_v2_model.onnx.data` | 187,711,488 | MATCH `b0f2e924…` | 200 | 206 prefix + suffix |
| `spoter_pilot.onnx` | 1,711,205 | MATCH `cd1b9f8c…` | 200 | 206 prefix + suffix |
| `spoter_pilot.onnx.data` | 187,580,416 | MATCH `18a08aa8…` | 200 | 206 prefix + suffix |

All four carry `Content-Type: application/octet-stream`, `Cache-Control: public, max-age=31536000,
immutable`, `Accept-Ranges: bytes` and an exact `Content-Length`; a `GET` sent with an `Origin` returns
`Access-Control-Allow-Origin: *` and exposes `Content-Range, Content-Length, Accept-Ranges, ETag`; the
`OPTIONS` preflight returns **204** with `GET, HEAD`, `allow-headers: range`, `max-age: 3600`. Ranged
reads were correct in both forms (`bytes=0-99` and the suffix `bytes=-32`).

Three host facts that matter downstream: **no `Timing-Allow-Origin`** is ever sent, so browser
cross-origin byte counts read as 0 (§8.3 works around it); **no `cf-cache-status` and no `Age`** header
appears, i.e. the dev URL involves no edge cache (§1.1); and ETags are upload-shaped rather than content
hashes (`…-36` on both sidecars, `…-1` on the re-uploaded graph, bare on the object still from the
original single PUT) — which is exactly why `docs/migration/local-only-assets-sha256.txt`, not the ETag,
is the integrity source.

### 8.2 Hosted vs local inference — bit-identical

A temporary page on the Vite dev origin imported the **production** `SpoterInferenceSession` and ran the
**same** 60×366 window through both arms in the **same** browser and ORT build — one arm from the public
URL, one from the same-origin file in `web/public`:

| Model | Local file | Hosted URL | Comparison |
|---|---|---|---|
| 79-class baseline | 79 logits, **HELLO 0.9976679086685181**, load 3,583.7 ms, infer 399.1 ms | 79 logits, **HELLO 0.9976679086685181**, infer 366.4 ms | **max abs diff 0**, 0/79 logits differ, same top-1 *and* confidence |
| 3-class pilot | 3 logits, **YES 0.999758780002594**, load 2,774.1 ms, infer 411.8 ms | 3 logits, **YES 0.999758780002594**, infer 426.5 ms | **max abs diff 0**, 0/3 logits differ |

Both sessions initialised via `wasm`; the network log shows the browser fetching the graph **and** its
derived `${modelUrl}.data` sidecar cross-origin (both 200); the console was clean. ORT fetched each file
**whole** — no ranged request was issued — so `206` support is available but not exercised by inference
today.

### 8.3 Cold-load cost of the interim host (drives §9.1)

| Transfer | Same-origin local dev server | Hosted `r2.dev` |
|---|---|---|
| `spoter_v2_model.onnx.data` (187.7 MB) | 1,614.8 ms | **357,015.6 ms** |
| `spoter_pilot.onnx.data` (187.6 MB) | 1,639.1 ms | **297,702.3 ms** |
| `spoter_v2_model.onnx` (122 KB) | 7.6 ms | 1,065.5 ms |
| `spoter_pilot.onnx` (1.7 MB) | 34.5 ms | 2,380.6 ms |

Effective hosted throughput ≈ **526 KB/s** (≈4.2 Mbps) and **630 KB/s** (≈5.0 Mbps). The cross-origin
size fields are 0 because of the missing `Timing-Allow-Origin`, so the trustworthy figures are the
browser-reported durations in the table.

### 8.4 Not measured here

A warm/cache-hit repeat load (there is no cache on `r2.dev` to warm), any custom-domain behaviour, other
browsers, the deployed Vercel site, live-camera recognition, and HTTP/2 vs HTTP/3 (the local `curl`
build lacks HTTP/2 support). The mobile-network matrix is specified but not yet executed — see
`docs/migration/model-delivery-performance-plan-2026-10-16.md`.

## 9. Vercel environment variables you will enter (build-time, Vite-inlined)

Set these in the Vercel project **before** the build (preview *and* production), then **redeploy** after
any change — `import.meta.env.VITE_*` is baked in at build time:

**Current verified values — the interim `r2.dev` host (correct for preview/staging only):**

```
VITE_SPOTER_V2_URL=https://pub-c3d9cf94b0d94a8d96b6b0816d15c41e.r2.dev/spoter_v2_model.onnx
VITE_SPOTER_PILOT_URL=https://pub-c3d9cf94b0d94a8d96b6b0816d15c41e.r2.dev/spoter_pilot.onnx
```

**Production target, once D-A lands:** the same two paths on `https://<model-host>` — change the
hostname only. Keep both objects at the bucket root, because `inference.ts` derives the sidecar as
`${modelUrl}.data`: no trailing slash and no extra path segment unless both objects move together.

* **`VITE_AVATAR_GLB_URL` stays UNSET** — the 47.4 MiB avatar is committed and served same-origin.
* Also required for the launch, from the earlier audit: `VITE_SUPABASE_URL`,
  `VITE_SUPABASE_PUBLISHABLE_KEY`, and `VITE_CONTACT_EMAIL`.
* Values are inlined into the public bundle; these are public URLs by design and contain no secrets.
* **Both hosts serve at once.** Cloudflare documents custom domains and `r2.dev` as independent
  ("enabling custom domains does not require enabling r2.dev access"), so switching over means changing
  only these two variables — the four objects are not re-uploaded, moved, or overwritten — and only
  **after** the new host passes `tools/verify_onnx_hosting.mjs` plus the §8.2 equality test.

### 9.1 Still-pending production step: the custom domain

Not started, and it needs your account — it cannot be done from this machine's CLI session. The exact
sequence, the cache rule that is **required** for these objects to be cached at all, and the
accompanying performance validation plan are in
`docs/migration/model-delivery-performance-plan-2026-10-16.md`.

## 10. Boundaries honoured

Bucket created and four objects uploaded through the owner-approved path; no credential ever requested
in chat or committed; no paid terms accepted; **no custom domain, DNS change or cache rule created**; no
Vercel deploy; no Git staging/commit/push; and no change to the frozen vocabulary, model artifacts,
SPOTER V2 pipeline, preprocessing, inference implementation or production avatar. All four model
artifacts still match `docs/migration/local-only-assets-sha256.txt` (`sha256sum -c` → all four `OK`).

**Production delivery is not finished.** Two things stand between the current state and a launch:
(1) the app can only use the throttled, uncached `r2.dev` host until the custom domain in §9.1 exists and
is verified; (2) recognition itself remains unvalidated on a live signer (unchanged from the earlier
audit) — §8.2 proves hosting does not alter inference, not that inference is accurate in the field.
