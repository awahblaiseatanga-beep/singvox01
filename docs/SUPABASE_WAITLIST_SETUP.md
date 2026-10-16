# SignVox — Supabase waiting list: setup, verification and owner checklist

Audience: the SignVox project owner. Everything in this document is either
already done in the code or an action that only the owner can perform in the
Supabase Dashboard. Nothing here requires pasting a secret into a chat, a file
in the repository, or the browser bundle.

Project ref: `aelfubrwzvwqurytobga` · Project URL: `https://aelfubrwzvwqurytobga.supabase.co`

---

## 1. What the integration does

1. A visitor opens **Join** (`#join`) and fills in name, email, optional phone,
   organization, interest and an optional message.
2. `requestWaitlistMagicLink` calls Supabase Auth `signInWithOtp`. Name, phone,
   organization and interest are attached as Supabase **user metadata** so they
   survive the redirect (including when the visitor opens the mail on another
   device). The free-text message is **not** copied into the auth record; it is
   kept in this tab's `sessionStorage` and is only written to the waiting list
   after verification.
3. Supabase emails a magic link. The page shows *check your inbox*, with resend,
   "use a different email", expired-link and failure states.
4. The visitor opens the link. Supabase verifies the address, the app regains a
   session on the Join page (the auth fragment resolves back to `#join`) and the
   **verified** details are shown for confirmation.
5. Only then is one row written to `public.waitlist_signups`, keyed to
   `auth.uid()`, under Row Level Security. A repeat submission is reported as
   "already on the list" instead of creating a duplicate.
6. There is no account dashboard, no new route and no change to the camera,
   recognition, avatar or diagnostics screens. The session exists only to make
   the waiting-list entry verifiable and self-readable.

If the two Vite variables are absent or the key is unsafe, the whole feature
switches off with a friendly message; every other page keeps working, and if
`VITE_CONTACT_EMAIL` is set the original "prepare the email yourself" flow takes
over.

---

## 2. Environment variables (names and placeholders only)

`web/.env.local` (Git-ignored — verified with `git check-ignore`):

```
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<publishable key>
VITE_CONTACT_EMAIL=<team inbox, optional fallback>
```

* Only these two Supabase values may ever reach the browser. They are public by
  design and are protected by Row Level Security.
* Never put a `service_role` key, a `sb_secret_…` key, the database password, or
  a Supabase personal access token in `web/`, in `.env.example`, or in the app.
  The client refuses to start if it detects one (`sb_secret_` prefix or a JWT
  whose `role` is `service_role`) and disables the waiting list instead.
* `.env.example` carries the same names with empty placeholders. Real values are
  never committed: `.gitignore` ignores `.env` and `.env.*`, with an explicit
  `!.env.example`.
* On Vercel, set the same two variables in Project → Settings → Environment
  Variables for Production/Preview, then redeploy (Vite inlines them at build
  time).

The owner-supplied URL is used verbatim by the client; if a REST endpoint such as
`…/rest/v1/` is pasted, the client strips that suffix and notes it as a warning.

---

## 3. Database: apply the migration (owner action, not yet applied)

Files:

* `supabase/migrations/20261016120000_create_waitlist_signups.sql` — create-only.
* `supabase/tests/waitlist_signups_rls_test.sql` — repeatable permission test.

The migration is **create-only**: it aborts before doing anything if
`public.waitlist_signups` already exists, and it contains no DROP, TRUNCATE,
ALTER of existing objects, or reset. On 2026-10-16 the live project reported
`PostgREST 404 PGRST205 — Could not find the table 'public.waitlist_signups' in
the schema cache`, so the table does not exist and the migration cannot
overwrite anything.

**How to apply it (choose one):**

1. **SQL Editor (recommended, no CLI needed).** Open the file, read it, then
   paste the whole thing into Dashboard → SQL Editor and run it once. The final
   three `select` statements are verification queries; expect `rls_enabled =
   true`, two policies (`waitlist_signups_insert_own`, `waitlist_signups_select_own`)
   and only `authenticated` in the grants list.
2. **Supabase CLI, if you install and link it.** `supabase link --project-ref
   aelfubrwzvwqurytobga` (browser login or your own local token — never paste a
   token into a chat), `supabase migration list` to compare history, review the
   SQL, then apply as a normal migration. Do **not** run `supabase db reset`, and
   do not `db push` without reading the plan first.

After applying, if the app says the waiting list is "not set up on the server
yet", refresh the API schema cache once in the SQL Editor:

```sql
notify pgrst, 'reload schema';
```

Then run the test file the same way:

```
supabase/tests/waitlist_signups_rls_test.sql
```

It runs inside a transaction that ends in `ROLLBACK`, so it leaves nothing
behind, and it prints a NOTICE per check plus a final
`ALL WAITLIST RLS CHECKS PASSED`. Layer 2 creates two scratch auth users; if your
project does not permit that from the SQL Editor, it says so explicitly
(`Layer 2 SKIPPED …`) rather than pretending to pass, and Layer 1's structural
assertions still run.

---

## 4. Dashboard checklist (owner actions)

| # | Action | Where | Why it matters |
|---|--------|-------|----------------|
| 1 | Confirm the **Email** provider is enabled | Authentication → Providers | The magic link is sent through it. As of 2026-10-16 the live public auth settings already report `email: true`. |
| 2 | Set **Site URL** and add **Redirect URLs** for local and production | Authentication → URL Configuration | Magic links can only redirect to an allowlisted URL. Add `http://localhost:5173/` (or your dev port) while developing, and the production origin once the domain is known. Add the **origin + path without `#`**, e.g. `https://signvox.example/`. |
| 3 | Review **magic link / OTP expiry** and the email confirmation setting | Authentication → Emails / Auth settings | Expiry is what produces the "link has expired" state the page already handles. `mailer_autoconfirm` is currently `false`, which is what a magic-link flow needs. |
| 4 | Check the built-in email sending limits, and enable **custom SMTP** before a public launch | Authentication → Emails / Settings → Auth SMTP | The built-in sender is rate-limited and meant for development; a launch needs your own SMTP (the app surfaces rate-limit errors as "wait a few minutes"). |
| 5 | Confirm the **publishable key** in use | Project Settings → API keys | This is the only key the browser needs. If it is ever rotated, update `web/.env.local` and the Vercel variables. |
| 6 | Apply the migration, then verify RLS and grants | SQL Editor | See §3. |
| 7 | Optional: add the production origin to Vercel env vars and redeploy | Vercel → Settings → Environment Variables | The variables are inlined at build time. |

Do **not** enable other auth providers, disable email confirmations, or change
unrelated account settings as part of this work.

---

## 5. What is verified, and what only the owner can verify

Verified locally (2026-10-16):

* `npm run build`, `npx tsc -b` and `npx vitest run` from `web/`.
* Unit tests for configuration validation, magic-link request, duplicate
  handling and error mapping (`web/src/tests/waitlistFlow.test.ts`) use a mocked
  Supabase client. They prove the app's logic, **not** that Supabase is reachable.
* Read-only probes against the live project: the publishable key authenticates,
  the email provider is enabled, and `public.waitlist_signups` does not exist.

Requires the owner (cannot be verified from this machine):

* Applying the migration and running the RLS test.
* Real end-to-end email delivery: request a link from a real inbox, confirm it
  arrives, open it, land back on the Join page and see the confirmation. Until
  that is done, treat "email delivery works" as **unverified**.
* Site URL / redirect allowlist values for the production domain.

---

## 6. Troubleshooting

| Symptom on the Join page | Meaning | Fix |
|---|---|---|
| "The secure waiting list is not connected on this build yet" | `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` missing from `web/.env.local` | Add both and restart the dev server (Vite reads env at start-up). |
| "…a Supabase key that must never be used in a browser…" | A `sb_secret_` key or a `service_role` JWT was configured | Replace it with the publishable key. |
| "The waiting list is not set up on the server yet" | Table missing or PostgREST cache stale | Apply the migration, then `notify pgrst, 'reload schema';`. |
| "That sign-in link has expired or was already used" | Link older than the OTP expiry, or opened twice | Use *Resend the link*. |
| "Too many sign-in emails were requested just now" | Built-in email rate limit | Wait a few minutes; for launch, configure custom SMTP (checklist #4). |
| Link opens the app but the page shows Home | The redirect origin is not allowlisted | Add the exact origin+path to Redirect URLs (checklist #2). |
