import { useEffect, useState } from 'react';
import { SignVoxHeader, type SignVoxPage } from './components/SignVoxHeader';
import { DiagnosticDashboard } from './components/DiagnosticDashboard';
import { AvatarDiagnostic } from './components/AvatarDiagnostic';
import { useSignVoxEngine } from './engine/useSignVoxEngine';
import { LiveTranslationPage } from './pages/LiveTranslationPage';
import { AvatarStudioPage } from './pages/AvatarStudioPage';
import { WelcomePage } from './pages/WelcomePage';
import { JoinPage } from './pages/JoinPage';
import { deriveLiveStatus } from './lib/uiStatus';

/**
 * SignVox public proof of concept:
 *   #welcome (default) - landing page
 *   #live    - Live Translation demo
 *   #avatar  - Avatar Studio
 *   #join    - waiting list and partnership enquiries
 * The engineering screens stay reachable by hash for internal use only:
 *   #diagnostics       - the former diagnostic dashboard
 *   #avatar-diagnostic - the existing avatar rig test suite
 */
type Route = SignVoxPage | 'diagnostics' | 'avatar-diagnostic';

/**
 * Supabase magic-link callbacks arrive in the URL fragment (implicit flow), and
 * the auth client clears the fragment once it has a session. The waiting list is
 * the only page that can consume a callback, so a callback fragment — and the
 * empty hash left behind right after a successful one — resolves to the Join
 * page instead of falling through to Home.
 */
const AUTH_CALLBACK_PARAM = /(?:^|[#&?])(access_token|refresh_token|error|error_code|error_description)=/i;
let hashCarriedAuthCallback =
  typeof window !== 'undefined' && AUTH_CALLBACK_PARAM.test(`${window.location.hash}${window.location.search}`);

const readRoute = (): Route => {
  const hash = (typeof window === 'undefined' ? '' : window.location.hash).replace(/^#/, '').toLowerCase();
  // A callback fragment always belongs to the waiting list …
  if (AUTH_CALLBACK_PARAM.test(`#${hash}`)) return 'join';
  // … and so does the empty hash the auth client leaves behind right after it
  // has consumed a successful one, but only for that first navigation.
  if (hashCarriedAuthCallback && hash.length === 0) return 'join';
  if (hash.length > 0) hashCarriedAuthCallback = false;
  if (hash === 'avatar-diagnostic') return 'avatar-diagnostic';
  if (hash === 'diagnostics') return 'diagnostics';
  if (hash === 'avatar') return 'avatar';
  if (hash === 'live') return 'live';
  if (hash === 'join') return 'join';
  return 'welcome';
};

const NAV_PAGES: { id: SignVoxPage; label: string; icon: string }[] = [
  { id: 'welcome', label: 'Home', icon: 'home' },
  { id: 'live', label: 'Live', icon: 'videocam' },
  { id: 'avatar', label: 'Avatar', icon: 'accessibility_new' },
  { id: 'join', label: 'Join', icon: 'mail' },
];

export default function App() {
  const [route, setRoute] = useState<Route>(readRoute);
  // All public pages share one engine binding so the camera stream, recognition
  // state and loaded avatar survive navigation. The internal screens keep their
  // own binding so the renderer is never left inside an unmounted page.
  const engine = useSignVoxEngine(route === 'diagnostics' ? 'diagnostics' : route === 'avatar-diagnostic' ? 'none' : 'product');

  useEffect(() => {
    const syncRoute = () => {
      setRoute(readRoute());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener('hashchange', syncRoute);
    return () => window.removeEventListener('hashchange', syncRoute);
  }, []);

  // Internal engineering screens: preserved behaviour, never in the product nav.
  if (route === 'avatar-diagnostic') return <AvatarDiagnostic />;
  if (route === 'diagnostics') return <DiagnosticDashboard engine={engine} />;

  const liveStatus = deriveLiveStatus({
    status: engine.status,
    error: engine.error,
    isActive: engine.activeRef.current,
    bufferReady: Boolean(engine.metrics?.sequenceStatus?.isReady),
    bufferProgress: engine.metrics?.sequenceStatus?.progressPercent ?? 0,
  });

  const navigate = (page: SignVoxPage) => {
    window.location.hash = page;
  };

  const isPublic = route === 'welcome' || route === 'live' || route === 'avatar' || route === 'join';

  return (
    <div className="flex min-h-[100dvh] flex-col bg-surface text-on-surface">
      <SignVoxHeader
        status={liveStatus.label}
        activePage={isPublic ? route : undefined}
        onNavigate={navigate}
        transcriptCount={engine.transcript.length}
        onOpenTranscript={engine.focusTranscript}
      />

      {/* Product pages stay mounted: the camera stream, landmark pipeline,
          recognition state and the loaded GLB avatar all survive navigation. */}
      <main className="mx-auto w-full max-w-[1400px] flex-1 px-6 pt-5 pb-32">
        <WelcomePage active={route === 'welcome'} onNavigate={navigate} />
        <LiveTranslationPage engine={engine} active={route === 'live'} />
        <AvatarStudioPage engine={engine} active={route === 'avatar'} />
        <JoinPage active={route === 'join'} />
      </main>

      {/* The floating island bar is the single navigation surface, at every
          screen size, so the shell looks the same on a phone and a desktop.
          It scales with the viewport and never shows a scrollbar. */}
      <nav aria-label="Primary" className="fixed inset-x-0 bottom-0 z-40 flex justify-center px-4 pb-safe">
        <div className="svx-floating-bar no-scrollbar mb-1 flex w-[min(100%,30rem)] items-center gap-1 overflow-x-auto rounded-[1.35rem] p-1">
          {NAV_PAGES.map((page) => {
            const isActive = page.id === route;
            return (
              <button
                key={page.id}
                type="button"
                onClick={() => navigate(page.id)}
                aria-current={isActive ? 'page' : undefined}
                className={`svx-nav-item ${isActive ? 'svx-nav-item-active' : ''}`}
              >
                <span className="svx-icon text-[1.375rem]">{page.icon}</span>
                {page.label}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
