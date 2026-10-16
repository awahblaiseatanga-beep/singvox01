import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * Single reusable Supabase browser client for SignVox.
 *
 * Hard rules enforced here:
 *  - Only the project URL and the PUBLISHABLE key are ever read from the
 *    environment. Both are public by design (they ship inside the client
 *    bundle) and are protected by Row Level Security on the server.
 *  - A secret key (`sb_secret_…`), a `service_role` JWT, a database password
 *    or a personal access token must never reach the browser. If one is
 *    configured by mistake the client refuses to start and every Supabase
 *    feature degrades to a friendly message instead of leaking privileges.
 *  - A missing configuration never throws and never breaks unrelated routes:
 *    the app keeps working, only the waiting-list features switch off.
 */

export const SUPABASE_URL_VAR = 'VITE_SUPABASE_URL';
export const SUPABASE_KEY_VAR = 'VITE_SUPABASE_PUBLISHABLE_KEY';

/** Shown wherever a Supabase feature is needed but not configured. */
export const WAITLIST_UNAVAILABLE_MESSAGE =
  'The secure waiting list is not connected on this build yet, so nothing you type here is sent or stored. ' +
  'The demo, camera pipeline and avatar all still work.';

/** Shown when a forbidden key type is configured. Deliberately non-technical. */
export const UNSUPPORTED_KEY_MESSAGE =
  'This build was started with a Supabase key that must never be used in a browser, so the waiting list is disabled. ' +
  'Please configure the project publishable key instead.';

export interface SupabaseConfig {
  /** Normalised project origin, e.g. `https://<ref>.supabase.co`. */
  readonly url: string;
  readonly publishableKey: string;
  /** Non-fatal problems worth surfacing to the owner (never contains key material). */
  readonly warnings: readonly string[];
}

export type SupabaseConfigResult =
  | { readonly ok: true; readonly config: SupabaseConfig }
  | {
      readonly ok: false;
      readonly reason: 'missing' | 'unsupported-key' | 'malformed';
      readonly message: string;
      /** Names of the variables that still need to be set (names only, no values). */
      readonly missing: readonly string[];
    };

const readEnvValue = (env: Record<string, unknown>, name: string): string => {
  const raw = env[name];
  return typeof raw === 'string' ? raw.trim() : '';
};

/** Strips a suffix that belongs to a REST/Auth endpoint rather than the project root. */
export function normalizeSupabaseUrl(raw: string): { url: string; warning?: string } {
  let value = raw.trim().replace(/\/+$/, '');
  const endpoint = /\/(rest|auth|storage|realtime)\/v1$/i.exec(value);
  if (endpoint) {
    value = value.slice(0, endpoint.index);
    return {
      url: value,
      warning: `The project URL had a "${endpoint[1]}/v1" suffix, which was removed. Use the bare project URL (for example https://<project-ref>.supabase.co).`,
    };
  }
  return { url: value };
}

/** Decodes a JWT payload without verifying it — used only to spot a service_role key. */
function readJwtRole(key: string): string | undefined {
  const parts = key.split('.');
  if (parts.length !== 3) return undefined;
  try {
    const padded = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(atob(padded + '='.repeat((4 - (padded.length % 4)) % 4))) as { role?: unknown };
    return typeof payload.role === 'string' ? payload.role : undefined;
  } catch {
    return undefined;
  }
}

/**
 * Validates the two public Supabase variables without touching the network.
 * Never returns or logs the key value itself.
 */
export function readSupabaseConfig(env: Record<string, unknown>): SupabaseConfigResult {
  const rawUrl = readEnvValue(env, SUPABASE_URL_VAR);
  const key = readEnvValue(env, SUPABASE_KEY_VAR);

  const missing = [
    ...(rawUrl ? [] : [SUPABASE_URL_VAR]),
    ...(key ? [] : [SUPABASE_KEY_VAR]),
  ];
  if (missing.length > 0) {
    return { ok: false, reason: 'missing', message: WAITLIST_UNAVAILABLE_MESSAGE, missing };
  }

  if (key.startsWith('sb_secret_')) {
    return { ok: false, reason: 'unsupported-key', message: UNSUPPORTED_KEY_MESSAGE, missing: [] };
  }
  const jwtRole = readJwtRole(key);
  if (jwtRole === 'service_role') {
    return { ok: false, reason: 'unsupported-key', message: UNSUPPORTED_KEY_MESSAGE, missing: [] };
  }

  const { url, warning } = normalizeSupabaseUrl(rawUrl);
  const warnings: string[] = [];
  if (warning) warnings.push(warning);

  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return {
      ok: false,
      reason: 'malformed',
      message: WAITLIST_UNAVAILABLE_MESSAGE,
      missing: [],
    };
  }
  if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') {
    return { ok: false, reason: 'malformed', message: WAITLIST_UNAVAILABLE_MESSAGE, missing: [] };
  }
  if (parsed.protocol === 'http:' && !/^(localhost|127\.0\.0\.1|\[::1\])$/.test(parsed.hostname)) {
    return { ok: false, reason: 'malformed', message: WAITLIST_UNAVAILABLE_MESSAGE, missing: [] };
  }
  if (!key.startsWith('sb_publishable_') && jwtRole && jwtRole !== 'anon') {
    // A legacy key whose role is neither anon nor publishable is not safe here.
    return { ok: false, reason: 'unsupported-key', message: UNSUPPORTED_KEY_MESSAGE, missing: [] };
  }
  if (!key.startsWith('sb_publishable_') && !jwtRole) {
    warnings.push('The Supabase key is neither a publishable key nor a decodable anon key; requests may be rejected.');
  }

  return { ok: true, config: { url: parsed.origin, publishableKey: key, warnings } };
}

export const supabaseConfigResult: SupabaseConfigResult = readSupabaseConfig(
  (import.meta.env ?? {}) as Record<string, unknown>,
);

/** True when the waiting-list features can talk to Supabase. */
export const isSupabaseConfigured = supabaseConfigResult.ok;

/**
 * The shared client, or `null` when configuration is missing/unsafe. Callers
 * must handle `null` with a friendly message rather than throwing at startup.
 */
export const supabase: SupabaseClient | null = supabaseConfigResult.ok
  ? createClient(supabaseConfigResult.config.url, supabaseConfigResult.config.publishableKey, {
      auth: {
        // Magic links arrive as URL fragments (implicit flow) so a visitor who
        // opens the email on another device or browser still completes sign-in.
        flowType: 'implicit',
        detectSessionInUrl: true,
        persistSession: true,
        autoRefreshToken: true,
        // Namespaced so the waiting-list session cannot collide with any other
        // Supabase usage on the same origin.
        storageKey: 'svx-waitlist-auth',
      },
    })
  : null;

export class SupabaseNotConfiguredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SupabaseNotConfiguredError';
  }
}

/** Narrowing helper for call sites that already handled the unconfigured case. */
export function requireSupabaseClient(): SupabaseClient {
  if (!supabase) {
    throw new SupabaseNotConfiguredError(
      isSupabaseConfigured ? UNSUPPORTED_KEY_MESSAGE : WAITLIST_UNAVAILABLE_MESSAGE,
    );
  }
  return supabase;
}
