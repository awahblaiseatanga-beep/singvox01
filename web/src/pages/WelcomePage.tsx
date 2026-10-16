import React from 'react';
import type { SignVoxPage } from '../components/SignVoxHeader';

interface WelcomePageProps {
  active: boolean;
  onNavigate: (page: SignVoxPage) => void;
}

/**
 * Public landing page for the SingVox proof of concept.
 * Every capability claim here is grounded in the verified build: recognition
 * covers the 79-class SPOTER V2 baseline (ASL_VOCAB), avatar clips =
 * ASL_HELLO/ASL_NO/ASL_YES in SignVox_Female_Competition_Prototype.glb.
 */
export const WelcomePage: React.FC<WelcomePageProps> = ({ active, onNavigate }) => {
  if (!active) return null;
  return (
    <div className="flex flex-col gap-5">
      {/* ---------------- Hero ---------------- */}
      <section className="svx-card p-8">
        <p>
          <span className="svx-chip svx-chip-ok">
            <span className="svx-icon text-[0.8125rem]">science</span>
            Prototype — under development
          </span>
        </p>
        <h1 className="mt-4 text-[2.3rem] font-extrabold leading-tight tracking-tight">
          Sign language, live.
        </h1>
        <p className="mt-3 max-w-[38rem] text-[0.95rem] leading-relaxed text-on-surface-variant">
          SingVox is an experimental mobile-first experience being built to support
          communication between Deaf sign-language users and people who do not sign.
          Point your camera, sign, and see the translation as text — with optional
          speech output — while a 3D avatar signs back what you type.
        </p>
        <div className="mt-5 flex flex-row flex-wrap gap-2">
          <button type="button" onClick={() => onNavigate('live')} className="svx-btn-primary">
            <span className="svx-icon text-[1.25rem]">videocam</span>
            Try the live demo
          </button>
          <button type="button" onClick={() => onNavigate('avatar')} className="svx-btn-ghost">
            <span className="svx-icon text-[1.25rem]">accessibility_new</span>
            Meet the avatar
          </button>
          <button type="button" onClick={() => onNavigate('join')} className="svx-btn-ghost">
            <span className="svx-icon text-[1.25rem]">mail</span>
            Join the waiting list
          </button>
        </div>
      </section>

      {/* ---------------- Problem ---------------- */}
      <section className="svx-card p-8">
        <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
          The communication gap
        </h2>
        <p className="mt-3 max-w-[42rem] text-[0.92rem] leading-relaxed">
          Everyday conversations — at a clinic, a school, a market stall — break down when
          one person signs and the other does not, and no interpreter is available.
          SingVox is exploring whether on-device camera recognition plus a signing avatar
          can help bridge those moments. It is an early prototype, not a replacement for
          human interpreters, and it is not suitable for unvalidated medical or emergency
          communication.
        </p>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="svx-card p-8">
        <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
          How the prototype works
        </h2>
        <ol className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(15rem,1fr))] gap-3">
          {[
            { icon: 'videocam', title: '1. Show a sign', text: 'Your camera tracks hand, pose and face landmarks entirely on this device. Video never leaves your phone or computer.' },
            { icon: 'psychology', title: '2. Get a translation', text: 'A small on-device model reads the movement and shows the recognized sign as text — spoken aloud if you ask it to.' },
            { icon: 'accessibility_new', title: '3. Sign back', text: 'Type or speak a sentence in Avatar Studio and the 3D avatar performs the signs it currently knows.' },
          ].map((step) => (
            <li key={step.title} className="svx-card-muted rounded-clay-sm p-4">
              <span className="svx-icon text-[1.5rem] text-primary-bright">{step.icon}</span>
              <p className="mt-2 text-[0.9rem] font-bold">{step.title}</p>
              <p className="mt-1 text-[0.8rem] leading-relaxed text-on-surface-variant">{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ---------------- What works now ---------------- */}
      <section className="svx-card p-8">
        <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
          What works right now
        </h2>
        <ul className="mt-3 flex flex-col gap-2 text-[0.88rem]">
          <li className="flex items-start gap-2">
            <span className="svx-icon text-[1.125rem] text-emerald-600">check_circle</span>
            <span><strong>Live Translation:</strong> recognizes <strong>79 ASL-based signs</strong> from your camera, with text output and optional speech.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="svx-icon text-[1.125rem] text-emerald-600">check_circle</span>
            <span><strong>Avatar Studio:</strong> the 3D avatar performs <strong>HELLO, YES and NO</strong> from typed or spoken sentences.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="svx-icon text-[1.125rem] text-amber-600">hourglass_top</span>
            <span><strong>Still in development:</strong> avatar animations beyond HELLO, YES and NO (a GOOD animation exists as an isolated experiment, not in the app), steadier recognition, live-signer validation and lower-end device support. The prototype makes mistakes — please judge it as a starting point.</span>
          </li>
        </ul>
      </section>

      {/* ---------------- Language resources vision ---------------- */}
      <section className="svx-card p-8">
        <h2 className="text-[0.72rem] font-bold uppercase tracking-[0.14em] text-on-surface-variant">
          SingVox Language Resources — a developing initiative
        </h2>
        <p className="mt-3 max-w-[42rem] text-[0.92rem] leading-relaxed">
          Beyond the app, SingVox aims to work with Deaf communities, sign-language
          experts, researchers and relevant organizations to document, validate and
          responsibly structure sign-language resources relevant to Cameroon —
          understanding regional and professional variation, validating candidate signs
          with qualified reviewers, and exploring research partnerships and future data
          services under proper governance.
        </p>
        <p className="mt-3 max-w-[42rem] text-[0.82rem] leading-relaxed text-on-surface-variant">
          This initiative is just beginning. We do not yet hold a comprehensive,
          commercially licensable Cameroonian sign-language dataset, and the current
          prototype is ASL-based research software — not a validated model of
          Cameroonian sign language.
        </p>
        <div className="mt-4">
          <button type="button" onClick={() => onNavigate('join')} className="svx-btn-primary">
            <span className="svx-icon text-[1.25rem]">handshake</span>
            Partner with SingVox
          </button>
        </div>
      </section>
    </div>
  );
};
