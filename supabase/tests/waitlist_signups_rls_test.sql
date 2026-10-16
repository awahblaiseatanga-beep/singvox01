-- ============================================================================
-- SignVox — repeatable permission test for public.waitlist_signups
-- ============================================================================
--
-- RUN THIS IN THE SUPABASE SQL EDITOR (Dashboard → SQL Editor), AFTER the
-- migration in supabase/migrations/20261016120000_create_waitlist_signups.sql.
-- It is read-only with respect to your real data: every statement runs inside
-- one transaction that ends with ROLLBACK, including the two scratch auth users
-- it creates. If anything is asserted wrongly the script raises, the
-- transaction aborts, and nothing is left behind.
--
-- Coverage:
--   Layer 1 (structural, always runs)
--     * Row Level Security is enabled on the table.
--     * `anon` holds NO privilege at all on the table.
--     * `authenticated` holds SELECT and INSERT and nothing else.
--     * Exactly two policies exist: INSERT and SELECT, both for authenticated.
--     * No policy exists for anon, and none for UPDATE/DELETE/ALL.
--     * The unique index on the normalised email and the auth.users FK exist.
--   Layer 2 (behavioural, needs the scratch users below)
--     * Anonymous SELECT and INSERT are refused by the database.
--     * A verified visitor can insert their own row and read it back.
--     * A different signed-in visitor sees zero rows.
--     * A signed-in visitor cannot insert a row for somebody else.
--     * Repeating the same sign-up is refused by the unique index.
--
-- SUCCESS looks like: a final NOTICE "ALL WAITLIST RLS CHECKS PASSED".
-- If Layer 2 cannot create its scratch users on this project it says so
-- explicitly (NOTICE ... SKIPPED) instead of pretending to pass.
--
-- Re-run it as often as you like: it changes nothing permanently.
-- ============================================================================

begin;

do $svx_waitlist_rls_test$
declare
  user_a constant uuid := '9a1c0f1e-0000-4000-8000-00000000a001';
  user_b constant uuid := '9a1c0f1e-0000-4000-8000-00000000b002';
  structural_checks integer := 0;
  behavioural_skipped boolean := false;
  visible_rows integer;
  inserted_rows integer;
begin
  -- ── Layer 1: structural guarantees ────────────────────────────────────────
  if to_regclass('public.waitlist_signups') is null then
    raise exception 'public.waitlist_signups does not exist — run the migration first.';
  end if;
  structural_checks := structural_checks + 1;

  if not (select relrowsecurity from pg_class where oid = 'public.waitlist_signups'::regclass) then
    raise exception 'FAIL: Row Level Security is not enabled on public.waitlist_signups.';
  end if;
  structural_checks := structural_checks + 1;

  if has_table_privilege('anon', 'public.waitlist_signups', 'SELECT')
     or has_table_privilege('anon', 'public.waitlist_signups', 'INSERT')
     or has_table_privilege('anon', 'public.waitlist_signups', 'UPDATE')
     or has_table_privilege('anon', 'public.waitlist_signups', 'DELETE') then
    raise exception 'FAIL: role anon holds privileges on public.waitlist_signups; anonymous callers must hold none.';
  end if;
  structural_checks := structural_checks + 1;

  if not has_table_privilege('authenticated', 'public.waitlist_signups', 'SELECT')
     or not has_table_privilege('authenticated', 'public.waitlist_signups', 'INSERT') then
    raise exception 'FAIL: role authenticated is missing SELECT/INSERT on public.waitlist_signups.';
  end if;
  if has_table_privilege('authenticated', 'public.waitlist_signups', 'UPDATE')
     or has_table_privilege('authenticated', 'public.waitlist_signups', 'DELETE') then
    raise exception 'FAIL: role authenticated must not be able to UPDATE or DELETE waiting-list rows.';
  end if;
  structural_checks := structural_checks + 1;

  if (select count(*) from pg_policies
      where schemaname = 'public' and tablename = 'waitlist_signups') <> 2 then
    raise exception 'FAIL: expected exactly 2 policies on public.waitlist_signups, found %.',
      (select count(*) from pg_policies where schemaname = 'public' and tablename = 'waitlist_signups');
  end if;
  structural_checks := structural_checks + 1;

  if exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'waitlist_signups'
      and (cmd <> 'INSERT' and cmd <> 'SELECT')
  ) then
    raise exception 'FAIL: an unexpected UPDATE/DELETE/ALL policy exists on public.waitlist_signups.';
  end if;
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'waitlist_signups'
      and cmd = 'INSERT' and 'authenticated' = any (roles)
      and qual is null and with_check ilike '%auth.uid()%user_id%'
  ) then
    raise exception 'FAIL: the INSERT policy must target authenticated and require auth.uid() = user_id.';
  end if;
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'waitlist_signups'
      and cmd = 'SELECT' and 'authenticated' = any (roles)
      and qual ilike '%auth.uid()%user_id%'
  ) then
    raise exception 'FAIL: the SELECT policy must target authenticated and restrict rows to auth.uid() = user_id.';
  end if;
  if exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'waitlist_signups'
      and ('anon' = any (roles) or 'public' = any (roles))
  ) then
    raise exception 'FAIL: no policy on public.waitlist_signups may target anon/public.';
  end if;
  structural_checks := structural_checks + 1;

  if not exists (
    select 1 from pg_indexes
    where schemaname = 'public' and tablename = 'waitlist_signups'
      and indexname = 'waitlist_signups_email_normalized_key'
  ) then
    raise exception 'FAIL: the unique index on the normalised email is missing.';
  end if;
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.waitlist_signups'::regclass
      and contype = 'f'
      and confrelid = 'auth.users'::regclass
      and confdeltype = 'c'
  ) then
    raise exception 'FAIL: user_id must reference auth.users(id) with ON DELETE CASCADE.';
  end if;
  structural_checks := structural_checks + 1;

  raise notice 'Layer 1 passed: % structural assertions on public.waitlist_signups.', structural_checks;

  -- ── Layer 2: behavioural checks with two scratch users ────────────────────
  begin
    insert into auth.users (
      id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at
    ) values
      (user_a, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated',
       'svx-rls-test-a@example.invalid', '', now(), now(), now()),
      (user_b, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated',
       'svx-rls-test-b@example.invalid', '', now(), now(), now());
  exception when others then
    behavioural_skipped := true;
    raise notice 'Layer 2 SKIPPED: could not create scratch auth users on this project (%). Layer 1 structural results above still apply.', sqlerrm;
  end;

  if not behavioural_skipped then

    -- 1. Anonymous visitors cannot read or write anything.
    execute 'set local role anon';
    perform set_config('request.jwt.claims', '{"role":"anon"}', true);
    begin
      perform count(*) from public.waitlist_signups;
      raise exception 'FAIL: an anonymous caller was allowed to SELECT the waiting list.';
    exception when insufficient_privilege then
      raise notice 'OK: anonymous SELECT refused (insufficient_privilege).';
    end;
    begin
      insert into public.waitlist_signups (user_id, full_name, email)
      values (user_a, 'Anonymous intruder', 'anon@example.invalid');
      raise exception 'FAIL: an anonymous caller was allowed to INSERT into the waiting list.';
    exception when insufficient_privilege then
      raise notice 'OK: anonymous INSERT refused (insufficient_privilege).';
    end;

    -- 2. Visitor A can submit and read back their own entry.
    execute 'set local role authenticated';
    perform set_config('request.jwt.claims', json_build_object('sub', user_a, 'role', 'authenticated')::text, true);
    insert into public.waitlist_signups (user_id, full_name, email, phone, interest, message)
    values (user_a, 'Test A', 'svx-rls-test-a@example.invalid', '+237000000000', 'Early user', 'permission test row')
    returning 1 into inserted_rows;
    raise notice 'OK: visitor A inserted their own row.';

    select count(*) into visible_rows from public.waitlist_signups;
    if visible_rows <> 1 then
      raise exception 'FAIL: visitor A expected to read exactly 1 row, saw %.', visible_rows;
    end if;
    raise notice 'OK: visitor A reads back exactly their own row.';

    -- 3. The same visitor cannot submit twice (unique index, not a silent duplicate).
    begin
      insert into public.waitlist_signups (user_id, full_name, email)
      values (user_a, 'Test A again', 'SVX-RLS-Test-A@example.invalid');
      raise exception 'FAIL: a repeated sign-up created a duplicate row.';
    exception when unique_violation then
      raise notice 'OK: repeated sign-up refused by the unique email index.';
    end;

    -- 4. Visitor B sees nothing and cannot write rows for anybody else.
    perform set_config('request.jwt.claims', json_build_object('sub', user_b, 'role', 'authenticated')::text, true);
    select count(*) into visible_rows from public.waitlist_signups;
    if visible_rows <> 0 then
      raise exception 'FAIL: visitor B could read % row(s) belonging to visitor A.', visible_rows;
    end if;
    raise notice 'OK: visitor B sees zero rows.';

    begin
      insert into public.waitlist_signups (user_id, full_name, email)
      values (user_a, 'Impersonation attempt', 'impersonation@example.invalid');
      raise exception 'FAIL: visitor B was allowed to insert a row for visitor A.';
    exception when insufficient_privilege then
      raise notice 'OK: inserting a row for another user refused by the INSERT policy.';
    end;

    -- 5. No client role can edit or delete an entry.
    begin
      update public.waitlist_signups set full_name = 'tampered';
      raise exception 'FAIL: a signed-in caller was allowed to UPDATE a waiting-list row.';
    exception when insufficient_privilege then
      raise notice 'OK: UPDATE refused (no grant, no policy).';
    end;
    begin
      delete from public.waitlist_signups;
      raise exception 'FAIL: a signed-in caller was allowed to DELETE waiting-list rows.';
    exception when insufficient_privilege then
      raise notice 'OK: DELETE refused (no grant, no policy).';
    end;

    reset role;
  end if;

  raise notice 'ALL WAITLIST RLS CHECKS PASSED (% structural assertions%s).',
    structural_checks,
    case when behavioural_skipped then ', behavioural layer skipped' else ', behavioural layer passed' end;
end
$svx_waitlist_rls_test$;

-- Nothing above is kept: the scratch users, their rows and any attempted change
-- all disappear with this rollback.
rollback;
