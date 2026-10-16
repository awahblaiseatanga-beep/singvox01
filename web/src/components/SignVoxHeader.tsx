import React from 'react';

export type SignVoxPage = 'welcome' | 'live' | 'avatar' | 'join';

export interface SignVoxHeaderProps {
  /** Live camera / pipeline status, e.g. "Ready" or "Camera stopped". */
  status: string;
  /** Avatar controller status. Shown as a second chip on the diagnostics bar. */
  avatarStatus?: string;
  /** Number of recognized signs currently in the transcript. */
  transcriptCount?: number;
  /** Scrolls the transcript panel into view. */
  onOpenTranscript?: () => void;
  /** `light` for the product pages, `dark` for the internal diagnostics screen. */
  variant?: 'light' | 'dark';
  /** Active product page; when provided with `onNavigate` the nav renders. */
  activePage?: SignVoxPage;
  /** Navigates between the public pages. */
  onNavigate?: (page: SignVoxPage) => void;
}

const toneFor = (value: string): string => {
  const normalized = value.toLowerCase();
  if (/(ready|running|recording|active|listening|streaming)/.test(normalized)) return 'svx-chip svx-chip-ok';
  if (/(error|fail|blocked|denied|unsupported|stopped|unable)/.test(normalized)) return 'svx-chip svx-chip-warn';
  return 'svx-chip';
};

const NAV_PAGES: { id: SignVoxPage; label: string; icon: string }[] = [
  { id: 'welcome', label: 'Home', icon: 'home' },
  { id: 'live', label: 'Live Demo', icon: 'videocam' },
  { id: 'avatar', label: 'Avatar Studio', icon: 'accessibility_new' },
  { id: 'join', label: 'Join', icon: 'mail' },
];

export const SignVoxHeader: React.FC<SignVoxHeaderProps> = ({
  status,
  avatarStatus,
  transcriptCount = 0,
  onOpenTranscript,
  variant = 'light',
  activePage,
  onNavigate,
}) => {
  const dark = variant === 'dark';

  return (
    <header className={`svx-appbar pt-safe w-full${dark ? ' svx-appbar-dark' : ''}`}>
      <div className="mx-auto flex h-16 w-full max-w-[1400px] items-center justify-between gap-3 px-6">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="svx-brand-mark flex h-9 w-9 shrink-0 items-center justify-center rounded-full">
            <span className="svx-icon text-[1.25rem]">spatial_audio</span>
          </div>
          <div className="flex min-w-0 flex-col">
            <span
              className={`text-[1.3125rem] font-extrabold leading-none tracking-tight ${
                dark ? 'text-white' : 'text-on-surface'
              }`}
            >
              Sign<span className="text-primary-bright">Vox</span>
            </span>
            <span className={`mt-0.5 text-[0.625rem] font-semibold uppercase tracking-[0.16em] ${
              dark ? 'text-[#8fdcff]' : 'text-on-surface-variant'
            }`}>
              {dark ? 'Web Vision Diagnostic' : 'Prototype · Sign language, live'}
            </span>
          </div>
        </div>

        {/* Navigation lives in the floating island bar at the bottom, at every
            screen size, so the shell keeps one identical composition. */}
        <div className="flex items-center gap-3">
          {dark && avatarStatus && (
            <span
              className={`${toneFor(avatarStatus)} inline-flex max-w-[48vw] items-center gap-1 truncate rounded-full px-2.5 py-1 text-[0.6875rem] font-semibold`}
              title="3D avatar controller status"
            >
              <span className="svx-icon text-[0.8125rem]">person_play</span>
              Avatar: {avatarStatus}
            </span>
          )}

          <span
            className={`${toneFor(status)} inline-flex max-w-[48vw] items-center gap-1.5 truncate rounded-full px-2.5 py-1 text-[0.6875rem] font-semibold`}
            title="Camera and recognition pipeline status"
          >
            <span className="svx-icon text-[0.8125rem]">{dark ? 'videocam' : 'sensors'}</span>
            <span className="truncate">{status}</span>
          </span>

          {onOpenTranscript && transcriptCount > 0 && (
            <button
              type="button"
              onClick={onOpenTranscript}
              aria-label={`Jump to the transcript (${transcriptCount} recognized signs)`}
              title="Jump to the sign transcript"
              className="svx-icon-btn relative"
            >
              <span className="svx-icon text-[1.25rem]">history</span>
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary-bright px-1 text-[0.625rem] font-bold text-white">
                {transcriptCount > 99 ? '99+' : transcriptCount}
              </span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
