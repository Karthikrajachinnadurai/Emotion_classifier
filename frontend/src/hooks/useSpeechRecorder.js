/**
 * useSpeechRecorder.js
 * =====================
 * Custom React hook for microphone access and audio recording.
 *
 * Encapsulates ALL browser media logic so components stay clean.
 *
 * States:
 *   idle        — Not recording, ready to start
 *   requesting  — Waiting for mic permission (show "Listening...")
 *   recording   — Actively capturing audio (show "Recording...")
 *   stopped     — Recording complete, audioBlob available
 *   error       — Something went wrong
 *
 * Usage:
 *   const { status, startRecording, stopRecording, audioBlob, error, reset } = useSpeechRecorder();
 */

import { useState, useRef, useCallback } from 'react';

// Preferred MIME types ordered by compatibility
const PREFERRED_MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  'audio/mp4',
];

/**
 * Returns the first MIME type supported by the browser's MediaRecorder,
 * or an empty string to let the browser choose its default.
 */
function getSupportedMimeType() {
  if (typeof MediaRecorder === 'undefined') return '';
  for (const mimeType of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(mimeType)) {
      return mimeType;
    }
  }
  return '';
}

export function useSpeechRecorder() {
  const [status, setStatus] = useState('idle'); // idle | requesting | recording | stopped | error
  const [audioBlob, setAudioBlob] = useState(null);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  /**
   * Reset all state back to idle.
   * Call this when the user dismisses the result or wants to record again.
   */
  const reset = useCallback(() => {
    setStatus('idle');
    setAudioBlob(null);
    setError(null);
    chunksRef.current = [];
  }, []);

  /**
   * Stop the active media stream and release microphone access.
   */
  const _stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  /**
   * Request microphone access and begin recording.
   */
  const startRecording = useCallback(async () => {
    // Guard: don't start if already recording
    if (status === 'recording' || status === 'requesting') return;

    setError(null);
    setAudioBlob(null);
    chunksRef.current = [];

    // ── 1. Check browser support ────────────────────────────────────────
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Your browser does not support microphone access. Please use Chrome, Firefox, or Edge.');
      setStatus('error');
      return;
    }

    if (typeof MediaRecorder === 'undefined') {
      setError('Your browser does not support audio recording (MediaRecorder API not found).');
      setStatus('error');
      return;
    }

    // ── 2. Request microphone permission ────────────────────────────────
    setStatus('requesting');

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,        // Mono — Whisper works best with mono
          sampleRate: 16000,      // 16 kHz — Whisper's native sample rate
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });
    } catch (err) {
      let friendlyMessage;
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        friendlyMessage =
          'Microphone access was denied. Please allow microphone access in your browser settings and try again.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        friendlyMessage = 'No microphone found. Please connect a microphone and try again.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        friendlyMessage = 'Microphone is already in use by another application. Please close it and try again.';
      } else if (err.name === 'OverconstrainedError') {
        friendlyMessage = 'Microphone does not meet the required audio constraints. Please try a different microphone.';
      } else {
        friendlyMessage = `Could not access microphone: ${err.message}`;
      }
      setError(friendlyMessage);
      setStatus('error');
      return;
    }

    streamRef.current = stream;

    // ── 3. Set up MediaRecorder ─────────────────────────────────────────
    const mimeType = getSupportedMimeType();
    const recorderOptions = mimeType ? { mimeType } : {};

    let recorder;
    try {
      recorder = new MediaRecorder(stream, recorderOptions);
    } catch (err) {
      _stopStream();
      setError(`Could not initialise audio recorder: ${err.message}`);
      setStatus('error');
      return;
    }

    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, {
        type: mimeType || 'audio/webm',
      });
      setAudioBlob(blob);
      setStatus('stopped');
      _stopStream();
    };

    recorder.onerror = (event) => {
      setError(`Recording error: ${event.error?.message || 'Unknown error'}`);
      setStatus('error');
      _stopStream();
    };

    // ── 4. Start recording ──────────────────────────────────────────────
    mediaRecorderRef.current = recorder;
    recorder.start(250); // collect data every 250ms
    setStatus('recording');
  }, [status, _stopStream]);

  /**
   * Stop recording and trigger blob assembly.
   */
  const stopRecording = useCallback(() => {
    if (status !== 'recording') return;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    // Status will be set to 'stopped' in recorder.onstop
  }, [status]);

  return {
    status,       // 'idle' | 'requesting' | 'recording' | 'stopped' | 'error'
    audioBlob,    // Blob | null — the recorded audio
    error,        // string | null — human-readable error message
    startRecording,
    stopRecording,
    reset,
  };
}
