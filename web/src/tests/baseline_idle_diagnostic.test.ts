import { describe, it, expect } from 'vitest';
import { TemporalStabilizer, BASELINE_STABILIZER_CONFIG } from '../lib/temporalStabilizer';

/**
 * Idle-suppression regression tests for the 79-class baseline thresholds.
 *
 * History: this file previously asserted `expect(commits.length).toBeGreaterThan(0)`
 * to "prove" that the low baseline `minimumConfidence` let idle noise commit a
 * sign. That assertion failed, and the measurement in
 * docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md shows why: a fluctuating 0.06/0.30
 * trace averages to ~0.11 time-weighted evidence, below the 0.25 commit
 * threshold. The correct expectation is therefore the opposite one — idle noise
 * must NOT commit — and it is asserted explicitly here.
 */
describe('Baseline stabilizer: idle suppression and commit reachability', () => {
  it('does not commit from fluctuating idle noise under the baseline thresholds', () => {
    const stab = new TemporalStabilizer({ ...BASELINE_STABILIZER_CONFIG, minimumConfidence: 0.05 });
    const commits: string[] = [];

    // Idle: one class hovers at 6% with occasional 30% spikes for 6 seconds.
    for (let i = 0; i < 60; i += 1) {
      const confidence = i % 5 === 0 ? 0.3 : 0.06;
      const state = stab.process({ classIndex: 14, className: 'ME', confidence, timestampMs: i * 100 });
      if (state.committedSign) commits.push(state.committedSign);
    }

    expect(commits).toEqual([]);
  });

  it('still commits a genuinely held sign under the baseline thresholds', () => {
    const stab = new TemporalStabilizer(BASELINE_STABILIZER_CONFIG);
    const commits: string[] = [];

    // A real sign held steady: 2 seconds at 90% confidence.
    for (let i = 0; i < 20; i += 1) {
      const state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.9, timestampMs: i * 100 });
      if (state.committedSign) commits.push(state.committedSign);
    }

    expect(commits).toEqual(['HELLO']);
  });

  it('rejects a single-frame confidence spike regardless of its height', () => {
    const stab = new TemporalStabilizer(BASELINE_STABILIZER_CONFIG);
    const commits: string[] = [];

    for (let i = 0; i < 12; i += 1) {
      const confidence = i === 6 ? 0.95 : 0.02;
      const state = stab.process({ classIndex: 7, className: 'WAIT', confidence, timestampMs: i * 100 });
      if (state.committedSign) commits.push(state.committedSign);
    }

    expect(commits).toEqual([]);
  });

  it('passes an unmapped class through unchanged so the UI can show it', () => {
    const stab = new TemporalStabilizer({ ...BASELINE_STABILIZER_CONFIG, minimumConfidence: 0.05 });
    const state = stab.process({ classIndex: 99, className: 'UNKNOWN', confidence: 0.8, timestampMs: 100 });
    expect(state.rawPrediction.className).toBe('UNKNOWN');
  });
});
