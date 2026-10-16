import React, { useEffect, useRef } from 'react';
import type { RawLandmarkInput } from '../lib/contracts';
import type { InferenceResult } from '../lib/inference';
import type { StabilizerState } from '../lib/temporalStabilizer';
import {
  computeHandBoundingBox,
  mapNormalizedToDisplay,
  smoothBox,
  computeBadgePosition,
  mapPointToDisplay,
  type DisplayBox,
} from '../lib/overlayCoordinates';
import { globalProfiler } from '../lib/latencyProfiler';

export type HandOverlayProps = {
  videoRef: React.RefObject<HTMLVideoElement>;
  rawDetection: RawLandmarkInput | null;
  liveResult?: InferenceResult;
  stableState?: StabilizerState;
  isBuffering?: boolean;
  bufferProgress?: number;
  showSkeleton?: boolean;
};

export const HandOverlay: React.FC<HandOverlayProps> = ({
  videoRef,
  rawDetection,
  liveResult,
  stableState,
  isBuffering = false,
  bufferProgress = 0,
  showSkeleton = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const smoothedBoxesRef = useRef<Map<string, DisplayBox>>(new Map());
  const smoothedBadgePosRef = useRef<{ x: number; y: number } | null>(null);

  // Store latest props in a mutable ref so render loop runs at continuous 60fps
  // without being torn down and recreated on every React render
  const propsRef = useRef({
    videoRef,
    rawDetection,
    liveResult,
    stableState,
    isBuffering,
    bufferProgress,
    showSkeleton,
  });

  propsRef.current = {
    videoRef,
    rawDetection,
    liveResult,
    stableState,
    isBuffering,
    bufferProgress,
    showSkeleton,
  };

  useEffect(() => {
    let animId: number;

    const render = () => {
      const renderStart = performance.now();
      const {
        videoRef: currentVideoRef,
        rawDetection: currentDetection,
        liveResult: currentLiveResult,
        stableState: currentStableState,
        isBuffering: currentIsBuffering,
        bufferProgress: currentBufferProgress,
        showSkeleton: currentShowSkeleton,
      } = propsRef.current;

      const canvas = canvasRef.current;
      const video = currentVideoRef.current;

      if (canvas && video) {
        const container = canvas.parentElement;
        const containerWidth = container ? container.clientWidth : canvas.clientWidth;
        const containerHeight = container ? container.clientHeight : canvas.clientHeight;

        const dpr = window.devicePixelRatio || 1;
        const targetWidth = Math.round(containerWidth * dpr);
        const targetHeight = Math.round(containerHeight * dpr);

        if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
          canvas.width = targetWidth;
          canvas.height = targetHeight;
        }

        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.save();
          ctx.scale(dpr, dpr);
          ctx.clearRect(0, 0, containerWidth, containerHeight);

          if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA && containerWidth > 0 && containerHeight > 0) {
            const videoWidth = video.videoWidth || 1280;
            const videoHeight = video.videoHeight || 720;

            const isStable = currentStableState?.status === 'Stable' && !!currentStableState.currentStableName;
            const isTentative = !isStable && !!currentLiveResult?.topK[0];

            // Primary color theme
            const primaryColor = isStable
              ? '#10b981' // Emerald
              : isTentative
              ? '#f59e0b' // Amber
              : '#38bdf8'; // Sky cyan

            const primaryFill = isStable
              ? 'rgba(16, 185, 129, 0.08)'
              : isTentative
              ? 'rgba(245, 158, 11, 0.08)'
              : 'rgba(56, 189, 248, 0.05)';

            // Optional landmark skeleton visualization
            if (currentShowSkeleton && currentDetection) {
              ctx.lineWidth = 1.5;
              ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
              ctx.fillStyle = 'rgba(56, 189, 248, 0.6)';

              // Draw pose connection points if available
              if (currentDetection.pose) {
                for (const p of currentDetection.pose) {
                  if ((p.visibility ?? 0) > 0.5) {
                    const pt = mapPointToDisplay(p, videoWidth, videoHeight, containerWidth, containerHeight, true);
                    ctx.beginPath();
                    ctx.arc(pt.x, pt.y, 2.5, 0, Math.PI * 2);
                    ctx.fill();
                  }
                }
              }

              // Draw hand skeleton points if available
              if (currentDetection.hands) {
                for (const h of currentDetection.hands) {
                  for (const pt of h.landmarks) {
                    const dp = mapPointToDisplay(pt, videoWidth, videoHeight, containerWidth, containerHeight, true);
                    ctx.beginPath();
                    ctx.arc(dp.x, dp.y, 2, 0, Math.PI * 2);
                    ctx.fill();
                  }
                }
              }
            }

            // Draw bounding boxes for each reliably detected hand
            const currentDisplayBoxes: DisplayBox[] = [];
            const detectedKeys = new Set<string>();

            if (currentDetection?.hands && currentDetection.hands.length > 0) {
              globalProfiler.recordFirstHandRendered();
              currentDetection.hands.forEach((hand, idx) => {
                const normBox = computeHandBoundingBox(hand.landmarks, { paddingX: 0.04, paddingY: 0.05 });
                if (normBox) {
                  const targetBox = mapNormalizedToDisplay(
                    normBox,
                    videoWidth,
                    videoHeight,
                    containerWidth,
                    containerHeight,
                    true // mirrored display
                  );

                  const handKey = `${hand.label}-${idx}`;
                  detectedKeys.add(handKey);

                  const prevBox = smoothedBoxesRef.current.get(handKey) || null;
                  const smoothed = smoothBox(prevBox, targetBox, 0.35);
                  smoothedBoxesRef.current.set(handKey, smoothed);
                  currentDisplayBoxes.push(smoothed);

                  // Draw hand bounding box
                  ctx.lineWidth = 1.8;
                  ctx.strokeStyle = primaryColor;
                  ctx.fillStyle = primaryFill;

                  // Rounded rectangle box
                  const r = 6;
                  ctx.beginPath();
                  ctx.moveTo(smoothed.x + r, smoothed.y);
                  ctx.lineTo(smoothed.x + smoothed.width - r, smoothed.y);
                  ctx.quadraticCurveTo(smoothed.x + smoothed.width, smoothed.y, smoothed.x + smoothed.width, smoothed.y + r);
                  ctx.lineTo(smoothed.x + smoothed.width, smoothed.y + smoothed.height - r);
                  ctx.quadraticCurveTo(smoothed.x + smoothed.width, smoothed.y + smoothed.height, smoothed.x + smoothed.width - r, smoothed.y + smoothed.height);
                  ctx.lineTo(smoothed.x + r, smoothed.y + smoothed.height);
                  ctx.quadraticCurveTo(smoothed.x, smoothed.y + smoothed.height, smoothed.x, smoothed.y + smoothed.height - r);
                  ctx.lineTo(smoothed.x, smoothed.y + r);
                  ctx.quadraticCurveTo(smoothed.x, smoothed.y, smoothed.x + r, smoothed.y);
                  ctx.closePath();
                  ctx.fill();
                  ctx.stroke();

                  // Corner accent marks for high-tech aesthetic
                  const cornerLen = Math.min(10, smoothed.width / 4, smoothed.height / 4);
                  ctx.lineWidth = 2.5;
                  ctx.strokeStyle = primaryColor;

                  // Top-left
                  ctx.beginPath();
                  ctx.moveTo(smoothed.x, smoothed.y + cornerLen);
                  ctx.lineTo(smoothed.x, smoothed.y);
                  ctx.lineTo(smoothed.x + cornerLen, smoothed.y);
                  ctx.stroke();

                  // Top-right
                  ctx.beginPath();
                  ctx.moveTo(smoothed.x + smoothed.width - cornerLen, smoothed.y);
                  ctx.lineTo(smoothed.x + smoothed.width, smoothed.y);
                  ctx.lineTo(smoothed.x + smoothed.width, smoothed.y + cornerLen);
                  ctx.stroke();

                  // Bottom-left
                  ctx.beginPath();
                  ctx.moveTo(smoothed.x, smoothed.y + smoothed.height - cornerLen);
                  ctx.lineTo(smoothed.x, smoothed.y + smoothed.height);
                  ctx.lineTo(smoothed.x + cornerLen, smoothed.y + smoothed.height);
                  ctx.stroke();

                  // Bottom-right
                  ctx.beginPath();
                  ctx.moveTo(smoothed.x + smoothed.width - cornerLen, smoothed.y + smoothed.height);
                  ctx.lineTo(smoothed.x + smoothed.width, smoothed.y + smoothed.height);
                  ctx.lineTo(smoothed.x + smoothed.width, smoothed.y + smoothed.height - cornerLen);
                  ctx.stroke();

                  // Subtle hand label tag
                  const tagText = hand.label === 'Left' ? 'L Hand' : hand.label === 'Right' ? 'R Hand' : 'Hand';
                  ctx.font = '600 10px Inter, system-ui, sans-serif';
                  const tagWidth = ctx.measureText(tagText).width + 10;
                  const tagHeight = 16;
                  const tagX = smoothed.x;
                  const tagY = Math.max(0, smoothed.y - tagHeight - 2);

                  ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
                  ctx.beginPath();
                  ctx.roundRect ? ctx.roundRect(tagX, tagY, tagWidth, tagHeight, 3) : ctx.rect(tagX, tagY, tagWidth, tagHeight);
                  ctx.fill();
                  ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
                  ctx.lineWidth = 1;
                  ctx.stroke();

                  ctx.fillStyle = '#94a3b8';
                  ctx.fillText(tagText, tagX + 5, tagY + 11);
                }
              });
            }

            // Prune boxes that disappeared
            for (const key of smoothedBoxesRef.current.keys()) {
              if (!detectedKeys.has(key)) {
                smoothedBoxesRef.current.delete(key);
              }
            }

            // Prepare badge content
            let badgeText = '';
            let statusDotColor = '#94a3b8';
            let statusDotSymbol = '○';

            if (currentIsBuffering) {
              badgeText = `Buffering (${currentBufferProgress}%)`;
              statusDotColor = '#64748b';
              statusDotSymbol = '○';
            } else if (isStable) {
              const signName = currentStableState!.currentStableName!;
              const conf = currentLiveResult?.topK[0]?.confidence ?? 0;
              const confPercent = Math.round(conf * 100);
              badgeText = `${signName}  ${confPercent}% Conf`;
              statusDotColor = '#10b981';
              statusDotSymbol = '●';
            } else if (isTentative) {
              const top = currentLiveResult!.topK[0];
              const confPercent = Math.round(top.confidence * 100);
              badgeText = `${top.className}  ${confPercent}% Conf`;
              statusDotColor = '#f59e0b';
              statusDotSymbol = '◐';
            } else {
              badgeText = currentDisplayBoxes.length > 0 ? 'Listening…' : 'No Hand Detected';
              statusDotColor = '#94a3b8';
              statusDotSymbol = '○';
            }

            // Measure badge width dynamically
            ctx.font = '600 13px Inter, system-ui, sans-serif';
            const textMetrics = ctx.measureText(badgeText);
            const badgeWidth = Math.max(130, textMetrics.width + 36);
            const badgeHeight = 32;

            // Compute unobstructed badge position
            const targetBadgePos = computeBadgePosition(
              currentDisplayBoxes,
              containerWidth,
              containerHeight,
              { badgeWidth, badgeHeight, margin: 12 }
            );

            // Smooth badge position to prevent jumpiness
            if (!smoothedBadgePosRef.current) {
              smoothedBadgePosRef.current = { ...targetBadgePos };
            } else {
              smoothedBadgePosRef.current.x += 0.3 * (targetBadgePos.x - smoothedBadgePosRef.current.x);
              smoothedBadgePosRef.current.y += 0.3 * (targetBadgePos.y - smoothedBadgePosRef.current.y);
            }

            const bx = smoothedBadgePosRef.current.x;
            const by = smoothedBadgePosRef.current.y;

            // Render glassmorphic badge pill
            ctx.save();
            ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
            ctx.shadowBlur = 8;
            ctx.shadowOffsetY = 2;

            ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
            ctx.beginPath();
            ctx.roundRect
              ? ctx.roundRect(bx, by, badgeWidth, badgeHeight, 16)
              : ctx.rect(bx, by, badgeWidth, badgeHeight);
            ctx.fill();

            ctx.restore();

            // Badge border
            ctx.lineWidth = 1.2;
            ctx.strokeStyle = isStable
              ? 'rgba(16, 185, 129, 0.6)'
              : isTentative
              ? 'rgba(245, 158, 11, 0.6)'
              : 'rgba(255, 255, 255, 0.15)';
            ctx.stroke();

            // Status indicator dot
            ctx.fillStyle = statusDotColor;
            ctx.font = 'bold 12px Inter, system-ui, sans-serif';
            ctx.fillText(statusDotSymbol, bx + 12, by + 20);

            // Badge text
            ctx.fillStyle = '#ffffff';
            ctx.font = '600 13px Inter, system-ui, sans-serif';
            ctx.fillText(badgeText, bx + 26, by + 21);

            // Subtitle tag for tentative status if applicable
            if (isTentative && !isStable) {
              ctx.font = '500 9px Inter, system-ui, sans-serif';
              ctx.fillStyle = '#f59e0b';
              ctx.fillText('TENTATIVE', bx + badgeWidth - 58, by + 12);
            }
          }
          ctx.restore();
        }
        globalProfiler.recordSample('overlayRender', performance.now() - renderStart);
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 5,
      }}
    />
  );
};
