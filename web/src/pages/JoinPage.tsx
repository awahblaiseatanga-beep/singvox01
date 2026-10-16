import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { User } from '@supabase/supabase-js';
import {
  WAITLIST_UNAVAILABLE_MESSAGE,
  isSupabaseConfigured,
  supabase,
} from '../lib/supabaseClient';
import {
  WAITLIST_INTERESTS,
  clearWaitlistDraft,
  draftFromStoredAndUser,
  emptyWaitlistDraft,
  friendlyWaitlistError,
  isValidEmail,
  loadOwnWaitlistSignup,
  loadWaitlistDraft,
  normalizeEmail,
  readAuthCallbackError,
  requestWaitlistMagicLink,
  resolveInterest,
  saveWaitlistDraft,
  submitWaitlistSignup,
  waitlistRedirectUrl,
  type WaitlistDraft,
  type WaitlistSignup,
} from '../lib/waitlist';

/**
 * Waiting-list and partnership enquiry page.
 *
 * Two submission paths, chosen automatically:
 *
 *  - Securely connected (VITE_SUPABASE_URL + VITE_SUPABASE_PUBLISHABLE_KEY set):
 *    the visitor's details are held as Supabase user metadata, a magic link
 *    verifies the email address, and only then is the row written to
 *    `public.waitlist_signups` under Row Level Security. Nobody — including
 *    other signed-in visitors — can read it back except the owner of the row.
 *
 *  - Not connected: the original behaviour is preserved. The visitor prepares
 *    the enquiry in their own mail app, addressed to the team inbox configured
 *    via VITE_CONTACT_EMAIL. Until that inbox is configured the form stays
 *    disabled with a clear explanation instead of silently losing submissions.
 */

const CONTACT_EMAIL = (import.meta.env.VITE_CONTACT_EMAIL as string | undefined)?.trim() || '';
const INTERESTS = WAITLIST_INTERESTS;

type Phase =
  | 'form'
  | 'sending'
  | 'link-sent'
  | 'checking'
  | 'confirm'
  | 'submitting'
  | 'joined'
  | 'mailto-ready';

const sessionStore = (): Storage | null => (typeof sessionStorage === 'undefined' ? null : sessionStorage);

export const JoinPage: React.FC<{ active: boolean }> = ({ active }) => {
  const [draft, setDraft] = useState<WaitlistDraft>(() => loadWaitlistDraft(sessionStore()) ?? emptyWaitlistDraft());
  const [phase, setPhase] = useState<Phase>('form');
  const [user, setUser] = useState<User | null>(null);
  const [signup, setSignup] = useState<WaitlistSignup | null>(null);
  const [duplicate, setDuplicate] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [sentTo, setSentTo] = useState('');
  const [mailtoHref, setMailtoHref] = useState('');
  // Supabase emits several auth events on load (initial session, sign-in from a
  // magic link, token refresh). Resolving the same visitor once is enough.
  const resolvedUserIdRef = useRef<string | null>(null);

  const setField = (field: keyof WaitlistDraft, value: string) =>
    setDraft((current) => ({ ...current, [field]: value }));

  const mergeVerifiedIdentity = useCallback((verified: User | null) => {
    if (!verified) return;
    const known = draftFromStoredAndUser(null, verified);
    setDraft((current) => ({
      fullName: current.fullName.trim() || known.fullName,
      email: current.email.trim() || known.email,
      phone: current.phone.trim() || known.phone,
      organization: current.organization.trim() || known.organization,
      interest: resolveInterest([current.interest, known.interest]),
      message: current.message,
    }));
  }, []);

  // Surface expired / already-used magic links, and resolve any existing session
  // (including the one created by the link that has just been clicked).
  useEffect(() => {
    const callbackError = readAuthCallbackError();
    if (callbackError) setNotice(callbackError.message);

    const client = supabase;
    if (!client) return;

    let cancelled = false;
    const resolve = async (verified: User | null) => {
      if (cancelled) return;
      if (verified && verified.id === resolvedUserIdRef.current) return;
      resolvedUserIdRef.current = verified?.id ?? null;
      if (!verified) {
        setUser(null);
        setSignup(null);
        setDuplicate(false);
        setPhase((current) => (current === 'link-sent' ? current : 'form'));
        return;
      }
      setUser(verified);
      mergeVerifiedIdentity(verified);
      setPhase((current) => (current === 'joined' ? current : 'checking'));
      const { signup: existing, error } = await loadOwnWaitlistSignup(client, verified.id);
      if (cancelled) return;
      if (error) setNotice(friendlyWaitlistError(error));
      if (existing) {
        setSignup(existing);
        setDuplicate(false);
        setPhase('joined');
        return;
      }
      setPhase('confirm');
    };

    void client.auth.getSession().then(({ data }) => resolve(data.session?.user ?? null));
    const { data: listener } = client.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' || event === 'INITIAL_SESSION' || event === 'SIGNED_OUT' || event === 'USER_UPDATED') {
        void resolve(session?.user ?? null);
      }
    });
    return () => {
      cancelled = true;
      listener.subscription.unsubscribe();
    };
  }, [mergeVerifiedIdentity]);

  const sendMagicLink = useCallback(async () => {
    setNotice(null);
    const client = supabase;
    if (!client) {
      setNotice(WAITLIST_UNAVAILABLE_MESSAGE);
      return;
    }
    setPhase('sending');
    const result = await requestWaitlistMagicLink(client, draft, waitlistRedirectUrl());
    if (!result.ok) {
      setNotice(result.message);
      setPhase('form');
      return;
    }
    saveWaitlistDraft(sessionStore(), draft);
    setSentTo(result.email ?? normalizeEmail(draft.email));
    setPhase('link-sent');
  }, [draft]);

  const confirmSignup = useCallback(async () => {
    setNotice(null);
    const client = supabase;
    if (!client || !user) return;
    setPhase('submitting');
    const result = await submitWaitlistSignup(client, user, draft);
    if (result.status === 'error') {
      setNotice(result.message);
      setPhase('confirm');
      return;
    }
    setSignup(result.signup ?? null);
    setDuplicate(result.status === 'already-submitted');
    clearWaitlistDraft(sessionStore());
    setPhase('joined');
  }, [draft, user]);

  const signOut = useCallback(async () => {
    setNotice(null);
    setSignup(null);
    setDuplicate(false);
    setUser(null);
    resolvedUserIdRef.current = null;
    setPhase('form');
    if (supabase) await supabase.auth.signOut();
  }, []);

  if (!active) return null;

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (phase === 'sending' || phase === 'submitting') return;
    if (phase === 'confirm' || phase === 'joined') {
      void confirmSignup();
      return;
    }
    if (isSupabaseConfigured) {
      void sendMagicLink();
      return;
    }
    // Not connected: preserve the original "prepare the email yourself" flow.
    setNotice(null);
    if (!CONTACT_EMAIL) {
      setNotice('Our inbox is not connected yet — please check back soon.');
      return;
    }
    if (draft.fullName.trim().length === 0) {
      setNotice('Please tell us your name.');
      return;
    }
    if (!isValidEmail(draft.email)) {
      setNotice('Please enter a valid email address so we can reply.');
      return;
    }
    const subject = encodeURIComponent(`SignVox ${draft.interest} enquiry — ${draft.fullName.trim()}`);
    const body = encodeURIComponent(
      [
        `Name: ${draft.fullName.trim()}`,
        `Email: ${draft.email.trim()}`,
        `Phone: ${draft.phone.trim() || '—'}`,
        `Organization: ${draft.organization.trim() || '—'}`,
        `Interest: ${draft.interest}`,
        '',
        draft.message.trim() || '(no message)',
      ].join('\n'),
    );
    setMailtoHref(`mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`);
    setPhase('mailto-ready');
  };

  const inputClass = 'svx-input';
  const verified = Boolean(user) && (phase === 'confirm' || phase === 'submitting' || phase === 'joined');
  const formDisabled = !isSupabaseConfigured && !CONTACT_EMAIL;
  const busy = phase === 'sending' || phase === 'submitting';
  const showForm = phase === 'form' || phase === 'sending' || phase === 'confirm' || phase === 'submitting' || phase === 'mailto-ready';

  return (
    <div className="flex flex-col gap-5">
      <section className="svx-card p-8">
        <p>
          <span className="svx-chip svx-chip-ok">
            <span className="svx-icon text-[0.8125rem]">mail</span>
            Join the waiting list
          </span>
        </p>
        <h1 className="mt-4 text-[1.9rem] font-extrabold tracking-tight">
          Stay close to SingVox
        </h1>
        <p className="mt-3 max-w-[40rem] text-[0.9rem] leading-relaxed text-on-surface-variant">
          Tell us who you are and what brings you here — early access, community
          collaboration, research, technology partnership, sponsorship or investment.
          Submitting an enquiry is not a commitment by either side; we will simply reply
          and start a conversation.
        </p>
      </section>

      {/* ---------------- Verified: on the list ---------------- */}
      {phase === 'joined' && (
        <section className="svx-card p-8" aria-labelledby="join-done-heading" role="status">
          <span className="svx-chip svx-chip-ok">
            <span className="svx-icon text-[0.8125rem]">check_circle</span>
            {duplicate ? 'Already on the list' : 'Email verified · you are on the list'}
          </span>
          <h2 id="join-done-heading" className="mt-4 text-[1.2rem] font-extrabold tracking-tight">
            {duplicate ? 'You were already on the waiting list' : 'Thank you — your email is verified'}
          </h2>
          <p className="mt-2 max-w-[40rem] text-[0.85rem] leading-relaxed text-on-surface-variant">
            {duplicate
              ? 'We already have your details from a previous sign-up, so nothing was added twice. Reply to any of our emails if you would like us to update them.'
              : 'Your place is saved. We will contact you at the verified address below as early access and partnership conversations open up.'}
          </p>
          <dl className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(12rem,1fr))] gap-3">
            {[
              { label: 'Name', value: draft.fullName.trim() || signup?.full_name || '—' },
              { label: 'Verified email', value: user?.email ?? signup?.email ?? '—' },
              { label: 'Phone', value: draft.phone.trim() || signup?.phone || '—' },
              { label: 'Interest', value: signup?.interest ?? draft.interest },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl bg-surface-dim px-4 py-3">
                <dt className="text-[0.72rem] font-bold uppercase tracking-[0.12em] text-on-surface-variant">{item.label}</dt>
                <dd className="mt-0.5 break-words text-[0.88rem] font-semibold">{item.value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-[0.78rem] leading-relaxed text-on-surface-variant">
            Only the SingVox team can read the waiting list, and only you and the team can
            read this entry. Being on the waiting list is not permission to use your
            recordings or any personal data for AI training.
          </p>
          <button type="button" onClick={() => void signOut()} className="svx-btn-ghost mt-4">
            <span className="svx-icon text-[1.25rem]">logout</span>
            Sign out on this device
          </button>
        </section>
      )}

      {/* ---------------- Link sent ---------------- */}
      {phase === 'link-sent' && (
        <section className="svx-card p-8" aria-labelledby="join-sent-heading" role="status">
          <span className="svx-chip svx-chip-ok">
            <span className="svx-icon text-[0.8125rem]">mark_email_unread</span>
            Verification link sent
          </span>
          <h2 id="join-sent-heading" className="mt-4 text-[1.2rem] font-extrabold tracking-tight">
            Check your inbox
          </h2>
          <p className="mt-2 max-w-[40rem] text-[0.85rem] leading-relaxed text-on-surface-variant">
            We sent a secure sign-in link to <strong className="text-on-surface">{sentTo}</strong>.
            Your details are saved only after you open that link and confirm the address —
            that step is what keeps the waiting list free of mistyped or fake emails.
          </p>
          <ul className="mt-3 flex list-disc flex-col gap-1 pl-5 text-[0.8rem] leading-relaxed text-on-surface-variant">
            <li>The link works once and expires after a short time.</li>
            <li>Nothing arrived? Check the spam folder before requesting another.</li>
            <li>You can close this page — the link brings you back here.</li>
          </ul>
          <div className="mt-4 flex flex-wrap gap-2.5">
            <button type="button" onClick={() => void sendMagicLink()} disabled={busy} className="svx-btn-primary">
              <span className="svx-icon text-[1.25rem]">forward_to_inbox</span>
              {busy ? 'Sending…' : 'Resend the link'}
            </button>
            <button type="button" onClick={() => { setNotice(null); setPhase('form'); }} className="svx-btn-ghost">
              <span className="svx-icon text-[1.25rem]">edit</span>
              Use a different email
            </button>
          </div>
        </section>
      )}

      {phase === 'checking' && (
        <section className="svx-card p-8" role="status">
          <p className="text-[0.88rem] font-semibold">Verifying your sign-in link…</p>
          <p className="mt-1 text-[0.82rem] text-on-surface-variant">This takes a second — please keep this page open.</p>
        </section>
      )}

      {/* ---------------- Form / confirm ---------------- */}
      {showForm && (
        <section className="svx-card p-8" aria-labelledby="join-form-heading">
          <h2 id="join-form-heading" className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
            {verified ? 'Confirm your details' : 'Your details'}
          </h2>

          {verified && (
            <p className="mt-3 rounded-2xl border border-[#bfe3c9] bg-[#f2fbf5] px-4 py-3 text-[0.85rem]">
              Your email is verified. Review the details below and add yourself to the
              waiting list.
            </p>
          )}

          {!verified && isSupabaseConfigured && (
            <p className="mt-3 text-[0.8rem] leading-relaxed text-on-surface-variant">
              We verify your email address before adding you, so the waiting list stays
              trustworthy. You will receive one sign-in link — open it and your details are
              saved.
            </p>
          )}

          {formDisabled && (
            <p role="status" className="mt-4 rounded-2xl border border-[#f0d9a8] bg-[#fffaf0] px-4 py-3 text-[0.85rem]">
              The secure waiting list is not connected on this build yet, and our team inbox is
              still being connected, so this form is disabled for now. Please try the demo and
              check back soon — nothing you type here is sent or stored anywhere.
            </p>
          )}

          <form onSubmit={submit} className="mt-4 flex flex-col gap-4">
            <div className="grid grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] gap-4">
              <div>
                <label htmlFor="join-name" className="mb-1.5 block text-[0.8rem] font-semibold">Name *</label>
                <input id="join-name" type="text" autoComplete="name" value={draft.fullName} onChange={(e) => setField('fullName', e.target.value)} disabled={formDisabled || busy} className={inputClass} placeholder="Your full name" />
              </div>
              <div>
                <label htmlFor="join-email" className="mb-1.5 block text-[0.8rem] font-semibold">Email *</label>
                <input
                  id="join-email"
                  type="email"
                  autoComplete="email"
                  value={verified ? (user?.email ?? draft.email) : draft.email}
                  onChange={(e) => setField('email', e.target.value)}
                  disabled={formDisabled || busy || verified}
                  readOnly={verified}
                  className={inputClass}
                  placeholder="you@example.org"
                  aria-describedby={verified ? 'join-email-verified' : undefined}
                />
                {verified && (
                  <p id="join-email-verified" className="mt-1 text-[0.72rem] text-on-surface-variant">
                    Verified — this is the address we will reply to.
                  </p>
                )}
              </div>
            </div>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] gap-4">
              <div>
                <label htmlFor="join-phone" className="mb-1.5 block text-[0.8rem] font-semibold">Phone <span className="font-normal text-on-surface-variant">(optional)</span></label>
                <input id="join-phone" type="tel" autoComplete="tel" value={draft.phone} onChange={(e) => setField('phone', e.target.value)} disabled={formDisabled || busy} className={inputClass} placeholder="+237 …" />
              </div>
              <div>
                <label htmlFor="join-org" className="mb-1.5 block text-[0.8rem] font-semibold">Organization <span className="font-normal text-on-surface-variant">(optional)</span></label>
                <input id="join-org" type="text" autoComplete="organization" value={draft.organization} onChange={(e) => setField('organization', e.target.value)} disabled={formDisabled || busy} className={inputClass} placeholder="School, company, association…" />
              </div>
            </div>
            <div>
              <label htmlFor="join-interest" className="mb-1.5 block text-[0.8rem] font-semibold">I am interested as</label>
              <select id="join-interest" value={draft.interest} onChange={(e) => setField('interest', e.target.value)} disabled={formDisabled || busy} className={inputClass}>
                {INTERESTS.map((option) => (<option key={option} value={option}>{option}</option>))}
              </select>
            </div>
            <div>
              <label htmlFor="join-message" className="mb-1.5 block text-[0.8rem] font-semibold">Message <span className="font-normal text-on-surface-variant">(optional)</span></label>
              <textarea id="join-message" rows={4} value={draft.message} onChange={(e) => setField('message', e.target.value)} disabled={formDisabled || busy} className={inputClass} placeholder="What would you like to explore with SingVox?" />
            </div>

            {notice && (
              <p role="alert" className="rounded-2xl border border-[#f0c8c3] bg-[#fff6f5] px-4 py-3 text-[0.85rem]">{notice}</p>
            )}

            {phase === 'mailto-ready' ? (
              <div role="status" className="rounded-2xl border border-[#bfe3c9] bg-[#f2fbf5] px-4 py-3">
                <p className="text-[0.88rem] font-semibold">Your message is ready in your email app.</p>
                <p className="mt-1 text-[0.8rem] text-on-surface-variant">Nothing is sent automatically — review and press send yourself.</p>
                <a href={mailtoHref} className="svx-btn-primary mt-3 inline-flex">
                  <span className="svx-icon text-[1.25rem]">send</span>
                  Open my email app to send
                </a>
              </div>
            ) : (
              <button
                type="submit"
                disabled={formDisabled || busy}
                className="svx-btn-primary w-auto"
                title={
                  formDisabled
                    ? 'Waiting list not connected yet'
                    : verified
                      ? 'Add me to the waiting list'
                      : isSupabaseConfigured
                        ? 'Send my verification link'
                        : 'Prepare your enquiry email'
                }
              >
                <span className="svx-icon text-[1.25rem]">{verified ? 'check_circle' : 'send'}</span>
                {phase === 'submitting'
                  ? 'Saving…'
                  : phase === 'sending'
                    ? 'Sending the link…'
                    : verified
                      ? 'Add me to the waiting list'
                      : isSupabaseConfigured
                        ? 'Send my verification link'
                        : 'Prepare my enquiry email'}
              </button>
            )}
          </form>

          <div className="mt-6 rounded-2xl bg-surface-dim px-4 py-3">
            <h3 className="text-[0.78rem] font-bold uppercase tracking-[0.12em] text-on-surface-variant">How your details are handled</h3>
            <ul className="mt-2 flex list-disc flex-col gap-1 pl-5 text-[0.78rem] leading-relaxed text-on-surface-variant">
              {isSupabaseConfigured ? (
                <>
                  <li>Your details are saved to the SingVox team&apos;s own database only after you confirm your email address.</li>
                  <li>They are protected so that only you and the team can read your entry — no other visitor can list or export the waiting list.</li>
                  <li>We use them solely to reply and manage early-access and partnership conversations.</li>
                </>
              ) : (
                <li>Your message goes only to the SingVox team inbox, by email you send yourself.</li>
              )}
              <li>No camera video, landmarks or biometric data are collected on this page.</li>
              <li>Joining the waiting list never grants permission to use your recordings for AI training.</li>
              <li>Ask for correction or deletion any time by replying to our response.</li>
            </ul>
          </div>
        </section>
      )}
    </div>
  );
};
