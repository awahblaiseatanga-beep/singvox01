import type { SupabaseClient, User } from '@supabase/supabase-js';

/**
 * Waiting-list domain logic: magic-link sign-in, verified signup submission,
 * duplicate handling and friendly, non-technical error mapping.
 *
 * Flow (full owner steps in docs/SUPABASE_WAITLIST_SETUP.md):
 *  1. The visitor enters their details on the Join page.
 *  2. `requestWaitlistMagicLink` emails a Supabase magic link. Name, phone,
 *     interest and organization travel as Supabase user metadata so the details
 *     survive the redirect — including when the email is opened on another
 *     device. The free-text enquiry message is deliberately NOT copied into the
 *     auth record; it is kept in this tab's sessionStorage only.
 *  3. The visitor clicks the link, Supabase verifies the address and the app
 *     regains a session on the Join page.
 *  4. Only now is the row written to `public.waitlist_signups`, under Row Level
 *     Security, keyed to the verified `auth.uid()`.
 *
 * Nothing here ever sends a secret to the browser and nothing here is a
 * permission to use anyone's data for model training.
 */

export const WAITLIST_TABLE = 'waitlist_signups';
export const WAITLIST_DRAFT_STORAGE_KEY = 'svx-waitlist-draft';

/** Interest options — kept identical to the wording already used on the page. */
export const WAITLIST_INTERESTS = [
  'Early user',
  'Deaf community member',
  'Researcher',
  'Technology partner',
  'Sponsor or investor',
] as const;
export type WaitlistInterest = (typeof WAITLIST_INTERESTS)[number];

export interface WaitlistDraft {
  fullName: string;
  email: string;
  /** Optional in the UI; stored only if the visitor provides it. */
  phone: string;
  organization: string;
  interest: string;
  message: string;
}

export const emptyWaitlistDraft = (): WaitlistDraft => ({
  fullName: '',
  email: '',
  phone: '',
  organization: '',
  interest: WAITLIST_INTERESTS[0],
  message: '',
});

/** The shape of a `public.waitlist_signups` row. */
export interface WaitlistSignup {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  phone: string | null;
  interest: string | null;
  message: string | null;
  created_at: string;
}

/** Minimal error surface shared by Auth and PostgREST so callers stay simple. */
export interface SupabaseErrorLike {
  message?: string;
  code?: string | null;
  status?: number | null;
  details?: string | null;
  hint?: string | null;
  name?: string;
}

export interface UrlLike {
  hash: string;
  search: string;
  origin?: string;
  pathname?: string;
}

export interface MagicLinkResult {
  ok: boolean;
  /** Normalised address the link was sent to (only set when `ok`). */
  email?: string;
  /** Which field the visitor should correct, when the failure is input-related. */
  field?: 'fullName' | 'email';
  message: string;
}

export interface SignupResult {
  status: 'created' | 'already-submitted' | 'error';
  signup?: WaitlistSignup;
  message: string;
}

export const MESSAGES = {
  invalidEmail: 'Please enter a valid email address so we can send you a verification link.',
  missingName: 'Please tell us your name.',
  linkSent: 'Check your inbox — we sent you a secure sign-in link.',
  alreadySubmitted: 'You are already on the waiting list — your details are unchanged.',
  created: 'You are on the waiting list.',
  serverNotReady:
    'The waiting list is not set up on the server yet. Nothing was saved — please try again once the team has finished connecting it.',
  notAllowed:
    'Your sign-in session could not be confirmed for this action. Please sign in again with a fresh link.',
  rateLimited:
    'Too many sign-in emails were requested just now. Please wait a few minutes and try again.',
  genericFailure: 'Something went wrong and nothing was saved. Please try again in a moment.',
} as const;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(normalizeEmail(value));
}

/**
 * The interest select always holds a value, so its first option doubles as the
 * "nothing chosen yet" state when the details are rebuilt after verification.
 */
export const DEFAULT_INTEREST: string = WAITLIST_INTERESTS[0];

/** First real choice wins; the untouched default never masks a known value. */
export function resolveInterest(candidates: (string | undefined)[]): string {
  for (const candidate of candidates) {
    const value = (candidate ?? '').trim();
    if (value.length > 0 && value !== DEFAULT_INTEREST) return value;
  }
  return DEFAULT_INTEREST;
}

/** Trims a value for storage, turning blank/whitespace-only input into `null`. */
export function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * Where Supabase should send the visitor after they click the magic link.
 * The app uses hash routes, so the base URL is used verbatim and the auth
 * fragment is handled by `readAuthCallbackError` / the route reader in App.tsx.
 * The owner must allow this exact origin in the Dashboard redirect allowlist.
 */
export function waitlistRedirectUrl(location: UrlLike = window.location): string {
  const origin = location.origin ?? '';
  const pathname = location.pathname ?? '/';
  return `${origin}${pathname}`;
}

/**
 * Reads a Supabase auth callback error out of the URL fragment or query string.
 * Expired or already-used magic links land here as `otp_expired`, and the
 * fragment is left in place by the auth client, so this can be called at any
 * time after load.
 */
export function readAuthCallbackError(
  location: UrlLike = window.location,
): { code: string; message: string } | null {
  const fragment = new URLSearchParams(String(location.hash ?? '').replace(/^#/, ''));
  const query = new URLSearchParams(String(location.search ?? '').replace(/^\?/, ''));
  const take = (name: string): string => fragment.get(name) ?? query.get(name) ?? '';

  const code = take('error_code');
  const error = take('error');
  if (!code && !error) return null;

  const key = (code || error).toLowerCase();
  if (key === 'otp_expired' || key === 'expired') {
    return {
      code: key,
      message: 'That sign-in link has expired or was already used. Request a new one below — it only takes a moment.',
    };
  }
  if (key === 'access_denied' || key === 'unauthorized') {
    return {
      code: key,
      message: 'That sign-in link could not be verified. Request a new one below to continue.',
    };
  }
  // The raw `error_description` comes from the URL and is never rendered: only
  // our own wording plus the short machine code is shown.
  return {
    code: key || 'unknown',
    message: 'That sign-in link could not be completed. Request a new one below to continue.',
  };
}

/** Turns an Auth error into something a visitor can act on. */
export function friendlyAuthError(error: SupabaseErrorLike | null | undefined): string {
  if (!error) return MESSAGES.genericFailure;
  const code = (error.code ?? '').toLowerCase();
  const text = (error.message ?? '').toLowerCase();
  if (code === 'over_email_send_rate_limit' || error.status === 429 || text.includes('rate limit') || text.includes('too many')) {
    return MESSAGES.rateLimited;
  }
  if (code === 'email_address_invalid' || code === 'validation_failed' || text.includes('invalid email')) {
    return MESSAGES.invalidEmail;
  }
  if (code === 'signup_disabled' || text.includes('signups not allowed') || text.includes('signup is disabled')) {
    return 'Sign-ups are currently closed for this project. Please try again later.';
  }
  if (code === 'email_address_not_authorized' || text.includes('not authorized')) {
    return 'We could not deliver the verification link to that address. Please try a different email address.';
  }
  if (text.includes('failed to fetch') || code === 'request_timeout' || error.status === 0) {
    return 'We could not reach the sign-in service. Please check your connection and try again.';
  }
  return MESSAGES.genericFailure;
}

/** Turns a PostgREST/RLS error into something a visitor can act on. */
export function friendlyWaitlistError(error: SupabaseErrorLike | null | undefined): string {
  if (!error) return MESSAGES.genericFailure;
  const code = error.code ?? '';
  const text = `${error.message ?? ''} ${error.details ?? ''}`.toLowerCase();
  if (code === '42P01' || code === 'PGRST205' || text.includes('schema cache') || text.includes('does not exist')) {
    return MESSAGES.serverNotReady;
  }
  if (code === '42501' || code === 'PGRST301' || text.includes('row-level security') || text.includes('permission denied')) {
    return MESSAGES.notAllowed;
  }
  if (code === '23514' || code === '22P02') {
    return 'Some of those details could not be accepted. Please check the name field and try again.';
  }
  if (text.includes('jwt expired') || text.includes('invalid claim')) {
    return MESSAGES.notAllowed;
  }
  return MESSAGES.genericFailure;
}

export function isUniqueViolation(error: SupabaseErrorLike | null | undefined): boolean {
  if (!error) return false;
  return error.code === '23505' || /duplicate key value|already exists/i.test(error.message ?? '');
}

/**
 * Metadata attached to the auth user so the details survive the redirect.
 * Deliberately excludes the free-text enquiry message, and records that
 * waitlist registration is not permission for model training.
 */
export function waitlistMetadataFromDraft(draft: WaitlistDraft): Record<string, string> {
  return {
    full_name: draft.fullName.trim(),
    phone: draft.phone.trim(),
    organization: draft.organization.trim(),
    interest: draft.interest.trim(),
    source: 'signvox-waitlist',
    // Plain-language record of what the visitor was told on the page.
    training_use_permission: 'never-granted-by-waitlist-signup',
  };
}

/** Rebuilds the draft after verification, preferring the tab's own saved draft. */
export function draftFromStoredAndUser(stored: WaitlistDraft | null, user: User | null): WaitlistDraft {
  const base = emptyWaitlistDraft();
  const metadata = (user?.user_metadata ?? {}) as Record<string, unknown>;
  const readMeta = (key: string): string => (typeof metadata[key] === 'string' ? (metadata[key] as string) : '');
  return {
    fullName: stored?.fullName?.trim() || readMeta('full_name'),
    email: stored?.email?.trim() || user?.email || '',
    phone: stored?.phone?.trim() || readMeta('phone'),
    organization: stored?.organization?.trim() || readMeta('organization'),
    interest: resolveInterest([stored?.interest, readMeta('interest')]),
    message: stored?.message ?? '',
  };
}

/** Same-tab draft persistence so the enquiry text survives the magic-link round trip. */
export function saveWaitlistDraft(storage: Pick<Storage, 'setItem'> | null, draft: WaitlistDraft): void {
  try {
    storage?.setItem(WAITLIST_DRAFT_STORAGE_KEY, JSON.stringify(draft));
  } catch {
    /* private mode / quota — the flow still works, only the prefill is lost */
  }
}

export function loadWaitlistDraft(storage: Pick<Storage, 'getItem'> | null): WaitlistDraft | null {
  try {
    const raw = storage?.getItem(WAITLIST_DRAFT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<WaitlistDraft>;
    return { ...emptyWaitlistDraft(), ...parsed };
  } catch {
    return null;
  }
}

export function clearWaitlistDraft(storage: Pick<Storage, 'removeItem'> | null): void {
  try {
    storage?.removeItem(WAITLIST_DRAFT_STORAGE_KEY);
  } catch {
    /* nothing to clean up */
  }
}

/** Emails a magic link. The only thing written to the database is the auth user. */
export async function requestWaitlistMagicLink(
  client: SupabaseClient,
  draft: WaitlistDraft,
  redirectTo: string,
): Promise<MagicLinkResult> {
  if (draft.fullName.trim().length === 0) {
    return { ok: false, field: 'fullName', message: MESSAGES.missingName };
  }
  const email = normalizeEmail(draft.email);
  if (!isValidEmail(email)) {
    return { ok: false, field: 'email', message: MESSAGES.invalidEmail };
  }

  const { error } = await client.auth.signInWithOtp({
    email,
    options: {
      shouldCreateUser: true,
      emailRedirectTo: redirectTo,
      data: waitlistMetadataFromDraft(draft),
    },
  });
  if (error) return { ok: false, message: friendlyAuthError(error) };
  return { ok: true, email, message: MESSAGES.linkSent };
}

/** Reads the signed-in visitor's own row. Anonymous callers get nothing back. */
export async function loadOwnWaitlistSignup(
  client: SupabaseClient,
  userId: string,
): Promise<{ signup: WaitlistSignup | null; error: SupabaseErrorLike | null }> {
  const { data, error } = await client
    .from(WAITLIST_TABLE)
    .select('id,user_id,full_name,email,phone,interest,message,created_at')
    .eq('user_id', userId)
    .maybeSingle<WaitlistSignup>();
  return { signup: (data as WaitlistSignup | null) ?? null, error: (error as SupabaseErrorLike | null) ?? null };
}

/**
 * Writes the verified waitlist row. A repeat submission is not an error: the
 * unique index turns it into "you are already on the list" and the existing row
 * is returned instead.
 */
export async function submitWaitlistSignup(
  client: SupabaseClient,
  user: Pick<User, 'id' | 'email' | 'user_metadata'>,
  draft: WaitlistDraft,
): Promise<SignupResult> {
  const email = normalizeEmail(user.email ?? draft.email);
  if (draft.fullName.trim().length === 0) {
    return { status: 'error', message: MESSAGES.missingName };
  }

  const row = {
    user_id: user.id,
    full_name: draft.fullName.trim(),
    email,
    phone: optionalText(draft.phone),
    interest: optionalText(draft.interest),
    message: optionalText(draft.message),
  };

  const { data, error } = await client
    .from(WAITLIST_TABLE)
    .insert(row)
    .select('id,user_id,full_name,email,phone,interest,message,created_at')
    .maybeSingle<WaitlistSignup>();

  if (!error && data) {
    return { status: 'created', signup: data as WaitlistSignup, message: MESSAGES.created };
  }
  if (!error) {
    // Insert accepted but RLS hid the returned row; fall back to reading it back.
    const existing = await loadOwnWaitlistSignup(client, user.id);
    if (existing.signup) return { status: 'created', signup: existing.signup, message: MESSAGES.created };
    return { status: 'error', message: MESSAGES.genericFailure };
  }

  if (isUniqueViolation(error)) {
    const existing = await loadOwnWaitlistSignup(client, user.id);
    if (existing.signup) {
      return { status: 'already-submitted', signup: existing.signup, message: MESSAGES.alreadySubmitted };
    }
    return { status: 'already-submitted', message: MESSAGES.alreadySubmitted };
  }

  return { status: 'error', message: friendlyWaitlistError(error) };
}
