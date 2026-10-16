import React from 'react';
import { FEATURE_DIMENSION } from '../lib/contracts';
import { mediaPipeConfig } from '../lib/mediapipe';
import { HandOverlay } from './HandOverlay';
import { SignVoxHeader } from './SignVoxHeader';
import type { SignVoxEngine } from '../engine/useSignVoxEngine';

/**
 * Internal engineering dashboard: landmark pipeline stats, cadence profiling, the
 * latency profiler, the Phase 1.1 consistency lab, tensor snapshots and the
 * synthetic ONNX test. Moved verbatim out of the old App.tsx and reachable only
 * through the `#diagnostics` hash route (or `#avatar-diagnostic` for the avatar
 * suite) so it never appears in the ordinary two-page product navigation.
 */
export function DiagnosticDashboard({ engine }: { engine: SignVoxEngine }) {
  const {
    status, avatarStatus, transcript, setTranscript, error,
    metrics, snapshot, syntheticTest, liveResult, activeModel, setActiveModel, activeModelSpec, avatarClipLabels,
    videoRef, avatarCanvasRef, avatarCtrlRef, latestDetection, stableState,
    showSkeleton, setShowSkeleton,
    start, stop, activeRef, captureNextRef, runSyntheticTest,
    autoSpeak, toggleAutoSpeak, speakLatest, isSpeechSupported, stopSpeaking,
    hearingState, recognizerRef, spokenText, setSpokenText, interimSpokenText,
    handleRunRepeatability, runningRepeatability, repeatabilityReport, inferenceSessionRef,
    coldStartReport, steadyStateReport, diagnosticNotice, diagnosticTrials,
    targetLabelInput, setTargetLabelInput, handleRecordTrial, handleExportSession, handleClearSession,
    frame, mark, focusTranscript,
  } = engine;

  return <div className="svx-diag">
    <SignVoxHeader
      variant="dark"
      status={status}
      avatarStatus={avatarStatus}
      transcriptCount={transcript.length}
      onOpenTranscript={focusTranscript}
    />
    <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '1rem' }}>
    <header style={{ marginBottom: '1rem' }}>
      <p className="eyebrow" style={{ color: '#4f46e5', fontWeight: 'bold', margin: 0 }}>SIGNVOX PILOT PROTOTYPE</p>
      <h1 style={{ margin: '0.2rem 0' }}>Live Recognition & 3D Avatar</h1>
      <p style={{ opacity: 0.8, margin: 0 }}>
        Active model: <strong>{activeModelSpec.displayName}</strong>
        {' · '}
        Scope: <strong>{activeModelSpec.scopeChip}</strong>
        {' · '}
        Avatar clips: <strong>{avatarClipLabels().length > 0 ? avatarClipLabels().join(', ') : 'loading'}</strong>
        {' · '}
        MediaPipe assets: <strong>{mediaPipeConfig.poseModelUrl.includes('storage.googleapis.com') ? 'development URLs' : 'configured artifact host'}</strong>
      </p>
      <p style={{ opacity: 0.7, margin: '0.2rem 0 0' }}>{activeModelSpec.scopeDetail}</p>
      <ul style={{ opacity: 0.7, margin: '0.2rem 0 0', paddingLeft: '1.1rem', fontSize: '0.85rem' }}>
        {activeModelSpec.notes.map((note) => <li key={note}>{note}</li>)}
      </ul>
    </header>

    {/* SIDE-BY-SIDE MAIN CONTAINER */}
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
      {/* LEFT COLUMN: CAMERA & CONTROLS */}
      <section className="camera-panel" style={{ background: '#111', borderRadius: '12px', padding: '1rem', border: '1px solid #333' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#93c5fd' }}>Signer Camera Input</h3>
        <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: '8px', overflow: 'hidden' }}>
          <video ref={videoRef} muted playsInline className="mirrored-preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          <HandOverlay
            videoRef={videoRef}
            rawDetection={latestDetection}
            liveResult={liveResult}
            stableState={stableState}
            isBuffering={!metrics?.sequenceStatus?.isReady}
            bufferProgress={metrics?.sequenceStatus?.progressPercent ?? 0}
            showSkeleton={showSkeleton}
          />
        </div>
        <div className="camera-note" style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.4rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Preview is mirrored for signer comfort; MediaPipe receives unmirrored raw frames.</span>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', opacity: 0.85 }}>
            <input type="checkbox" checked={showSkeleton} onChange={(e) => setShowSkeleton(e.target.checked)} />
            <span>Show Skeleton</span>
          </label>
        </div>

        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>Model Selection:</label>
          <select 
            value={activeModel} 
            onChange={(e) => {
               const val = e.target.value as 'pilot' | 'baseline';
               setActiveModel(val);
               if (activeRef.current) {
                  stop();
               }
            }}
            style={{ padding: '0.3rem 0.6rem', borderRadius: '6px', background: '#222', color: '#fff', border: '1px solid #555' }}
          >
            <option value="pilot">3-Class Pilot ONNX (HELLO, YES, NO) — fallback</option>
            <option value="baseline">79-Class Baseline ONNX (SPOTER V2) — default</option>
          </select>
        </div>

        <div className="controls" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1rem' }}>
          <button onClick={start} disabled={activeRef.current} style={{ padding: '0.5rem 1rem', background: '#2563eb', color: '#fff', borderRadius: '6px', border: 'none', cursor: 'pointer' }}>Start Camera</button>
          <button onClick={stop} disabled={!activeRef.current} style={{ padding: '0.5rem 1rem', background: '#dc2626', color: '#fff', borderRadius: '6px', border: 'none', cursor: 'pointer' }}>Stop</button>
          <button onClick={() => { captureNextRef.current = true; }} style={{ padding: '0.5rem 0.8rem' }}>Capture Diagnostic Frame</button>
          <button onClick={runSyntheticTest} style={{ padding: '0.5rem 0.8rem' }}>Run Synthetic ONNX Test</button>
          <button onClick={() => { window.location.hash = '#avatar-diagnostic'; }} style={{ padding: '0.5rem 0.8rem' }}>Avatar Test Suite</button>
        </div>
      </section>

      {/* RIGHT COLUMN: 3D AVATAR CANVAS */}
      <section style={{ background: '#111827', borderRadius: '12px', padding: '1rem', border: '1px solid #374151', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: '#a7f3d0' }}>ASL Avatar Playback</h3>
          <span style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: avatarStatus === 'Ready' ? '#065f46' : '#991b1b', color: '#fff' }}>
            {avatarStatus}
          </span>
        </div>
        <div ref={avatarCanvasRef} style={{ width: '100%', height: '420px', borderRadius: '8px', overflow: 'hidden', background: '#181824' }} />
        <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', opacity: 0.7, textAlign: 'center' }}>
          Current Mode: {avatarCtrlRef.current?.animationMode || 'ASL_NEUTRAL'}
        </div>
      </section>
    </div>

    {/* SPEECH & HEARING CONTROLS */}
    <section className="speech-controls" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem', padding: '0.8rem', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', border: '1px solid #333' }}>
      <h3 style={{ margin: 0, fontSize: '0.9rem', opacity: 0.8 }}>Speech Synthesis</h3>
      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={autoSpeak} onChange={toggleAutoSpeak} disabled={!isSpeechSupported()} />
          Auto-Speak Recognized Signs
      </label>
      <button onClick={speakLatest} disabled={!isSpeechSupported() || transcript.length === 0} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>Speak Latest</button>
      <button onClick={stopSpeaking} disabled={!isSpeechSupported()} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>Stop Speaking</button>
      <span style={{ fontSize: '0.8rem', opacity: 0.6, marginLeft: 'auto' }}>
          {isSpeechSupported() ? "Web Speech API Active" : "Web Speech API Unsupported"}
      </span>
    </section>

    <section className="hearing-controls" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem', padding: '0.8rem', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', border: '1px solid #333' }}>
      <h3 style={{ margin: 0, fontSize: '0.9rem', opacity: 0.8 }}>Hearing Input Speech-to-ASL</h3>
      <button onClick={() => recognizerRef.current?.start()} disabled={hearingState === 'listening' || hearingState === 'unsupported'} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>🎤 Start Listening</button>
      <button onClick={() => recognizerRef.current?.stop()} disabled={hearingState !== 'listening'} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>⏹ Stop Listening</button>
      <span style={{ fontSize: '0.8rem', opacity: 0.6, marginLeft: 'auto', textTransform: 'capitalize' }}>
          Status: {hearingState}
      </span>
      <div style={{ width: '100%', marginTop: '0.5rem', minHeight: '1.5rem' }}>
          {spokenText.length > 0 && <button onClick={() => setSpokenText([])} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', float: 'right' }}>Clear</button>}
          {spokenText.map(t => (
            <div key={t.id} style={{ marginBottom: '0.5rem', padding: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
               <span style={{ display: 'block', fontSize: '0.9rem', opacity: 0.8, color: '#aaccff' }}>Source: "{t.text}"</span>
               {t.asl && (
                   <div style={{ marginTop: '0.3rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                     <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>ASL sequence:</span>
                     {t.asl.tokens.map((tok, i) => (
                        <React.Fragment key={i}>
                            {i > 0 && <span style={{ opacity: 0.5 }}>→</span>}
                            <span 
                                onClick={() => {
                                   if (tok.supported && tok.canonicalName && avatarCtrlRef.current) {
                                      avatarCtrlRef.current.playSignByLabel(tok.canonicalName);
                                   }
                                }}
                                style={{ 
                                    padding: '0.2rem 0.5rem', 
                                    background: tok.supported ? 'rgba(0,255,0,0.2)' : 'rgba(255,0,0,0.2)',
                                    color: tok.supported ? '#88ff88' : '#ff8888',
                                    borderRadius: '4px',
                                    fontSize: '0.85rem',
                                    border: `1px solid ${tok.supported ? '#006600' : '#660000'}`,
                                    cursor: tok.supported ? 'pointer' : 'default',
                                    textTransform: 'uppercase'
                                }}
                                title={tok.supported ? 'Click to play avatar animation' : 'Unsupported sign'}
                            >
                                {tok.supported ? tok.canonicalName : `${tok.sourceWord} [unsupported]`}
                            </span>
                        </React.Fragment>
                     ))}
                   </div>
               )}
            </div>
          ))}
          {interimSpokenText && <span style={{ display: 'block', fontSize: '1rem', opacity: 0.6, fontStyle: 'italic', color: '#88ccff' }}>{interimSpokenText} ...</span>}
      </div>
    </section>

    {error && <p className="error" style={{ padding: '0.8rem', background: '#991b1b', color: '#fff', borderRadius: '6px' }}>{error}</p>}

    <section className="grid">
      <article>
        <h2>Landmarks & Input Pipeline</h2>
        <p>Pose {mark(frame?.presence.pose)} · 33×5</p>
        <p>Left hand {mark(frame?.presence.leftHand)} · 21×3</p>
        <p>Right hand {mark(frame?.presence.rightHand)} · 21×3</p>
        <p>Face {mark(frame?.presence.face)} · first 25×3</p>
        <p>Vector {frame?.raw.length === FEATURE_DIMENSION ? '366 dimensions ✓' : 'waiting'}</p>
        <p>V2 normalization {metrics ? '✓' : 'waiting'}</p>
        <p>Sequence buffer: {metrics?.sequenceStatus ? `${metrics.sequenceStatus.length}/${metrics.sequenceStatus.capacity} frames (${metrics.sequenceStatus.isReady ? '✓ Ready' : `Buffering ${metrics.sequenceStatus.progressPercent}%`})` : '0/60 frames (Buffering)'}</p>
        <p>NaN/Inf {metrics ? `${metrics.normalizedFinite.nan}/${metrics.normalizedFinite.inf}` : '—'}</p>
      </article>
      <article><h2>Cadence Profiling</h2>
        <p>Camera FPS: {metrics?.cameraFps.toFixed(1) ?? '—'}</p>
        <p>Buffer frames/s (125 ms grid, target 8): {metrics?.processingFps.toFixed(1) ?? '—'}</p>
        <p>Landmark observations/s: {metrics?.observationFps.toFixed(1) ?? '—'}</p>
        <p>Newest buffer frame: {metrics ? (metrics.interpolated ? 'interpolated between two observations' : 'direct observation') : '—'}</p>
        <p>Overall Latency: {metrics?.overallLatencyMs.toFixed(1) ?? '—'} ms</p>
        <p style={{marginLeft: '10px', fontSize: '0.9em', opacity: 1}}>└ MediaPipe (Total): {metrics?.mpLatencyMs.toFixed(1) ?? '—'} ms</p>
        <p style={{marginLeft: '20px', fontSize: '0.85em', opacity: 0.8}}>├ Pose: {metrics?.mpPoseMs?.toFixed(1) ?? '—'} ms</p>
        <p style={{marginLeft: '20px', fontSize: '0.85em', opacity: 0.8}}>├ Hands: {metrics?.mpHandsMs?.toFixed(1) ?? '—'} ms</p>
        <p style={{marginLeft: '20px', fontSize: '0.85em', opacity: 0.8}}>└ Face: {metrics?.mpFaceMs?.toFixed(1) ?? '—'} ms</p>
        <p style={{marginLeft: '10px', fontSize: '0.9em', opacity: 1}}>└ Delegate (pose/hands/face): {metrics?.mpDelegate ?? '—'}</p>
        <p style={{marginLeft: '10px', fontSize: '0.9em', opacity: 1}}>└ FeatureVec: {metrics?.featureLatencyMs.toFixed(1) ?? '—'} ms</p>
        <p style={{marginLeft: '10px', fontSize: '0.9em', opacity: 1}}>└ Normalization: {metrics?.normLatencyMs.toFixed(1) ?? '—'} ms</p>
        <p>Dropped Frames: {metrics?.dropped ?? 0}</p>
        <p>Invalid groups: {frame?.invalidGroups.length ?? 0}</p>
      </article>
      <article><h2>Hand mapping</h2>{frame?.handAssignments.length ? frame.handAssignments.map((assignment, index) => <p key={`${assignment.mediaPipeLabel}-${index}`}>MediaPipe {assignment.mediaPipeLabel} → {assignment.canonicalSlot}</p>) : <p>Show one hand at a time, then use Capture diagnostic frame.</p>}</article>
    </section>

    {snapshot && <section className="snapshot"><h2>Captured diagnostic frame</h2><pre>{JSON.stringify(snapshot, null, 2)}</pre></section>}
    
    {syntheticTest && <section className="snapshot">
      <h2>Synthetic ONNX Diagnostic</h2>
      <p>ONNX Runtime: {syntheticTest.passed ? 'PASS' : 'FAIL'}</p>
      <p>Execution provider: {syntheticTest.provider.toUpperCase()}</p>
      <p>Input: [1,60,366]</p>
      <p>Output: {syntheticTest.logits.length} logits</p>
      <p>Top prediction: {syntheticTest.topK[0]?.className} ({syntheticTest.topK[0]?.classIndex})</p>
      <p>Inference latency: {syntheticTest.latencyMs.toFixed(1)} ms</p>
      <p>No NaN: {syntheticTest.nan === 0 ? 'PASS' : 'FAIL'}</p>
      <p>No Inf: {syntheticTest.inf === 0 ? 'PASS' : 'FAIL'}</p>
    </section>}

    {liveResult && <section className="snapshot live-prediction">
      <h2>Live Model Predictions (Diagnostic)</h2>
      <p style={{ margin: '0 0 0.4rem 0', fontSize: '0.85rem', color: '#94a3b8' }}>
        Active Model: <strong>{activeModelSpec.displayName}</strong> · Latency: <strong>{liveResult.latencyMs.toFixed(1)} ms</strong>
      </p>
      <p style={{ margin: '0 0 0.6rem 0', fontSize: '0.75rem', color: '#f59e0b', fontStyle: 'italic' }}>
        Note: Softmax scores represent uncalibrated relative model output, not true posterior certainty.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {liveResult.topK.slice(0, 3).map((item, idx) => (
          <div
            key={`${item.classIndex}-${idx}`}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.4rem 0.6rem',
              borderRadius: '6px',
              background: idx === 0 ? 'rgba(37, 99, 235, 0.25)' : 'rgba(255, 255, 255, 0.04)',
              border: idx === 0 ? '1px solid rgba(59, 130, 246, 0.6)' : '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <span>
              <span style={{ opacity: 0.7, marginRight: '0.4rem' }}>#{idx + 1}</span>
              <strong>{item.className}</strong>
              <span style={{ opacity: 0.5, fontSize: '0.75rem', marginLeft: '0.4rem' }}>(id: {item.classIndex})</span>
            </span>
            <span style={{ fontFamily: 'monospace', fontWeight: idx === 0 ? 'bold' : 'normal' }}>
              {(item.confidence * 100).toFixed(1)}% <span style={{ opacity: 0.6, fontSize: '0.75rem' }}>({item.confidence.toFixed(3)})</span>
            </span>
          </div>
        ))}
      </div>
    </section>}

    {/* Pipeline Latency Profiler Panel */}
    <section className="snapshot" style={{ marginTop: '1.5rem', background: '#0a0f1d', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem', borderBottom: '1px solid #1e293b', paddingBottom: '0.5rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.05rem', color: '#38bdf8' }}>Pipeline Latency Profiler (10 Stages)</h2>
        <span style={{ fontSize: '0.75rem', background: '#1e293b', color: '#94a3b8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
          Cold-Start vs Steady-State
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Cold Start Metrics */}
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '6px', border: '1px solid #1e293b' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#f59e0b' }}>Cold-Start Timings (Initial Launch)</h3>
          <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
            <tbody>
              <tr><td style={{ color: '#94a3b8', padding: '3px 0' }}>1. Camera & Video Readiness:</td><td style={{ textAlign: 'right', fontWeight: 'bold' }}>{coldStartReport.cameraPermissionAndReadyMs ? `${coldStartReport.cameraPermissionAndReadyMs.toFixed(0)} ms` : '—'}</td></tr>
              <tr><td style={{ color: '#94a3b8', padding: '3px 0' }}>2. MediaPipe Initialization:</td><td style={{ textAlign: 'right', fontWeight: 'bold' }}>{coldStartReport.mediaPipeInitMs ? `${coldStartReport.mediaPipeInitMs.toFixed(0)} ms` : '—'}</td></tr>
              <tr><td style={{ color: '#94a3b8', padding: '3px 0' }}>3. First Hand Visible → Render:</td><td style={{ textAlign: 'right', fontWeight: 'bold', color: '#10b981' }}>{coldStartReport.firstHandVisibleToRenderMs ? `${coldStartReport.firstHandVisibleToRenderMs.toFixed(0)} ms` : '—'}</td></tr>
              <tr><td style={{ color: '#94a3b8', padding: '3px 0' }}>6. ONNX Model Initialization:</td><td style={{ textAlign: 'right', fontWeight: 'bold' }}>{coldStartReport.onnxInitMs ? `${coldStartReport.onnxInitMs.toFixed(0)} ms` : '—'}</td></tr>
              <tr><td style={{ color: '#94a3b8', padding: '3px 0' }}>6b. ONNX Kernel Warmup:</td><td style={{ textAlign: 'right', fontWeight: 'bold' }}>{coldStartReport.onnxFirstInferenceMs ? `${coldStartReport.onnxFirstInferenceMs.toFixed(0)} ms` : '—'}</td></tr>
              <tr><td style={{ color: '#94a3b8', padding: '3px 0' }}>8. Sequence Buffer Readiness (60f):</td><td style={{ textAlign: 'right', fontWeight: 'bold' }}>{coldStartReport.bufferWarmupMs ? `${coldStartReport.bufferWarmupMs.toFixed(0)} ms` : '—'}</td></tr>
            </tbody>
          </table>
        </div>

        {/* Steady State Metrics */}
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '6px', border: '1px solid #1e293b' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#38bdf8' }}>Steady-State Timings (Median / P95)</h3>
          <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: '#64748b', borderBottom: '1px solid #334155' }}>
                <th style={{ textAlign: 'left', padding: '2px 0' }}>Stage</th>
                <th style={{ textAlign: 'right', padding: '2px 4px' }}>Median</th>
                <th style={{ textAlign: 'right', padding: '2px 4px' }}>P95</th>
                <th style={{ textAlign: 'right', padding: '2px 0' }}>Samples</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(steadyStateReport).map(([stage, s]) => (
                <tr key={stage} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ color: '#94a3b8', padding: '2px 0' }}>{stage}</td>
                  <td style={{ textAlign: 'right', padding: '2px 4px', fontWeight: 'bold' }}>{s.count > 0 ? `${s.median}ms` : '—'}</td>
                  <td style={{ textAlign: 'right', padding: '2px 4px' }}>{s.count > 0 ? `${s.p95}ms` : '—'}</td>
                  <td style={{ textAlign: 'right', padding: '2px 0', opacity: 0.6 }}>{s.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    {/* Phase 1.1 Consistency Diagnostic Lab */}
    <section className="snapshot" style={{ marginTop: '1.5rem', background: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem', borderBottom: '1px solid #1e293b', paddingBottom: '0.5rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.05rem', color: '#38bdf8' }}>Phase 1.1 Consistency Diagnostic Lab</h2>
        <span style={{ fontSize: '0.75rem', background: '#1e293b', color: '#94a3b8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
          Diagnostic Isolation Mode
        </span>
      </div>

      {diagnosticNotice && (
        <div style={{ padding: '0.4rem 0.6rem', marginBottom: '0.8rem', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', fontSize: '0.8rem' }}>
          {diagnosticNotice}
        </div>
      )}

      {/* Investigation A: Identical-Input Repeatability */}
      <div style={{ marginBottom: '1.2rem', padding: '0.8rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', border: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h3 style={{ margin: 0, fontSize: '0.9rem', color: '#e2e8f0' }}>A. Identical-Input Repeatability (10 Inference Runs)</h3>
          <button
            onClick={handleRunRepeatability}
            disabled={!metrics?.sequenceStatus?.isReady || runningRepeatability || !inferenceSessionRef.current}
            style={{ fontSize: '0.8rem', padding: '0.3rem 0.7rem', cursor: metrics?.sequenceStatus?.isReady ? 'pointer' : 'not-allowed', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px' }}
          >
            {runningRepeatability ? 'Running 10x…' : 'Run 10x Repeatability Test'}
          </button>
        </div>
        <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: '#94a3b8' }}>
          Copies current 60×366 tensor once; reuses exact Float32Array across 10 sequential inference calls without MediaPipe or normalization.
        </p>

        {repeatabilityReport && (
          <div style={{ marginTop: '0.5rem', padding: '0.6rem', borderRadius: '4px', background: repeatabilityReport.isRepeatable ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: repeatabilityReport.isRepeatable ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', fontSize: '0.85rem', color: repeatabilityReport.isRepeatable ? '#4ade80' : '#f87171' }}>
              <span>{repeatabilityReport.isRepeatable ? '✓ DETERMINISTIC REPEATABILITY PASS' : '✗ NON-DETERMINISTIC REPEATABILITY'}</span>
              <span>Max Logit Δ: {repeatabilityReport.maxLogitDeviation.toExponential(2)}</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.3rem' }}>
              Latency: min {repeatabilityReport.latencyStats.minMs}ms · avg {repeatabilityReport.latencyStats.avgMs}ms · max {repeatabilityReport.latencyStats.maxMs}ms | Tolerance: {repeatabilityReport.tolerance}
            </div>
            <div style={{ marginTop: '0.4rem', maxHeight: '120px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ color: '#64748b', borderBottom: '1px solid #334155' }}>
                    <th style={{ padding: '2px 4px' }}>Run</th>
                    <th style={{ padding: '2px 4px' }}>Top Class</th>
                    <th style={{ padding: '2px 4px' }}>Conf %</th>
                    <th style={{ padding: '2px 4px' }}>Logit Δ</th>
                    <th style={{ padding: '2px 4px' }}>Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {repeatabilityReport.runs.map((r) => (
                    <tr key={r.runIndex} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '2px 4px' }}>#{r.runIndex}</td>
                      <td style={{ padding: '2px 4px' }}>{r.topClassName} ({r.topClassIndex})</td>
                      <td style={{ padding: '2px 4px' }}>{(r.topConfidence * 100).toFixed(1)}%</td>
                      <td style={{ padding: '2px 4px', fontFamily: 'monospace' }}>{r.maxLogitDiffFromRun1.toExponential(1)}</td>
                      <td style={{ padding: '2px 4px' }}>{r.latencyMs} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Investigation B: Input Quality & Cadence */}
      <div style={{ marginBottom: '1.2rem', padding: '0.8rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', border: '1px solid #1e293b' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: '#e2e8f0' }}>B. Input Quality & Cadence (Current 60-Frame Window)</h3>
        {metrics?.sequenceQuality ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', marginBottom: '0.5rem', fontSize: '0.75rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.35rem 0.5rem', borderRadius: '4px' }}>
                <span style={{ color: '#94a3b8' }}>Left Hand: </span>
                <strong style={{ color: metrics.sequenceQuality.lhPercent > 0 ? '#38bdf8' : '#64748b' }}>{metrics.sequenceQuality.lhPercent}%</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.35rem 0.5rem', borderRadius: '4px' }}>
                <span style={{ color: '#94a3b8' }}>Right Hand: </span>
                <strong style={{ color: metrics.sequenceQuality.rhPercent > 0 ? '#38bdf8' : '#64748b' }}>{metrics.sequenceQuality.rhPercent}%</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.35rem 0.5rem', borderRadius: '4px' }}>
                <span style={{ color: '#94a3b8' }}>Pose: </span>
                <strong style={{ color: metrics.sequenceQuality.posePercent === 100 ? '#4ade80' : '#f59e0b' }}>{metrics.sequenceQuality.posePercent}%</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.35rem 0.5rem', borderRadius: '4px' }}>
                <span style={{ color: '#94a3b8' }}>Face: </span>
                <strong style={{ color: metrics.sequenceQuality.facePercent > 0 ? '#38bdf8' : '#64748b' }}>{metrics.sequenceQuality.facePercent}%</strong>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
              <span>Non-finite frames: <strong style={{ color: metrics.sequenceQuality.framesWithNonFinite === 0 ? '#4ade80' : '#f87171' }}>{metrics.sequenceQuality.framesWithNonFinite}</strong></span>
              <span>Duration: <strong>{metrics.sequenceQuality.durationMs} ms</strong></span>
              <span>Cadence: <strong>{metrics.sequenceQuality.avgIntervalMs} ± {metrics.sequenceQuality.intervalStdDevMs} ms/frame</strong></span>
            </div>
            <div style={{ fontSize: '0.72rem', background: 'rgba(0,0,0,0.2)', padding: '0.4rem', borderRadius: '4px', borderLeft: metrics.sequenceQuality.heuristicMovementCompleteness.isClippingSuspected ? '3px solid #f59e0b' : '3px solid #38bdf8' }}>
              <span style={{ color: '#94a3b8' }}>Movement profile (heuristic indicator): </span>
              <span style={{ color: metrics.sequenceQuality.heuristicMovementCompleteness.isClippingSuspected ? '#f59e0b' : '#cbd5e1' }}>
                {metrics.sequenceQuality.heuristicMovementCompleteness.note}
              </span>
            </div>
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b' }}>
            Buffering sequence ({metrics?.sequenceStatus?.length ?? 0}/60 frames)…
          </p>
        )}
      </div>

      {/* Investigation C: Controlled 5-Trial Live Session Recorder */}
      <div style={{ padding: '0.8rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', border: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h3 style={{ margin: 0, fontSize: '0.9rem', color: '#e2e8f0' }}>C. Controlled 5-Trial Sign Recorder</h3>
          <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>
            {diagnosticTrials.length}/5 Captured
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.6rem', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Sign Label (e.g. HELLO, YES, NO)"
            value={targetLabelInput}
            onChange={(e) => setTargetLabelInput(e.target.value)}
            style={{ flex: 1, padding: '0.3rem 0.5rem', fontSize: '0.8rem', background: '#020617', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }}
          />
          <button
            onClick={handleRecordTrial}
            disabled={!metrics?.sequenceStatus?.isReady || diagnosticTrials.length >= 5 || !liveResult}
            style={{ fontSize: '0.8rem', padding: '0.3rem 0.7rem', cursor: metrics?.sequenceStatus?.isReady && diagnosticTrials.length < 5 ? 'pointer' : 'not-allowed', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px' }}
          >
            Capture Trial ({diagnosticTrials.length}/5)
          </button>
          <button
            onClick={handleExportSession}
            disabled={diagnosticTrials.length === 0}
            style={{ fontSize: '0.8rem', padding: '0.3rem 0.7rem', cursor: diagnosticTrials.length > 0 ? 'pointer' : 'not-allowed', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '4px' }}
          >
            Export JSON
          </button>
          {diagnosticTrials.length > 0 && (
            <button
              onClick={handleClearSession}
              style={{ fontSize: '0.8rem', padding: '0.3rem 0.5rem', background: '#334155', color: '#94a3b8', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Reset
            </button>
          )}
        </div>

        {diagnosticTrials.length > 0 ? (
          <div style={{ maxHeight: '160px', overflowY: 'auto' }}>
            <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ color: '#64748b', borderBottom: '1px solid #334155' }}>
                  <th style={{ padding: '3px 4px' }}>#</th>
                  <th style={{ padding: '3px 4px' }}>Label</th>
                  <th style={{ padding: '3px 4px' }}>Top-1 Prediction</th>
                  <th style={{ padding: '3px 4px' }}>Top-2</th>
                  <th style={{ padding: '3px 4px' }}>Top-3</th>
                  <th style={{ padding: '3px 4px' }}>Hands (L/R)</th>
                  <th style={{ padding: '3px 4px' }}>Duration</th>
                  <th style={{ padding: '3px 4px' }}>Latency</th>
                </tr>
              </thead>
              <tbody>
                {diagnosticTrials.map((t) => (
                  <tr key={t.trialIndex} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '3px 4px' }}>{t.trialIndex}</td>
                    <td style={{ padding: '3px 4px', fontWeight: 'bold', color: '#38bdf8' }}>{t.targetLabel ?? '—'}</td>
                    <td style={{ padding: '3px 4px', color: '#e2e8f0' }}>
                      {t.top3[0]?.className} ({(t.top3[0]?.confidence * 100).toFixed(1)}%)
                    </td>
                    <td style={{ padding: '3px 4px', color: '#94a3b8' }}>
                      {t.top3[1]?.className} ({(t.top3[1]?.confidence * 100).toFixed(1)}%)
                    </td>
                    <td style={{ padding: '3px 4px', color: '#64748b' }}>
                      {t.top3[2]?.className} ({(t.top3[2]?.confidence * 100).toFixed(1)}%)
                    </td>
                    <td style={{ padding: '3px 4px' }}>
                      {t.quality.lhPercent}% / {t.quality.rhPercent}%
                    </td>
                    <td style={{ padding: '3px 4px' }}>{t.quality.durationMs}ms</td>
                    <td style={{ padding: '3px 4px' }}>{t.latencyMs}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b' }}>
            No trials recorded yet. Enter a sign label, perform the sign, and click "Capture Trial".
          </p>
        )}
      </div>
    </section>

    {stableState && <section className="snapshot live-recognition" id="signvox-transcript">
      <h2>Stabilized Sign Recognition & Avatar Target</h2>
      <p className="prediction-main">Current Sign: <b>{stableState.currentStableName || '—'}</b></p>
      <p>Stability: {(stableState.stabilityEvidence * 100).toFixed(1)}%</p>
      <p>Status: {stableState.status}</p>
      <div className="transcript-box" style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h3 style={{ margin: 0, fontSize: '0.8rem', opacity: 0.7, textTransform: 'uppercase' }}>Transcript</h3>
          {transcript.length > 0 && <button onClick={() => setTranscript([])} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}>Clear transcript</button>}
        </div>
        <p style={{ margin: 0, fontSize: '1.2rem', lineHeight: 1.5, wordSpacing: '4px' }}>
          {transcript.length ? transcript.map(t => t.displayText).join(' ') : 'Waiting for first sign...'}
        </p>
      </div>
    </section>}

    <footer style={{ marginTop: '2rem', textAlign: 'center', opacity: 0.6, fontSize: '0.8rem' }}>
      MediaPipe models: {mediaPipeConfig.poseModelUrl.includes('storage.googleapis.com') ? 'development URLs' : 'configured artifact host'}. No landmark frames are uploaded.
    </footer>
    </main>
  </div>;
}
