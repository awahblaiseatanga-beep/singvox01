import { describe, it, expect, vi } from 'vitest';
import type { SupabaseClient, User } from '@supabase/supabase-js';
import {
  SUPABASE_KEY_VAR,
  SUPABASE_URL_VAR,
  UNSUPPORTED_KEY_MESSAGE,
  WAITLIST_UNAVAILABLE_MESSAGE,
  readSupabaseConfig,
} from '../lib/supabaseClient';
import {
  DEFAULT_INTEREST,
  MESSAGES,
  WAITLIST_DRAFT_STORAGE_KEY,
  clearWaitlistDraft,
  draftFromStoredAndUser,
  emptyWaitlistDraft,
  friendlyAuthError,
  friendlyWaitlistError,
  isValidEmail,
  loadOwnWaitlistSignup,
  loadWaitlistDraft,
  normalizeEmail,
  optionalText,
  readAuthCallbackError,
  resolveInterest,
  requestWaitlistMagicLink,
  saveWaitlistDraft,
  submitWaitlistSignup,
  waitlistMetadataFromDraft,
  waitlistRedirectUrl,
  type WaitlistDraft,
  type WaitlistSignup,
} from '../lib/waitlist';

/**
 * These tests exercise the SignVox waiting-list logic with a MOCKED Supabase
 * client. They prove configuration validation, request/response handling,
 * duplicate handling and permission-error mapping. They do NOT prove that the
 * live Supabase project accepts anything — that needs the real end-to-end run
 * described in docs/SUPABASE_WAITLIST_SETUP.md §5.
 */

const VALID_ENV = {
  [SUPABASE_URL_VAR]: 'https://aelfubrwzvwqurytobga.supabase.co',
  [SUPABASE_KEY_VAR]: 'sb_publishable_test_key_value',
};

const JWT_FOR_ROLE = (role: string) =>
  [
    Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url'),
    Buffer.from(JSON.stringify({ role, iss: 'supabase' })).toString('base64url'),
    'signature',
  ].join('.');

const draft = (overrides: Partial<WaitlistDraft> = {}): WaitlistDraft => ({
  ...emptyWaitlistDraft(),
  fullName: 'Amina Test',
  email: 'Amina@Example.org',
  phone: '+237 600 000 000',
  organization: 'Example Association',
  interest: 'Researcher',
  message: 'We would like to collaborate.',
  ...overrides,
});

interface FakeOptions {
  signInOtp?: (input: unknown) => { data?: unknown; error?: unknown };
  insertResult?: { data: unknown; error: unknown };
  selectResult?: { data: unknown; error: unknown };
}

/** Minimal chainable stand-in for the supabase-js query builder. */
function fakeClient(options: FakeOptions = {}) {
  const calls = {
    signInOtp: [] as any[],
    tables: [] as string[],
    inserts: [] as any[],
    selects: [] as string[],
    filters: [] as [string, any][],
  };

  const client = {
    auth: {
      signInWithOtp: vi.fn(async (input: any) => {
        calls.signInOtp.push(input);
        return options.signInOtp ? options.signInOtp(input) : { data: { user: null }, error: null };
      }),
    },
    from(table: string) {
      calls.tables.push(table);
      let mode: 'select' | 'insert' = 'select';
      const builder: any = {
        insert(row: any) {
          mode = 'insert';
          calls.inserts.push(row);
          return builder;
        },
        select(columns: string) {
          calls.selects.push(columns);
          return builder;
        },
        eq(column: string, value: any) {
          calls.filters.push([column, value]);
          return builder;
        },
        async maybeSingle() {
          return (mode === 'insert' ? options.insertResult : options.selectResult) ?? { data: null, error: null };
        },
      };
      return builder;
    },
  };

  return { client: client as unknown as SupabaseClient, calls };
}

const SESSION_USER = { id: 'user-0001', email: 'Amina@Example.org', user_metadata: {} } as unknown as User;

const STORED_ROW: WaitlistSignup = {
  id: 'row-1',
  user_id: 'user-0001',
  full_name: 'Amina Test',
  email: 'amina@example.org',
  phone: null,
  interest: 'Researcher',
  message: null,
  created_at: '2026-10-16T00:00:00.000Z',
};

describe('Supabase configuration validation', () => {
  it('reports missing variables by name and keeps the app usable', () => {
    const result = readSupabaseConfig({});
    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.reason).toBe('missing');
    expect([...result.missing]).toEqual([SUPABASE_URL_VAR, SUPABASE_KEY_VAR]);
    expect(result.message).toBe(WAITLIST_UNAVAILABLE_MESSAGE);
    // Never leaks a key value, because there is nothing to leak.
    expect(result.message).not.toMatch(/sb_/);
  });

  it('accepts a publishable key and normalises the project origin', () => {
    const result = readSupabaseConfig(VALID_ENV);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.config.url).toBe('https://aelfubrwzvwqurytobga.supabase.co');
    expect(result.config.warnings).toEqual([]);
  });

  it('strips a copied REST endpoint suffix and says so', () => {
    const result = readSupabaseConfig({
      ...VALID_ENV,
      [SUPABASE_URL_VAR]: 'https://aelfubrwzvwqurytobga.supabase.co/rest/v1/',
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.config.url).toBe('https://aelfubrwzvwqurytobga.supabase.co');
    expect(result.config.warnings.join(' ')).toContain('rest/v1');
  });

  it('refuses a secret key rather than shipping it to the browser', () => {
    const result = readSupabaseConfig({ ...VALID_ENV, [SUPABASE_KEY_VAR]: 'sb_secret_do_not_ship' });
    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.reason).toBe('unsupported-key');
    expect(result.message).toBe(UNSUPPORTED_KEY_MESSAGE);
    expect(result.message).not.toContain('do_not_ship');
  });

  it('refuses a service_role JWT', () => {
    const result = readSupabaseConfig({ ...VALID_ENV, [SUPABASE_KEY_VAR]: JWT_FOR_ROLE('service_role') });
    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.reason).toBe('unsupported-key');
  });

  it('rejects a malformed or insecure project URL', () => {
    expect(readSupabaseConfig({ ...VALID_ENV, [SUPABASE_URL_VAR]: 'not-a-url' }).ok).toBe(false);
    const insecure = readSupabaseConfig({ ...VALID_ENV, [SUPABASE_URL_VAR]: 'http://example.com' });
    expect(insecure.ok).toBe(false);
    if (insecure.ok) return;
    expect(insecure.reason).toBe('malformed');
  });

  it('allows http on loopback for local development', () => {
    const local = readSupabaseConfig({ ...VALID_ENV, [SUPABASE_URL_VAR]: 'http://localhost:54321' });
    expect(local.ok).toBe(true);
  });
});

describe('email handling', () => {
  it('normalises case and whitespace', () => {
    expect(normalizeEmail('  Amina@Example.ORG ')).toBe('amina@example.org');
  });

  it('accepts real-looking addresses and rejects malformed ones', () => {
    expect(isValidEmail('amina@example.org')).toBe(true);
    expect(isValidEmail('amina@example')).toBe(false);
    expect(isValidEmail('amina example.org')).toBe(false);
    expect(isValidEmail('@example.org')).toBe(false);
  });

  it('turns blank optional input into null instead of an empty string', () => {
    expect(optionalText('   ')).toBeNull();
    expect(optionalText(' +237 600 ')).toBe('+237 600');
  });
});

describe('magic-link callback handling', () => {
  it('ignores a successful callback fragment', () => {
    expect(readAuthCallbackError({ hash: '#access_token=abc&type=magiclink&expires_in=3600', search: '' })).toBeNull();
  });

  it('explains an expired link without echoing the raw description', () => {
    const result = readAuthCallbackError({
      hash: '#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+<script>',
      search: '',
    });
    expect(result?.code).toBe('otp_expired');
    expect(result?.message).toMatch(/expired or was already used/i);
    expect(result?.message).not.toContain('<script>');
  });

  it('handles the same parameters arriving as a query string', () => {
    const result = readAuthCallbackError({ hash: '', search: '?error_code=otp_expired' });
    expect(result?.code).toBe('otp_expired');
  });

  it('falls back to a generic explanation for an unknown code', () => {
    const result = readAuthCallbackError({ hash: '#error_code=weird_failure', search: '' });
    expect(result?.code).toBe('weird_failure');
    expect(result?.message).toMatch(/could not be completed/i);
  });
});

describe('requesting a magic link', () => {
  it('refuses to send without a name, without calling Supabase', async () => {
    const { client, calls } = fakeClient();
    const result = await requestWaitlistMagicLink(client, draft({ fullName: '   ' }), 'https://example.test/');
    expect(result.ok).toBe(false);
    expect(result.field).toBe('fullName');
    expect(calls.signInOtp).toHaveLength(0);
  });

  it('refuses to send to an invalid address, without calling Supabase', async () => {
    const { client, calls } = fakeClient();
    const result = await requestWaitlistMagicLink(client, draft({ email: 'nope' }), 'https://example.test/');
    expect(result.ok).toBe(false);
    expect(result.field).toBe('email');
    expect(calls.signInOtp).toHaveLength(0);
  });

  it('sends to the normalised address with the redirect and metadata, but not the message', async () => {
    const { client, calls } = fakeClient();
    const result = await requestWaitlistMagicLink(client, draft(), 'https://example.test/');
    expect(result.ok).toBe(true);
    expect(result.email).toBe('amina@example.org');
    expect(result.message).toBe(MESSAGES.linkSent);

    const input = calls.signInOtp[0];
    expect(input.email).toBe('amina@example.org');
    expect(input.options.emailRedirectTo).toBe('https://example.test/');
    expect(input.options.shouldCreateUser).toBe(true);
    expect(input.options.data).toMatchObject({
      full_name: 'Amina Test',
      phone: '+237 600 000 000',
      interest: 'Researcher',
      source: 'signvox-waitlist',
    });
    // The free-text enquiry is never copied into the auth record.
    expect(JSON.stringify(input.options.data)).not.toContain('collaborate');
    expect(input.options.data.training_use_permission).toBe('never-granted-by-waitlist-signup');
  });

  it('turns a rate limit into advice the visitor can act on', async () => {
    const { client } = fakeClient({
      signInOtp: () => ({ error: { code: 'over_email_send_rate_limit', status: 429, message: 'email rate limit exceeded' } }),
    });
    const result = await requestWaitlistMagicLink(client, draft(), 'https://example.test/');
    expect(result.ok).toBe(false);
    expect(result.message).toBe(MESSAGES.rateLimited);
  });

  it('maps auth errors without leaking internals', () => {
    expect(friendlyAuthError({ code: 'email_address_invalid' })).toBe(MESSAGES.invalidEmail);
    expect(friendlyAuthError({ code: 'email_address_not_authorized', message: 'Email address not authorized' })).toMatch(/different email/i);
    expect(friendlyAuthError({ message: 'Failed to fetch' })).toMatch(/could not reach/i);
    expect(friendlyAuthError({ message: 'unexpected_gibberish_xyz' })).toBe(MESSAGES.genericFailure);
    expect(friendlyAuthError(null)).toBe(MESSAGES.genericFailure);
  });
});

describe('reading the visitor’s own record', () => {
  it('filters by the signed-in user id', async () => {
    const { client, calls } = fakeClient({ selectResult: { data: STORED_ROW, error: null } });
    const { signup, error } = await loadOwnWaitlistSignup(client, 'user-0001');
    expect(error).toBeNull();
    expect(signup?.id).toBe('row-1');
    expect(calls.tables).toEqual(['waitlist_signups']);
    expect(calls.filters).toEqual([['user_id', 'user-0001']]);
  });

  it('returns null when the visitor has no row yet', async () => {
    const { client } = fakeClient({ selectResult: { data: null, error: null } });
    const { signup, error } = await loadOwnWaitlistSignup(client, 'user-0002');
    expect(signup).toBeNull();
    expect(error).toBeNull();
  });
});

describe('submitting the waiting-list entry', () => {
  it('writes only the visitor’s own verified row', async () => {
    const { client, calls } = fakeClient({ insertResult: { data: STORED_ROW, error: null } });
    const result = await submitWaitlistSignup(client, SESSION_USER, draft());
    expect(result.status).toBe('created');
    expect(result.signup?.id).toBe('row-1');
    expect(calls.tables).toEqual(['waitlist_signups']);
    expect(calls.inserts[0]).toEqual({
      user_id: 'user-0001',
      full_name: 'Amina Test',
      email: 'amina@example.org',
      phone: '+237 600 000 000',
      interest: 'Researcher',
      message: 'We would like to collaborate.',
    });
  });

  it('stores nulls rather than blanks for unused optional fields', async () => {
    const { client, calls } = fakeClient({ insertResult: { data: STORED_ROW, error: null } });
    await submitWaitlistSignup(client, SESSION_USER, draft({ phone: '  ', message: '' }));
    expect(calls.inserts[0].phone).toBeNull();
    expect(calls.inserts[0].message).toBeNull();
  });

  it('refuses to submit without a name', async () => {
    const { client, calls } = fakeClient();
    const result = await submitWaitlistSignup(client, SESSION_USER, draft({ fullName: '' }));
    expect(result.status).toBe('error');
    expect(result.message).toBe(MESSAGES.missingName);
    expect(calls.inserts).toHaveLength(0);
  });

  it('reports a repeat submission as already on the list instead of duplicating it', async () => {
    const { client, calls } = fakeClient({
      insertResult: { data: null, error: { code: '23505', message: 'duplicate key value violates unique constraint' } },
      selectResult: { data: STORED_ROW, error: null },
    });
    const result = await submitWaitlistSignup(client, SESSION_USER, draft());
    expect(result.status).toBe('already-submitted');
    expect(result.message).toBe(MESSAGES.alreadySubmitted);
    expect(result.signup?.id).toBe('row-1');
    expect(calls.inserts).toHaveLength(1);
  });

  it('tells the visitor the server is not ready when the migration is missing', async () => {
    const { client } = fakeClient({
      insertResult: {
        data: null,
        error: { code: 'PGRST205', message: "Could not find the table 'public.waitlist_signups' in the schema cache" },
      },
    });
    const result = await submitWaitlistSignup(client, SESSION_USER, draft());
    expect(result.status).toBe('error');
    expect(result.message).toBe(MESSAGES.serverNotReady);
  });

  it('reports a refused write as a session problem', async () => {
    const { client } = fakeClient({
      insertResult: { data: null, error: { code: '42501', message: 'new row violates row-level security policy for table "waitlist_signups"' } },
    });
    const result = await submitWaitlistSignup(client, SESSION_USER, draft());
    expect(result.status).toBe('error');
    expect(result.message).toBe(MESSAGES.notAllowed);
  });

  it('maps permission and availability errors consistently', () => {
    expect(friendlyWaitlistError({ code: '42P01' })).toBe(MESSAGES.serverNotReady);
    expect(friendlyWaitlistError({ code: '42501' })).toBe(MESSAGES.notAllowed);
    expect(friendlyWaitlistError({ message: 'JWT expired' })).toBe(MESSAGES.notAllowed);
    expect(friendlyWaitlistError({ code: '23514' })).toMatch(/could not be accepted/i);
    expect(friendlyWaitlistError({ message: 'anything else' })).toBe(MESSAGES.genericFailure);
  });
});

describe('draft persistence and reconstruction', () => {
  const memoryStorage = () => {
    const map = new Map<string, string>();
    return {
      map,
      storage: {
        getItem: (key: string) => map.get(key) ?? null,
        setItem: (key: string, value: string) => void map.set(key, value),
        removeItem: (key: string) => void map.delete(key),
      },
    };
  };

  it('round-trips the draft in this tab only', () => {
    const { map, storage } = memoryStorage();
    saveWaitlistDraft(storage, draft());
    expect(map.has(WAITLIST_DRAFT_STORAGE_KEY)).toBe(true);
    expect(loadWaitlistDraft(storage)?.fullName).toBe('Amina Test');
    clearWaitlistDraft(storage);
    expect(loadWaitlistDraft(storage)).toBeNull();
  });

  it('survives unusable storage without throwing', () => {
    const throwing = { getItem: () => { throw new Error('blocked'); }, setItem: () => { throw new Error('blocked'); }, removeItem: () => { throw new Error('blocked'); } };
    expect(() => saveWaitlistDraft(throwing, draft())).not.toThrow();
    expect(loadWaitlistDraft(throwing)).toBeNull();
    expect(() => clearWaitlistDraft(throwing)).not.toThrow();
  });

  it('prefers this tab’s draft and falls back to verified metadata', () => {
    const fromMeta = draftFromStoredAndUser(null, {
      id: 'user-0001',
      email: 'amina@example.org',
      user_metadata: { full_name: 'From Metadata', phone: '+237 600 111 222', interest: 'Sponsor or investor' },
    } as unknown as User);
    expect(fromMeta.fullName).toBe('From Metadata');
    expect(fromMeta.email).toBe('amina@example.org');
    expect(fromMeta.interest).toBe('Sponsor or investor');

    const merged = draftFromStoredAndUser(draft({ fullName: 'Typed Here', message: 'my enquiry' }), {
      id: 'user-0001',
      email: 'amina@example.org',
      user_metadata: { full_name: 'From Metadata' },
    } as unknown as User);
    expect(merged.fullName).toBe('Typed Here');
    expect(merged.message).toBe('my enquiry');
    expect(merged.phone).toBe('+237 600 000 000');
  });

  it('does not let the untouched interest default mask a known choice', () => {
    // The select starts on the first option, which must not override what the
    // verified metadata says the visitor chose before confirming.
    expect(resolveInterest([DEFAULT_INTEREST, 'Researcher'])).toBe('Researcher');
    expect(resolveInterest(['Sponsor or investor', 'Researcher'])).toBe('Sponsor or investor');
    expect(resolveInterest([DEFAULT_INTEREST, ''])).toBe(DEFAULT_INTEREST);
    expect(resolveInterest([])).toBe(DEFAULT_INTEREST);

    const rebuilt = draftFromStoredAndUser(draft({ interest: DEFAULT_INTEREST }), {
      id: 'user-0001',
      email: 'amina@example.org',
      user_metadata: { interest: 'Researcher' },
    } as unknown as User);
    expect(rebuilt.interest).toBe('Researcher');
  });

  it('never puts the free-text message in the auth metadata', () => {
    const metadata = waitlistMetadataFromDraft(draft());
    expect(Object.keys(metadata).sort()).toEqual([
      'full_name',
      'interest',
      'organization',
      'phone',
      'source',
      'training_use_permission',
    ]);
  });
});

describe('magic-link redirect target', () => {
  it('uses the app origin without a hash route', () => {
    expect(waitlistRedirectUrl({ hash: '', search: '', origin: 'http://localhost:5173', pathname: '/' })).toBe(
      'http://localhost:5173/',
    );
    expect(
      waitlistRedirectUrl({ hash: '#join', search: '', origin: 'https://signvox.example', pathname: '/' }),
    ).toBe('https://signvox.example/');
  });
});
