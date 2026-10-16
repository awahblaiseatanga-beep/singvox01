import { describe, it, expect } from 'vitest';
import { LatencyProfiler } from '../lib/latencyProfiler';

describe('LatencyProfiler', () => {
  it('computes accurate median, p95, min, and max', () => {
    // 20 evenly spaced samples: 5, 10, 15, ..., 100
    const values = Array.from({ length: 20 }, (_, i) => (i + 1) * 5);
    const stats = LatencyProfiler.computeStats(values);

    expect(stats.count).toBe(20);
    expect(stats.min).toBe(5);
    expect(stats.max).toBe(100);
    // Median of 20 elements (average of 10th and 11th elements: 50 and 55) = 52.5
    expect(stats.median).toBe(52.5);
    // p95 index is floor(20 * 0.95) = 19 (100)
    expect(stats.p95).toBe(100);
  });

  it('handles empty samples safely', () => {
    const stats = LatencyProfiler.computeStats([]);
    expect(stats.count).toBe(0);
    expect(stats.median).toBe(0);
    expect(stats.p95).toBe(0);
  });

  it('records samples and generates steady-state report', () => {
    const profiler = new LatencyProfiler();
    for (let i = 1; i <= 30; i++) {
      profiler.recordSample('mediaPipeDetect', i * 2);
      profiler.recordSample('featureExtraction', 0.5);
      profiler.recordSample('v2Normalization', 0.2);
      profiler.recordSample('onnxInference', 45);
    }

    const report = profiler.getSteadyStateReport();
    expect(report.mediaPipeDetect.count).toBe(30);
    expect(report.featureExtraction.median).toBe(0.5);
    expect(report.v2Normalization.median).toBe(0.2);
    expect(report.onnxInference.median).toBe(45);
  });
});
