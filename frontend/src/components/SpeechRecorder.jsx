/**
 * SpeechRecorder.jsx
 * ====================
 * A fully self-contained Speech-to-Text recorder component.
 *
 * Features:
 *  - Mic button with animated pulse ring during recording
 *  - Status label: Idle → Listening... → Recording... → Uploading... → Transcribing...
 *  - Graceful error display with dismiss button
 *  - Transcript display on success
 *  - Calls onTranscript(text) prop so the parent can consume the result
 *
 * Props:
 *  - onTranscript: (text: string) => void   Called when transcription succeeds
 *  - disabled: boolean                      Disables the button (e.g. when parent is busy)
 *
 * This component does NOT call /predict or modify any other state.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Mic, MicOff, Square, Loader2, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { useSpeechRecorder } from '../hooks/useSpeechRecorder';
import { transcribeAudio } from '../api/speechApi';

// ── Status display config ─────────────────────────────────────────────────────
const STATUS_CONFIG = {
  idle: {
    label: null,
    color: 'var(--accent-primary)',
    showPulse: false,
  },
  requesting: {
    label: '🎙 Listening...',
    color: '#F59E0B',
    showPulse: true,
  },
  recording: {
    label: '● Recording...',
    color: '#EF4444',
    showPulse: true,
  },
  uploading: {
    label: '↑ Uploading...',
    color: 'var(--accent-secondary)',
    showPulse: false,
  },
  transcribing: {
    label: '✦ Transcribing...',
    color: '#A78BFA',
    showPulse: false,
  },
  done: {
    label: '✓ Done',
    color: '#10B981',
    showPulse: false,
  },
  error: {
    label: null,
    color: '#EF4444',
    showPulse: false,
  },
};

// ── Component ─────────────────────────────────────────────────────────────────
const SpeechRecorder = ({ onTranscript, disabled = false }) => {
  const { status: recorderStatus, audioBlob, error: recorderError, startRecording, stopRecording, reset } =
    useSpeechRecorder();

  // Extended status includes upload/transcribe phases
  const [phase, setPhase] = useState('idle'); // idle | requesting | recording | uploading | transcribing | done | error
  const [apiError, setApiError] = useState(null);
  const [transcript, setTranscript] = useState(null);

  // ── Sync recorder status → phase ─────────────────────────────────────────
  useEffect(() => {
    if (recorderStatus === 'idle') setPhase('idle');
    else if (recorderStatus === 'requesting') setPhase('requesting');
    else if (recorderStatus === 'recording') setPhase('recording');
    else if (recorderStatus === 'error') {
      setPhase('error');
      setApiError(recorderError);
    }
    // 'stopped' is handled in the useEffect below
  }, [recorderStatus, recorderError]);

  // ── When blob is ready → upload → transcribe ──────────────────────────────
  useEffect(() => {
    if (recorderStatus !== 'stopped' || !audioBlob) return;

    let cancelled = false;

    const runTranscription = async () => {
      setPhase('uploading');

      try {
        await new Promise((r) => setTimeout(r, 300)); // Brief pause for UI feedback
        if (cancelled) return;

        setPhase('transcribing');
        const result = await transcribeAudio(audioBlob);
        if (cancelled) return;

        setTranscript(result.transcript);
        setPhase('done');

        // Notify parent immediately
        if (onTranscript) {
          onTranscript(result.transcript);
        }
      } catch (err) {
        if (!cancelled) {
          setApiError(err.message);
          setPhase('error');
        }
      }
    };

    runTranscription();
    return () => { cancelled = true; };
  }, [recorderStatus, audioBlob, onTranscript]);

  // ── Dismiss / reset ───────────────────────────────────────────────────────
  const handleReset = useCallback(() => {
    reset();
    setPhase('idle');
    setApiError(null);
    setTranscript(null);
  }, [reset]);

  // ── Button action ─────────────────────────────────────────────────────────
  const handleButtonClick = useCallback(() => {
    if (phase === 'recording') {
      stopRecording();
    } else if (phase === 'idle' || phase === 'done' || phase === 'error') {
      if (phase !== 'idle') handleReset();
      else startRecording();
    }
  }, [phase, startRecording, stopRecording, handleReset]);

  // For done/error states, clicking mic starts a new recording
  const handleMicClick = useCallback(() => {
    if (phase === 'done' || phase === 'error') {
      handleReset();
      // Small timeout to let state flush before starting
      setTimeout(() => startRecording(), 50);
    } else if (phase === 'idle') {
      startRecording();
    } else if (phase === 'recording') {
      stopRecording();
    }
  }, [phase, startRecording, stopRecording, handleReset]);

  const config = STATUS_CONFIG[phase] || STATUS_CONFIG.idle;
  const isProcessing = phase === 'uploading' || phase === 'transcribing';
  const isDisabled = disabled || isProcessing;

  // ── Button icon ───────────────────────────────────────────────────────────
  const renderIcon = () => {
    if (isProcessing) return <Loader2 size={20} className="stt-spin" />;
    if (phase === 'recording') return <Square size={18} fill="white" />;
    if (phase === 'error') return <MicOff size={20} />;
    if (phase === 'done') return <Mic size={20} />;
    return <Mic size={20} />;
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="stt-wrapper" aria-label="Speech to text recorder">
      {/* Main mic button */}
      <div className="stt-btn-container">
        {/* Pulse ring — shown during requesting & recording */}
        {config.showPulse && (
          <span
            className="stt-pulse-ring"
            style={{ '--pulse-color': config.color }}
          />
        )}

        <button
          id="stt-mic-btn"
          type="button"
          className={`stt-btn ${phase === 'recording' ? 'stt-btn--recording' : ''} ${isProcessing ? 'stt-btn--processing' : ''}`}
          style={{ '--btn-color': config.color }}
          onClick={handleMicClick}
          disabled={isDisabled}
          title={
            phase === 'recording'
              ? 'Stop recording'
              : phase === 'idle'
              ? 'Start voice recording'
              : config.label || 'Processing...'
          }
          aria-pressed={phase === 'recording'}
        >
          {renderIcon()}
        </button>
      </div>

      {/* Status label */}
      {config.label && (
        <span className="stt-status-label" style={{ color: config.color }}>
          {config.label}
        </span>
      )}

      {/* Error message */}
      {phase === 'error' && apiError && (
        <div className="stt-error-toast" role="alert">
          <AlertCircle size={14} style={{ flexShrink: 0, marginTop: '1px' }} />
          <span>{apiError}</span>
          <button
            type="button"
            className="stt-dismiss-btn"
            onClick={handleReset}
            aria-label="Dismiss error"
          >
            <X size={13} />
          </button>
        </div>
      )}

      {/* Success: transcript preview */}
      {phase === 'done' && transcript && (
        <div className="stt-transcript-preview" role="status">
          <CheckCircle2 size={14} color="#10B981" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span className="stt-transcript-text">"{transcript}"</span>
          <button
            type="button"
            className="stt-dismiss-btn"
            onClick={handleReset}
            aria-label="Clear transcript"
            title="Record again"
          >
            <X size={13} />
          </button>
        </div>
      )}
    </div>
  );
};

export default SpeechRecorder;
