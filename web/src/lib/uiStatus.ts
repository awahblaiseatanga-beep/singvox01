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
    // Report the *actual* failure. A missing model file is not a camera problem:
    // the camera and landmarks can be running perfectly, and labelling that as
    // "Camera unavailable" sends the user to fix the wrong thing.
    const friendly = friendlyError(error);
    return { phase: 'error', label: friendly.chip, detail: friendly.hint };
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
  /** Two-to-three-word form of `title` for the narrow status chip. */
  chip: string;
}

/** Map technical camera/pipeline failures onto plain-language guidance. */
export function friendlyError(rawError: string): FriendlyError {
  const raw = rawError.toLowerCase();

  if (raw.includes('permission') || raw.includes('notallowed') || raw.includes('denied')) {
    return {
      title: 'Camera access is blocked',
      chip: 'Camera blocked',
      hint: 'Allow camera access for this site in your browser settings, then press Start translation again.',
    };
  }
  if (raw.includes('notfound') || raw.includes('no camera') || raw.includes('devicesnotfound')) {
    return {
      title: 'No camera found',
      chip: 'No camera',
      hint: 'Connect a camera or open SignVox on a device that has one, then try again.',
    };
  }
  if (raw.includes('notreadable') || raw.includes('could not start') || raw.includes('trackstart')) {
    return {
      title: 'Camera is busy',
      chip: 'Camera busy',
      hint: 'Another application or tab is using the camera. Close it and press Start translation again.',
    };
  }
  // A page without a secure context exposes no `navigator.mediaDevices`, so the
  // failure reaches us as a missing `getUserMedia`, not as a named DOMException.
  //
  // This branch used to test for the substring `https`, which mislabelled *every*
  // error that quoted an https URL — including the model and avatar asset URLs
  // this app prints in its own diagnostics — as a TLS problem. Match the actual
  // secure-context symptoms instead.
  if (
    raw.includes('secure context') ||
    raw.includes('insecure') ||
    raw.includes('mediadevices') ||
    raw.includes('getusermedia')
  ) {
    return {
      title: 'A secure connection is required',
      chip: 'Needs HTTPS',
      hint: 'Browsers only allow camera access over HTTPS or on localhost.',
    };
  }
  // The model files are far too large to commit, so a deployment that has not
  // been given `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` answers the model
  // URL with its own index.html. That is a hosting problem, not a connectivity or
  // code problem, and the user cannot act on it — say so instead of blaming the
  // connection. Matched on the token the asset preflight prefixes (lib/assetPreflight).
  if (raw.includes('sign model asset missing')) {
    return {
      title: 'Sign recognition is unavailable in this build',
      chip: 'Recognition unavailable',
      hint: 'The sign model file is missing from this deployment, so signs cannot be translated right now. Please try again later.',
    };
  }
  if (raw.includes('onnx') || raw.includes('model')) {
    return {
      title: 'Sign model could not load',
      chip: 'Sign model unavailable',
      hint: 'Check your connection, then stop and start the session again.',
    };
  }
  return {
    title: 'Camera could not start',
    chip: 'Camera unavailable',
    hint: 'Check that a camera is available and permitted, then try again.',
  };
}
