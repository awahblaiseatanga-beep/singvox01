import { describe, it, expect } from 'vitest';
import {
  computeHandBoundingBox,
  mapPointToDisplay,
  mapNormalizedToDisplay,
  smoothBox,
  computeBadgePosition,
} from '../lib/overlayCoordinates';
import type { Point3 } from '../lib/contracts';

describe('overlayCoordinates utility tests', () => {
  describe('computeHandBoundingBox', () => {
    it('returns null for undefined or empty landmarks', () => {
      expect(computeHandBoundingBox(undefined)).toBeNull();
      expect(computeHandBoundingBox([])).toBeNull();
    });

    it('returns null if any coordinate contains NaN or Infinity', () => {
      const invalid: Point3[] = [
        { x: 0.5, y: 0.5, z: 0 },
        { x: NaN, y: 0.5, z: 0 },
      ];
      expect(computeHandBoundingBox(invalid)).toBeNull();
    });

    it('computes correct padded bounding box clamped to [0, 1]', () => {
      const landmarks: Point3[] = [
        { x: 0.2, y: 0.3, z: 0 },
        { x: 0.4, y: 0.6, z: 0 },
      ];
      const box = computeHandBoundingBox(landmarks, { paddingX: 0.05, paddingY: 0.05 });
      expect(box).not.toBeNull();
      expect(box!.minX).toBeCloseTo(0.15);
      expect(box!.maxX).toBeCloseTo(0.45);
      expect(box!.minY).toBeCloseTo(0.25);
      expect(box!.maxY).toBeCloseTo(0.65);
    });

    it('clamps bounding box edges to [0, 1] when near borders', () => {
      const landmarks: Point3[] = [
        { x: 0.01, y: 0.02, z: 0 },
        { x: 0.98, y: 0.99, z: 0 },
      ];
      const box = computeHandBoundingBox(landmarks, { paddingX: 0.05, paddingY: 0.05 });
      expect(box).not.toBeNull();
      expect(box!.minX).toBe(0);
      expect(box!.maxX).toBe(1);
      expect(box!.minY).toBe(0);
      expect(box!.maxY).toBe(1);
    });
  });

  describe('mapPointToDisplay & mapNormalizedToDisplay', () => {
    it('maps coordinates correctly for matching 16:9 video in 16:9 container', () => {
      const videoW = 1280;
      const videoH = 720;
      const containerW = 640;
      const containerH = 360;

      // In matching aspect ratio, scale = 0.5, offsetX = 0, offsetY = 0
      const pt = mapPointToDisplay({ x: 0.25, y: 0.5 }, videoW, videoH, containerW, containerH, false);
      expect(pt.x).toBeCloseTo(0.25 * 640);
      expect(pt.y).toBeCloseTo(0.5 * 360);

      // Mirrored: x=0.25 appears visually at (1 - 0.25) * 640 = 0.75 * 640
      const mirroredPt = mapPointToDisplay({ x: 0.25, y: 0.5 }, videoW, videoH, containerW, containerH, true);
      expect(mirroredPt.x).toBeCloseTo(0.75 * 640);
      expect(mirroredPt.y).toBeCloseTo(0.5 * 360);
    });

    it('maps normalized bounding box under single-mirroring correctly', () => {
      const box = { minX: 0.2, maxX: 0.4, minY: 0.3, maxY: 0.7 };
      const display = mapNormalizedToDisplay(box, 1280, 720, 1000, 562.5, true);

      // Under mirroring: left is at (1 - 0.4) * 1000 = 600, right is at (1 - 0.2) * 1000 = 800
      expect(display.x).toBeCloseTo(600);
      expect(display.width).toBeCloseTo(200); // 800 - 600
      expect(display.y).toBeCloseTo(0.3 * 562.5);
      expect(display.height).toBeCloseTo(0.4 * 562.5);
    });

    it('handles object-fit: cover aspect ratio cropping (4:3 camera in 16:9 container)', () => {
      const videoW = 640;
      const videoH = 480; // 4:3
      const containerW = 1280;
      const containerH = 720; // 16:9

      // Scale to cover 1280x720:
      // scale = max(1280/640=2, 720/480=1.5) = 2.0
      // renderedWidth = 1280, renderedHeight = 960 (cropped top and bottom by 120px)
      // offsetY = (720 - 960) / 2 = -120
      const centerPt = mapPointToDisplay({ x: 0.5, y: 0.5 }, videoW, videoH, containerW, containerH, false);
      expect(centerPt.x).toBeCloseTo(640);
      expect(centerPt.y).toBeCloseTo(-120 + 0.5 * 960); // = 360 (exact center of container!)
    });
  });

  describe('smoothBox', () => {
    it('returns target box directly when previous is null', () => {
      const target = { x: 100, y: 150, width: 80, height: 90 };
      expect(smoothBox(null, target)).toEqual(target);
    });

    it('interpolates with alpha parameter', () => {
      const prev = { x: 100, y: 100, width: 50, height: 50 };
      const target = { x: 200, y: 200, width: 100, height: 100 };
      const smoothed = smoothBox(prev, target, 0.5);

      expect(smoothed.x).toBeCloseTo(150);
      expect(smoothed.y).toBeCloseTo(150);
      expect(smoothed.width).toBeCloseTo(75);
      expect(smoothed.height).toBeCloseTo(75);
    });
  });

  describe('computeBadgePosition', () => {
    it('positions at top center when no hands are detected', () => {
      const pos = computeBadgePosition([], 800, 600, { badgeWidth: 160, badgeHeight: 32, margin: 10 });
      expect(pos.x).toBeCloseTo((800 - 160) / 2);
      expect(pos.y).toBe(10);
    });

    it('positions above single hand when clearance permits', () => {
      const hand = { x: 300, y: 250, width: 100, height: 120 };
      const pos = computeBadgePosition([hand], 800, 600, { badgeWidth: 140, badgeHeight: 30, margin: 10 });

      // Centered with hand: 300 + (100 - 140) / 2 = 280
      expect(pos.x).toBe(280);
      // Above hand: 250 - 30 - 10 = 210
      expect(pos.y).toBe(210);
    });

    it('repositions below single hand when top clearance is insufficient', () => {
      const handNearTop = { x: 300, y: 20, width: 100, height: 120 };
      const pos = computeBadgePosition([handNearTop], 800, 600, { badgeWidth: 140, badgeHeight: 30, margin: 10 });

      // Above would be 20 - 30 - 10 = -20 < margin. Repositions below:
      // Below hand: 20 + 120 + 10 = 150
      expect(pos.y).toBe(150);
      expect(pos.x).toBe(280);
    });

    it('positions centered between two hands above the highest hand', () => {
      const hand1 = { x: 200, y: 200, width: 80, height: 100 };
      const hand2 = { x: 500, y: 220, width: 80, height: 100 };
      const pos = computeBadgePosition([hand1, hand2], 800, 600, { badgeWidth: 140, badgeHeight: 30, margin: 10 });

      // Spans from 200 to 580: center is 200 + (380 - 140)/2 = 320
      expect(pos.x).toBe(320);
      // Highest hand is minY = 200: above is 200 - 30 - 10 = 160
      expect(pos.y).toBe(160);
    });

    it('repositions two-hand badge to unobstructed area when both hands are near top edge', () => {
      const hand1 = { x: 200, y: 15, width: 80, height: 100 };
      const hand2 = { x: 500, y: 25, width: 80, height: 100 };
      const pos = computeBadgePosition([hand1, hand2], 800, 600, { badgeWidth: 140, badgeHeight: 30, margin: 10 });

      // Above highest hand (15) is 15 - 30 - 10 = -25 < 10.
      // Repositions below lowest hand (25 + 100 = 125): below is 125 + 10 = 135
      expect(pos.y).toBe(135);
      expect(pos.x).toBe(320);
    });
  });
});
