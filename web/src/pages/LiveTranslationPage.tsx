import React from 'react';
import { HandOverlay } from '../components/HandOverlay';
import type { SignVoxEngine } from '../engine/useSignVoxEngine';
import { deriveLiveStatus, friendlyError } from '../lib/uiStatus';

interface LiveTranslationPageProps {
  engine: SignVoxEngine;
  /** False while the user is on Avatar Studio; the page stays mounted so the
   *  camera stream, landmark pipeline and recognition state survive. */
  active: boolean;
}

export const LiveTranslationPage: React.FC<LiveTranslationPageProps> = ({ engine, active }) => {
  const {
    status, error, start, stop, activeRef,
    videoRef, latestDetection, liveResult, stableState, metrics,
    transcript, setTranscript, showSkeleton,
    autoSpeak, toggleAutoSpeak, speakLatest, stopSpeaking, isSpeechSupported,
    activeModelSpec, avatarCanPlay, recognitionGate,
  } = engine;

  const sequenceStatus = metrics?.sequenceStatus;
  const live = deriveLiveStatus({
    status,
    error,
    isActive: activeRef.current,
    bufferReady: Boolean(sequenceStatus?.isReady),
    bufferProgress: sequenceStatus?.progressPercent ?? 0,
  });
  const cameraOn = activeRef.current;
  const currentSign = stableState?.currentStableName?.trim();
  // Scope vs animation coverage: the model recognises more signs than the
  // production avatar can currently perform, and the UI states both numbers.
  const animatedSigns = activeModelSpec.avatarClipLabels.join(' · ');
  const animatedCount = activeModelSpec.avatarClipLabels.length;
  const hasUnanimatedSigned = activeModelSpec.classCount > animatedCount;
  // A recognised sign may not have an avatar clip; say so instead of playing
  // an unrelated animation or implying the avatar is broken.
  const currentSignHasClip = currentSign ? avatarCanPlay(currentSign) : false;
  const recent = [...transcript].reverse();
  const speechAvailable = isSpeechSupported();

  return (
    <div className={active ? 'block' : 'hidden'} aria-hidden={!active}>
      {error && (
        <div
          role="alert"
          className="mb-4 rounded-3xl border border-[#f0c8c3] bg-[#fff6f5] px-5 py-4 text-on-surface"
        >
          <p className="text-[0.95rem] font-bold">{friendlyError(error).title}</p>
          <p className="mt-1 text-[0.85rem] text-on-surface-variant">{friendlyError(error).hint}</p>
          <p className="mt-2 break-words text-[0.72rem] text-on-surface-variant/80">{error}</p>
        </div>
      )}

      {/* One column, read top to bottom: camera, then the text and speech
          panels below it, so every line gets the full width of the screen. */}
      <div className="flex flex-col gap-5">
        {/* ---------------- Camera ---------------- */}
        <section className="svx-card p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h1 className="text-[1.15rem] font-extrabold tracking-tight">Live translation</h1>
            <span className="flex items-center gap-1.5 text-[0.75rem] font-semibold text-on-surface-variant">
              <span
                className={`h-2 w-2 rounded-full ${cameraOn ? 'bg-emerald-500' : 'bg-on-surface-variant/40'}`}
                aria-hidden="true"
              />
              {live.label}
            </span>
          </div>

          <p className="mb-3 flex flex-wrap items-center gap-1.5 text-[0.72rem] font-semibold">
            <span className="svx-chip">Prototype</span>
            <span className="svx-chip svx-chip-ok">Recognized signs: {activeModelSpec.scopeChip}</span>
            <span className="svx-chip">{activeModelSpec.displayName}</span>
            <span className="text-on-surface-variant">ASL-based — not validated CSL</span>
          </p>

          {hasUnanimatedSigned && (
            <p className="mb-3 text-[0.72rem] leading-relaxed text-on-surface-variant">
              Recognizes {activeModelSpec.classCount} signs; the avatar animates{' '}
              <strong className="text-on-surface">{animatedCount}</strong> of them ({animatedSigns}).
              Other recognized signs are shown as text only.
            </p>
          )}

          <div className="relative w-full overflow-hidden rounded-3xl bg-[#0b1120]" style={{ aspectRatio: '16 / 9' }}>
            <video
              ref={videoRef}
              muted
              playsInline
              className="mirrored-preview"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            <HandOverlay
              videoRef={videoRef}
              rawDetection={latestDetection}
              liveResult={liveResult}
              stableState={stableState}
              isBuffering={!sequenceStatus?.isReady}
              bufferProgress={sequenceStatus?.progressPercent ?? 0}
              showSkeleton={showSkeleton}
            />

            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-[#0b1120]/92 px-6 text-center">
                <span className="svx-icon text-[2.5rem] text-[#8fdcff]">videocam_off</span>
                <p className="text-[0.95rem] font-semibold text-white">Camera is off</p>
                <p className="max-w-[22rem] text-[0.8rem] text-[#a9c4c6]">{live.detail}</p>
              </div>
            )}
          </div>

          <div className="mt-4 flex flex-row flex-wrap items-center gap-3">
            {cameraOn ? (
              <button type="button" onClick={stop} className="svx-btn-danger w-auto">
                <span className="svx-icon text-[1.25rem]">stop_circle</span>
                End session
              </button>
            ) : (
              <button
                type="button"
                onClick={start}
                disabled={live.phase === 'starting-camera'}
                className="svx-btn-primary w-auto"
              >
                <span className="svx-icon text-[1.25rem]">videocam</span>
                {live.phase === 'starting-camera' ? 'Starting…' : 'Start translation'}
              </button>
            )}

            {cameraOn && !sequenceStatus?.isReady && (
              <div className="flex-1">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-dim">
                  <div
                    className="h-full rounded-full bg-primary-bright transition-[width] duration-300"
                    style={{ width: `${Math.max(4, Math.min(100, sequenceStatus?.progressPercent ?? 0))}%` }}
                  />
                </div>
                <p className="mt-1.5 text-[0.75rem] text-on-surface-variant">{live.detail}</p>
              </div>
            )}

            {cameraOn && sequenceStatus?.isReady && (
              <p className="text-[0.78rem] text-on-surface-variant">{live.detail}</p>
            )}
          </div>

          <p className="mt-3 flex items-start gap-1.5 text-[0.72rem] leading-relaxed text-on-surface-variant">
            <span className="svx-icon text-[0.875rem]" aria-hidden="true">lock</span>
            Video stays on this device. Only landmark points are processed, and nothing is uploaded.
          </p>
        </section>

        {/* ---------------- Results ---------------- */}
        <div className="flex flex-col gap-5">
          <section className="svx-card p-5" aria-live="polite">
            <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">Translation</h2>
            {currentSign ? (
              <p className="mt-3 break-words text-[2.9rem] font-extrabold leading-none tracking-tight text-primary">
                {currentSign}
              </p>
            ) : (
              <p className="mt-3 text-[0.95rem] leading-relaxed text-on-surface-variant">
                Your translation will appear here when a sign is recognized.
              </p>
            )}
            {cameraOn && recognitionGate && !recognitionGate.allowed && (
              <p className="mt-2 flex items-start gap-1.5 text-[0.78rem] text-on-surface-variant">
                <span className="svx-icon text-[0.875rem]" aria-hidden="true">front_hand</span>
                {recognitionGate.detail}
              </p>
            )}
            {currentSign && !currentSignHasClip && (
              <p className="mt-2 flex items-start gap-1.5 text-[0.78rem] text-on-surface-variant">
                <span className="svx-icon text-[0.875rem]" aria-hidden="true">info</span>
                Recognized as text only. The avatar has no verified animation for this sign yet.
              </p>
            )}
            <p className="mt-3 text-[0.78rem] text-on-surface-variant">
              {cameraOn
                ? sequenceStatus?.isReady
                  ? 'Hold a sign steady in view for a moment.'
                  : 'Getting ready — keep your hands in view.'
                : 'Press Start translation to begin.'}
            </p>
          </section>

          <section className="svx-card p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">Speak it out</h2>
              {!speechAvailable && (
                <span className="text-[0.72rem] text-on-surface-variant">Not supported in this browser</span>
              )}
            </div>
            <label className="mt-3 flex min-h-11 items-center gap-3 text-[0.88rem] font-medium">
              <input
                type="checkbox"
                checked={autoSpeak}
                onChange={toggleAutoSpeak}
                disabled={!speechAvailable}
                className="h-5 w-5 rounded border-hairline accent-primary"
              />
              Speak each recognized sign aloud
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={speakLatest}
                disabled={!speechAvailable || transcript.length === 0}
                className="svx-btn-ghost"
              >
                <span className="svx-icon text-[1.125rem]">volume_up</span>
                Speak latest
              </button>
              <button type="button" onClick={stopSpeaking} disabled={!speechAvailable} className="svx-btn-ghost">
                <span className="svx-icon text-[1.125rem]">volume_off</span>
                Stop speaking
              </button>
            </div>
          </section>

          <section className="svx-card p-5" id="signvox-transcript">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
                Recent translations
              </h2>
              {transcript.length > 0 && (
                <button
                  type="button"
                  onClick={() => setTranscript([])}
                  className="min-h-9 text-[0.75rem] font-semibold text-primary underline-offset-4 hover:underline"
                >
                  Clear
                </button>
              )}
            </div>
            {recent.length === 0 ? (
              <p className="mt-3 text-[0.88rem] text-on-surface-variant">
                Recognized signs will be listed here as they are committed.
              </p>
            ) : (
              <ul className="mt-3 flex flex-col gap-2">
                {recent.slice(0, 12).map((item) => (
                  <li key={item.id} className="svx-card-muted flex items-center justify-between gap-3 px-4 py-2.5">
                    <span className="flex items-center gap-2">
                      <span className="text-[0.95rem] font-bold tracking-wide">{item.displayText}</span>
                      {item.avatarClipAvailable === false && (
                        <span className="text-[0.68rem] font-semibold uppercase tracking-wide text-on-surface-variant">
                          text only
                        </span>
                      )}
                    </span>
                    <span className="text-[0.72rem] text-on-surface-variant">
                      {item.at ? new Date(item.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {recent.length > 12 && (
              <p className="mt-3 text-[0.72rem] text-on-surface-variant">Showing the 12 most recent of {recent.length}.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};
