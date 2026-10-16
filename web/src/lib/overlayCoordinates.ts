import type { Point3 } from './contracts';

export type NormalizedBox = {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
};

export type DisplayBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type BoundingBoxOptions = {
  paddingX?: number; // Normalized horizontal padding (default 0.04)
  paddingY?: number; // Normalized vertical padding (default 0.05)
};

/**
 * Computes a normalized bounding box around hand landmarks.
 * Returns null if landmarks are missing, empty, or contain non-finite numbers.
 */
export function computeHandBoundingBox(
  landmarks: Point3[] | undefined,
  options: BoundingBoxOptions = {}
): NormalizedBox | null {
  if (!landmarks || landmarks.length === 0) return null;

  const paddingX = options.paddingX ?? 0.04;
  const paddingY = options.paddingY ?? 0.05;

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;

  for (const pt of landmarks) {
    if (!Number.isFinite(pt.x) || !Number.isFinite(pt.y)) {
      return null;
    }
    if (pt.x < minX) minX = pt.x;
    if (pt.x > maxX) maxX = pt.x;
    if (pt.y < minY) minY = pt.y;
    if (pt.y > maxY) maxY = pt.y;
  }

  if (minX > maxX || minY > maxY) return null;

  // Apply padding and clamp to [0, 1]
  return {
    minX: Math.max(0, minX - paddingX),
    maxX: Math.min(1, maxX + paddingX),
    minY: Math.max(0, minY - paddingY),
    maxY: Math.min(1, maxY + paddingY),
  };
}

/**
 * Maps an unmirrored normalized coordinate (x, y) to displayed canvas pixels,
 * accounting for CSS `object-fit: cover` and optional horizontal mirroring (`scaleX(-1)`).
 */
export function mapPointToDisplay(
  point: { x: number; y: number },
  videoWidth: number,
  videoHeight: number,
  containerWidth: number,
  containerHeight: number,
  isMirrored = true
): { x: number; y: number } {
  if (videoWidth <= 0 || videoHeight <= 0 || containerWidth <= 0 || containerHeight <= 0) {
    return { x: 0, y: 0 };
  }

  // object-fit: cover scaling
  const scale = Math.max(containerWidth / videoWidth, containerHeight / videoHeight);
  const renderedWidth = videoWidth * scale;
  const renderedHeight = videoHeight * scale;
  const offsetX = (containerWidth - renderedWidth) / 2;
  const offsetY = (containerHeight - renderedHeight) / 2;

  // If the video is CSS-mirrored, unmirrored coordinate x appears visually at 1 - x
  const effectiveX = isMirrored ? 1.0 - point.x : point.x;

  return {
    x: offsetX + effectiveX * renderedWidth,
    y: offsetY + point.y * renderedHeight,
  };
}

/**
 * Maps a normalized bounding box to display canvas coordinates.
 * When isMirrored = true, minX maps to the right edge and maxX maps to the left edge visually.
 */
export function mapNormalizedToDisplay(
  box: NormalizedBox,
  videoWidth: number,
  videoHeight: number,
  containerWidth: number,
  containerHeight: number,
  isMirrored = true
): DisplayBox {
  if (videoWidth <= 0 || videoHeight <= 0 || containerWidth <= 0 || containerHeight <= 0) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }

  const scale = Math.max(containerWidth / videoWidth, containerHeight / videoHeight);
  const renderedWidth = videoWidth * scale;
  const renderedHeight = videoHeight * scale;
  const offsetX = (containerWidth - renderedWidth) / 2;
  const offsetY = (containerHeight - renderedHeight) / 2;

  let left: number;
  let right: number;

  if (isMirrored) {
    // Under horizontal flip, the visual left edge is at (1 - maxX)
    left = offsetX + (1.0 - box.maxX) * renderedWidth;
    right = offsetX + (1.0 - box.minX) * renderedWidth;
  } else {
    left = offsetX + box.minX * renderedWidth;
    right = offsetX + box.maxX * renderedWidth;
  }

  const top = offsetY + box.minY * renderedHeight;
  const bottom = offsetY + box.maxY * renderedHeight;

  return {
    x: left,
    y: top,
    width: Math.max(0, right - left),
    height: Math.max(0, bottom - top),
  };
}

/**
 * Exponential Moving Average (EMA) smoothing between successive box positions to suppress jitter.
 */
export function smoothBox(
  previousBox: DisplayBox | null,
  targetBox: DisplayBox,
  alpha = 0.35
): DisplayBox {
  if (!previousBox) return { ...targetBox };

  return {
    x: previousBox.x + alpha * (targetBox.x - previousBox.x),
    y: previousBox.y + alpha * (targetBox.y - previousBox.y),
    width: previousBox.width + alpha * (targetBox.width - previousBox.width),
    height: previousBox.height + alpha * (targetBox.height - previousBox.height),
  };
}

export type BadgePositionOptions = {
  badgeWidth?: number;
  badgeHeight?: number;
  margin?: number;
};

/**
 * Computes an unobstructed position for the recognition badge pill.
 *
 * Requirements:
 * - When 1 hand is present: Positions above the hand. If top clearance is insufficient, repositions below.
 * - When 2 hands are present: Positions centered between the hands above the topmost hand box so it does
 *   not obscure either hand or signing movements. If top clearance is insufficient, repositions below the
 *   lower hand or falls back to an unobstructed preview edge.
 * - When 0 hands are present: Positions at top-center.
 */
export function computeBadgePosition(
  handBoxes: DisplayBox[],
  containerWidth: number,
  containerHeight: number,
  options: BadgePositionOptions = {}
): { x: number; y: number } {
  const badgeWidth = options.badgeWidth ?? 150;
  const badgeHeight = options.badgeHeight ?? 32;
  const margin = options.margin ?? 12;

  if (handBoxes.length === 0) {
    return {
      x: Math.max(margin, (containerWidth - badgeWidth) / 2),
      y: margin,
    };
  }

  if (handBoxes.length === 1) {
    const box = handBoxes[0];
    let targetX = box.x + (box.width - badgeWidth) / 2;
    targetX = Math.max(margin, Math.min(containerWidth - badgeWidth - margin, targetX));

    // Try placing above the hand box
    const aboveY = box.y - badgeHeight - margin;
    if (aboveY >= margin) {
      return { x: targetX, y: aboveY };
    }

    // Insufficient top clearance: place below the hand box
    const belowY = box.y + box.height + margin;
    if (belowY + badgeHeight <= containerHeight - margin) {
      return { x: targetX, y: belowY };
    }

    // Both tight: clamp to top margin
    return { x: targetX, y: margin };
  }

  // Two or more hands detected
  const minX = Math.min(...handBoxes.map((b) => b.x));
  const maxX = Math.max(...handBoxes.map((b) => b.x + b.width));
  const minY = Math.min(...handBoxes.map((b) => b.y));
  const maxY = Math.max(...handBoxes.map((b) => b.y + b.height));

  // Center horizontally between the outer bounds of both hands
  let targetX = minX + (maxX - minX - badgeWidth) / 2;
  targetX = Math.max(margin, Math.min(containerWidth - badgeWidth - margin, targetX));

  // Try positioning above the highest hand
  const aboveY = minY - badgeHeight - margin;
  if (aboveY >= margin) {
    return { x: targetX, y: aboveY };
  }

  // Insufficient clearance above both hands: check below the lowest hand
  const belowY = maxY + margin;
  if (belowY + badgeHeight <= containerHeight - margin) {
    return { x: targetX, y: belowY };
  }

  // Hands span both top and bottom: position along an unobstructed edge (bottom center)
  return {
    x: Math.max(margin, (containerWidth - badgeWidth) / 2),
    y: Math.max(margin, containerHeight - badgeHeight - margin),
  };
}
