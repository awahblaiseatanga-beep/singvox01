/**
 * Presentation-only helpers: turn real pipeline state into short, non-technical
 * labels for the product UI. No state is invented here — every branch reads a
 * value the engine already produces.
 */

export interface LiveStatusInput {
  /** Raw engine status string. */
  status: string;
  /** Raw engine error string, when the pipeline failed. */
  error?: string;
  /** Whether the camera + landmark pipeline is currently running. */
  isActive: boolean;
  /** Whether the 60-frame sequence buffer is full. */
  bufferReady: boolean;
  /** 0-100 buffer fill percentage while warming up. */
  bufferProgress: number;
}

export type LiveStatusPhase =
  | 'off'
  | 'starting-camera'
  | 'preparing-recognition'
  | 'warming-up'
  | 'ready'
  | 'error';

export interface LiveStatus {
  phase: LiveStatusPhase;
  /** Short label for the status chip. */
  label: string;
  /** Sentence shown next to the camera viewport. */
  detail: string;
}

export function deriveLiveStatus(input: LiveStatusInput): LiveStatus {
  const { status, error, isActive, bufferReady, bufferProgress } = input;
  const raw = status.toLowerCase();

  if (error) {
    return { phase: 'error', label: 'Camera unavailable', detail: 'The camera or recognition pipeline could not start.' };
  }

  if (raw.includes('requesting') || raw.includes('initializing')) {
    return { phase: 'starting-camera', label: 'Starting camera…', detail: 'Waiting for camera permission and the landmark model.' };
  }

  if (raw.includes('tracking active')) {
    return { phase: 'preparing-recognition', label: 'Preparing recognition…', detail: 'Tracking landmarks. Loading the sign model.' };
  }

  if (raw.includes('live')) {
    if (!bufferReady) {
      const pct = Math.max(0, Math.min(99, Math.round(bufferProgress)));
      return { phase: 'warming-up', label: pct > 0 ? `Getting ready ${pct}%` : 'Getting ready', detail: 'Hold your hands where the camera can see them.' };
    }
    return { phase: 'ready', label: 'Ready', detail: 'Sign in view and hold briefly to translate.' };
  }

  if (isActive) {
    return { phase: 'preparing-recognition', label: 'Preparing recognition…', detail: 'Starting the sign model.' };
  }

  return { phase: 'off', label: 'Camera off', detail: 'Start a translation session to use the camera.' };
}

export interface FriendlyError {
  title: string;
  hint: string;
}

/** Map technical camera/pipeline failures onto plain-language guidance. */
export function friendlyError(rawError: string): FriendlyError {
  const raw = rawError.toLowerCase();

  if (raw.includes('permission') || raw.includes('notallowed') || raw.includes('denied')) {
    return {
      title: 'Camera access is blocked',
      hint: 'Allow camera access for this site in your browser settings, then press Start translation again.',
    };
  }
  if (raw.includes('notfound') || raw.includes('no camera') || raw.includes('devicesnotfound')) {
    return { title: 'No camera found', hint: 'Connect a camera or open SignVox on a device that has one, then try again.' };
  }
  if (raw.includes('notreadable') || raw.includes('could not start') || raw.includes('trackstart')) {
    return { title: 'Camera is busy', hint: 'Another application or tab is using the camera. Close it and press Start translation again.' };
  }
  if (raw.includes('secure') || raw.includes('https')) {
    return { title: 'A secure connection is required', hint: 'Browsers only allow camera access over HTTPS or on localhost.' };
  }
  if (raw.includes('onnx') || raw.includes('model')) {
    return { title: 'Sign model could not load', hint: 'Check your connection, then stop and start the session again.' };
  }
  return { title: 'Camera could not start', hint: 'Check that a camera is available and permitted, then try again.' };
}
