-- ============================================================================
-- SignVox — waiting list schema
-- Project ref: aelfubrwzvwqurytobga
-- ============================================================================
--
-- WHAT THIS DOES
--   Creates ONE new table, `public.waitlist_signups`, holding the minimum needed
--   to run the waiting list: the verified authenticated user, their name, the
--   verified email address, an optional phone number, the enquiry they chose to
--   send, and when it was created.
--
-- WHAT THIS DELIBERATELY DOES NOT DO
--   * No DROP, TRUNCATE, ALTER of any existing object, and no reset.
--   * No public (anonymous) read policy of any kind: anonymous callers cannot
--     list, read or export waiting-list entries.
--   * No update/delete grants to authenticated callers either — a submitted
--     entry is immutable from the client; corrections are handled by the team.
--   * No consent-for-training flag. Waitlist registration is NOT permission to
--     use anyone's recordings or personal data for AI training, so no such
--     permission is collected or stored here. If the owner later decides to ask
--     for an explicit acknowledgement on the page, add its own column and
--     timestamp in a separate migration.
--
-- SAFETY
--   The first block aborts the whole migration if `public.waitlist_signups`
--   already exists, so this file can never overwrite an existing table. If it
--   aborts, stop and inspect the live schema instead of editing this file.
--
-- HOW TO APPLY (owner only — see docs/SUPABASE_WAITLIST_SETUP.md)
--   Either: review this file, then paste it into Supabase Dashboard → SQL Editor
--   and run it once as the project owner.
--   Or: with the Supabase CLI linked to this project, apply it as a normal
--   migration. Do not run `supabase db push` without reviewing the plan first,
--   and never run `supabase db reset` against this project.
--
-- ============================================================================

-- ── Pre-flight: refuse to touch an existing table ───────────────────────────
do $$
begin
  if to_regclass('public.waitlist_signups') is not null then
    raise exception
      'public.waitlist_signups already exists — migration aborted without changes. Inspect the live schema before applying anything.';
  end if;
end
$$;

-- ── Table ───────────────────────────────────────────────────────────────────
create table public.waitlist_signups (
  id uuid primary key default gen_random_uuid(),

  -- One row per verified visitor. `on delete cascade` removes only that
  -- visitor's own waiting-list row when their auth user is deleted; nothing
  -- else in the project references this table, so no unrelated data can be
  -- destroyed by it.
  user_id uuid not null unique references auth.users (id) on delete cascade,

  full_name text not null
    constraint waitlist_signups_full_name_length
    check (char_length(btrim(full_name)) between 1 and 200),

  -- The address Supabase Auth has verified. Normalised in the generated column
  -- below so duplicates cannot slip through as "Someone@Example.com".
  email text not null
    constraint waitlist_signups_email_shape
    check (position('@' in email) > 1 and char_length(email) <= 320),

  email_normalized text generated always as (lower(btrim(email))) stored,

  phone text
    constraint waitlist_signups_phone_length
    check (phone is null or char_length(btrim(phone)) between 3 and 40),

  -- Which kind of enquiry this is ("Early user", "Researcher", …).
  interest text
    constraint waitlist_signups_interest_length
    check (interest is null or char_length(btrim(interest)) between 1 and 80),

  -- Optional free-text enquiry the visitor typed on the page.
  message text
    constraint waitlist_signups_message_length
    check (message is null or char_length(message) <= 4000),

  created_at timestamptz not null default now()
);

comment on table public.waitlist_signups is
  'SignVox waiting-list entries. One row per email-verified visitor, created only after Supabase Auth has confirmed the address. Waitlist registration is not permission to use personal data or recordings for AI training.';
comment on column public.waitlist_signups.user_id is
  'Verified Supabase Auth user. Row Level Security allows a visitor to read and insert only rows where auth.uid() = user_id.';
comment on column public.waitlist_signups.email_normalized is
  'lower(btrim(email)); unique so a second sign-up with the same address (any letter case) is rejected instead of duplicated.';
comment on column public.waitlist_signups.message is
  'Optional free-text enquiry from the Join page. Never copied into the auth user record.';

-- One entry per verified email address, case- and whitespace-insensitive.
create unique index waitlist_signups_email_normalized_key
  on public.waitlist_signups (email_normalized);

-- ── Row Level Security ──────────────────────────────────────────────────────
alter table public.waitlist_signups enable row level security;

-- Supabase grants ALL on new public tables to anon/authenticated by default.
-- Take every privilege back, then hand out only what the flow needs. `anon`
-- keeps nothing at all, so anonymous visitors cannot list, read or export.
revoke all on table public.waitlist_signups from anon;
revoke all on table public.waitlist_signups from authenticated;
grant select, insert on table public.waitlist_signups to authenticated;

-- Insert: a signed-in visitor may create only their own row. The composite
-- requirements (verified auth.uid(), shape checks above) mean a forged user_id
-- is rejected by the database, not by the client.
create policy waitlist_signups_insert_own
  on public.waitlist_signups
  for insert
  to authenticated
  with check (auth.uid() = user_id);

-- Select: a signed-in visitor may read back only their own row. This is what
-- makes "already on the list" possible without exposing anyone else's entry.
create policy waitlist_signups_select_own
  on public.waitlist_signups
  for select
  to authenticated
  using (auth.uid() = user_id);

-- No INSERT/SELECT policy exists for anon, and no UPDATE or DELETE policy or
-- grant exists for any client role: entries cannot be edited, enumerated,
-- exported or deleted through the public API by anyone but the service role.

-- ── Verification (expected output noted, this selects nothing private) ──────
select relname as table_name, relrowsecurity as rls_enabled
from pg_class
where oid = 'public.waitlist_signups'::regclass;

select polname as policy, polcmd as command, roles.rolname as applies_to
from pg_policy
join pg_roles roles on roles.oid = polroles[1]
where polrelid = 'public.waitlist_signups'::regclass
order by polname;

select grantee, privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name = 'waitlist_signups'
order by grantee, privilege_type;
