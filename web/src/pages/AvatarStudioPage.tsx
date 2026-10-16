import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { SignVoxEngine } from '../engine/useSignVoxEngine';
import { textToASL, type ASLToken } from '../lib/textToASL';
import { isSpeechRecognitionSupported } from '../lib/speechRecognition';

interface AvatarStudioPageProps {
  engine: SignVoxEngine;
  /** False while the user is on Live Translation; the page stays mounted so the
   *  GLB model, mixer and renderer are never reloaded on navigation. */
  active: boolean;
}

const labelFromClip = (clipName: string) => clipName.replace(/^ASL_/i, '').toUpperCase();

export const AvatarStudioPage: React.FC<AvatarStudioPageProps> = ({ engine, active }) => {
  const {
    avatarCanvasRef, avatarCtrlRef, avatarStatus, remeasureAvatar,
    recognizerRef, hearingState, spokenText, interimSpokenText, setSpokenText, setInterimSpokenText,
  } = engine;

  const [sentence, setSentence] = useState('');
  const [requested, setRequested] = useState<ASLToken[] | null>(null);
  const [requestedSource, setRequestedSource] = useState('');
  const [notice, setNotice] = useState<string | null>(null);
  const queueRef = useRef<number[]>([]);

  /** Real animation clips currently loaded in the production controller. */
  const signLabels = useMemo(() => {
    const clips = avatarCtrlRef.current?.animationClips ?? [];
    return clips
      .map((clip) => clip.name)
      .filter((name) => /^ASL_/i.test(name))
      .map(labelFromClip)
      .filter((label) => label !== 'NEUTRAL');
    // avatarStatus drives recomputation once the GLB finishes loading.
  }, [avatarStatus, avatarCtrlRef]);

  const ready = avatarStatus === 'Ready';
  const clearQueue = () => {
    queueRef.current.forEach((handle) => window.clearTimeout(handle));
    queueRef.current = [];
  };

  const playLabel = (label: string) => {
    avatarCtrlRef.current?.playSignByLabel(label);
  };

  /** Play supported tokens in order, using the real clip duration as the gap. */
  const playSequence = (tokens: ASLToken[]) => {
    clearQueue();
    const controller = avatarCtrlRef.current;
    if (!controller) return;
    let delay = 0;
    let played = 0;
    tokens.forEach((token) => {
      if (!token.supported || !token.canonicalName) return;
      const canonical = token.canonicalName;
      const clip = controller.animationClips.find((c) => c.name.toUpperCase() === `ASL_${canonical}`.toUpperCase());
      const handle = window.setTimeout(() => playLabel(canonical), delay);
      queueRef.current.push(handle);
      delay += Math.max(700, (clip?.duration ?? 0.9) * 1000);
      played += 1;
    });
    if (played === 0) {
      setNotice('None of those words have an animation clip yet, so nothing was played.');
    }
  };

  const submitSentence = (event: React.FormEvent) => {
    event.preventDefault();
    const value = sentence.trim();
    if (!value) return;
    const asl = textToASL(value);
    setRequested(asl.tokens);
    setRequestedSource(asl.sourceText);
    const supported = asl.tokens.filter((token) => token.supported).length;
    setNotice(
      supported === 0
        ? null
        : `${supported} of ${asl.tokens.length} words have a verified animation clip.`
    );
    if (supported > 0) playSequence(asl.tokens);
  };

  const latestSpoken = spokenText.length > 0 ? spokenText[spokenText.length - 1] : null;
  const tokens: ASLToken[] = requested ?? latestSpoken?.asl?.tokens ?? [];
  const tokenSource = requested ? requestedSource : latestSpoken?.text ?? '';
  const supportedCount = tokens.filter((token) => token.supported).length;

  React.useEffect(() => () => clearQueue(), []);

  // The viewport lives in a hidden page until this one is opened, so measure the
  // renderer against its real box as soon as the page becomes visible.
  useEffect(() => {
    if (!active) return;
    const frame = window.requestAnimationFrame(() => remeasureAvatar());
    return () => window.cancelAnimationFrame(frame);
  }, [active, remeasureAvatar]);

  return (
    <div className={active ? 'block' : 'hidden'} aria-hidden={!active}>
      {/* One column, read top to bottom: the avatar first, then the controls
          that drive it, so nothing is squeezed into a narrow side column. */}
      <div className="flex flex-col gap-5">
        {/* ---------------- Avatar viewport ---------------- */}
        <section className="svx-card p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h1 className="text-[1.15rem] font-extrabold tracking-tight">Avatar studio</h1>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.6875rem] font-semibold ${
                ready ? 'svx-chip svx-chip-ok' : 'svx-chip'
              }`}
            >
              <span className="svx-icon text-[0.8125rem]">{ready ? 'check_circle' : 'hourglass_top'}</span>
              {ready ? 'Avatar ready' : avatarStatus.replace('…', '') + '…'}
            </span>
          </div>

          <p className="mb-3 flex flex-wrap items-center gap-1.5 text-[0.72rem] font-semibold">
            <span className="svx-chip">Prototype</span>
            {signLabels.length > 0 ? (
              <span className="svx-chip svx-chip-ok">Supported animations: {signLabels.join(' · ')}</span>
            ) : (
              <span className="svx-chip">Loading supported animations…</span>
            )}
          </p>

          <div
            className="relative w-full overflow-hidden rounded-3xl bg-[#181824]"
            style={{ aspectRatio: '3 / 4', maxHeight: '58dvh', minHeight: '260px' }}
          >
            {/* Production Three.js host. The engine owns the GLB, lights, mixer
                and resize handling; this element only provides the surface. */}
            <div ref={avatarCanvasRef} className="absolute inset-0 h-full w-full" />
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => {
                clearQueue();
                avatarCtrlRef.current?.setMode('clip:ASL_NEUTRAL');
              }}
              disabled={!ready}
              className="svx-btn-ghost"
            >
              <span className="svx-icon text-[1.125rem]">accessibility_new</span>
              Rest pose
            </button>
            <button
              type="button"
              onClick={() => {
                clearQueue();
                tokens.length > 0 && playSequence(tokens);
              }}
              disabled={!ready || supportedCount === 0}
              className="svx-btn-ghost"
            >
              <span className="svx-icon text-[1.125rem]">play_arrow</span>
              Replay
            </button>
          </div>

          {avatarStatus.startsWith('Error') && (
            <p role="alert" className="mt-3 rounded-2xl border border-[#f0c8c3] bg-[#fff6f5] px-4 py-3 text-[0.82rem]">
              The 3D avatar could not be loaded, so sign playback is unavailable right now.
              <span className="mt-1 block text-[0.72rem] text-on-surface-variant">{avatarStatus}</span>
            </p>
          )}
          {!ready && !avatarStatus.startsWith('Error') && (
            <p className="mt-3 text-[0.78rem] text-on-surface-variant">
              Loading the SignVox avatar model. This happens once and is kept ready while you move between pages.
            </p>
          )}
        </section>

        {/* ---------------- Sign output ---------------- */}
        <div className="flex flex-col gap-5">
          <section className="svx-card p-5">
            <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
              Ask the avatar to sign
            </h2>
            <form onSubmit={submitSentence} className="mt-3 flex flex-wrap gap-3">
              <label className="sr-only" htmlFor="svx-sentence">Sentence to sign</label>
              <input
                id="svx-sentence"
                type="text"
                value={sentence}
                onChange={(e) => setSentence(e.target.value)}
                placeholder="Type a sentence, e.g. hello yes"
                autoComplete="off"
                className="svx-input min-w-0 flex-1"
              />
              <button type="submit" disabled={!ready || sentence.trim().length === 0} className="svx-btn-primary shrink-0">
                <span className="svx-icon text-[1.25rem]">sign_language</span>
                Sign it
              </button>
            </form>

            {tokenSource && (
              <p className="mt-4 text-[0.8rem] text-on-surface-variant">
                Requested: <strong className="text-on-surface">{tokenSource}</strong>
              </p>
            )}

            {tokens.length > 0 ? (
              <>
                <div className="mt-3 flex flex-wrap gap-2">
                  {tokens.map((token, index) => {
                    const key = `${token.sourceWord}-${index}`;
                    if (token.supported && token.canonicalName) {
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => playLabel(token.canonicalName as string)}
                          disabled={!ready}
                          className="svx-sign-chip"
                          title={`Play the ${token.canonicalName} animation`}
                        >
                          <span className="svx-icon text-[0.9375rem]">play_arrow</span>
                          {token.canonicalName}
                        </button>
                      );
                    }
                    return (
                      <span key={key} className="svx-sign-chip svx-sign-chip-unsupported" title="No animation clip exists for this word yet">
                        <span className="svx-icon text-[0.9375rem]">block</span>
                        {token.sourceWord} — not available
                      </span>
                    );
                  })}
                </div>
                {supportedCount === 0 && (
                  <p className="mt-3 text-[0.82rem] text-on-surface-variant">
                    SignVox cannot sign this sentence yet: none of those words have an animation clip.
                    {signLabels.length > 0 && <> Available now: <strong className="text-on-surface">{signLabels.join(', ')}</strong>.</>}
                  </p>
                )}
              </>
            ) : (
              <p className="mt-3 text-[0.82rem] text-on-surface-variant">
                {ready
                  ? signLabels.length > 0
                    ? <>Available signs in this build: <strong className="text-on-surface">{signLabels.join(', ')}</strong>.</>
                    : 'No sign animation clips are loaded in this build, so nothing can be signed yet.'
                  : 'Waiting for the avatar model to finish loading.'}
              </p>
            )}

            {notice && <p className="mt-3 text-[0.78rem] text-on-surface-variant">{notice}</p>}
          </section>

          <section className="svx-card p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
                Or speak
              </h2>
              {!isSpeechRecognitionSupported() && (
                <span className="text-[0.72rem] text-on-surface-variant">Microphone input not supported here</span>
              )}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => recognizerRef.current?.start()}
                disabled={hearingState === 'listening' || hearingState === 'unsupported'}
                className="svx-btn-ghost"
              >
                <span className="svx-icon text-[1.125rem]">mic</span>
                Start listening
              </button>
              <button
                type="button"
                onClick={() => recognizerRef.current?.stop()}
                disabled={hearingState !== 'listening'}
                className="svx-btn-ghost"
              >
                <span className="svx-icon text-[1.125rem]">mic_off</span>
                Stop listening
              </button>
            </div>
            <p className="mt-3 text-[0.78rem] text-on-surface-variant">
              {hearingState === 'listening'
                ? interimSpokenText
                  ? `Hearing: “${interimSpokenText}”`
                  : 'Listening… speak the sentence you want signed.'
                : 'Speech is turned into sign words on this device and sent to the avatar.'}
            </p>
            {spokenText.length > 0 && (
              <div className="mt-3 flex items-center justify-between gap-3">
                <p className="text-[0.78rem] text-on-surface-variant">
                  Last request: <strong className="text-on-surface">{latestSpoken?.text}</strong>
                </p>
                <button
                  type="button"
                  onClick={() => { setSpokenText([]); setInterimSpokenText(''); setRequested(null); setRequestedSource(''); }}
                  className="min-h-9 text-[0.75rem] font-semibold text-primary underline-offset-4 hover:underline"
                >
                  Clear
                </button>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};
