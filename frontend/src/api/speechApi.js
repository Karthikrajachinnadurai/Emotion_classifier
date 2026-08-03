/**
 * speechApi.js
 * =============
 * Isolated API module for the Speech-to-Text endpoint.
 *
 * Uses the existing axiosClient (with JWT auth interceptor) so that
 * no auth logic needs to be duplicated.
 *
 * Usage:
 *   import { transcribeAudio } from '../api/speechApi';
 *   const { transcript } = await transcribeAudio(audioBlob);
 */

import axiosClient from './axiosClient';

/**
 * Upload an audio Blob to the backend and receive its transcript.
 *
 * @param {Blob} audioBlob - The recorded audio blob from useSpeechRecorder
 * @param {string} [filename='recording.webm'] - Optional filename hint for format detection
 * @returns {Promise<{ transcript: string }>}
 * @throws {Error} with a user-friendly message if the request fails
 */
export async function transcribeAudio(audioBlob, filename = 'recording.webm') {
  if (!audioBlob || audioBlob.size === 0) {
    throw new Error('Audio recording is empty. Please try recording again.');
  }

  // Build multipart form data
  const formData = new FormData();
  formData.append('audio', audioBlob, filename);

  try {
    const response = await axiosClient.post('/speech-to-text', formData, {
      headers: {
        // Let the browser set Content-Type with proper boundary
        'Content-Type': 'multipart/form-data',
      },
      // Increase timeout for larger audio files (30 seconds)
      timeout: 30_000,
    });

    return response.data; // { transcript: "..." }
  } catch (err) {
    // Surface a user-friendly error message
    if (err.response) {
      const detail = err.response.data?.detail;
      switch (err.response.status) {
        case 400:
          throw new Error(detail || 'Audio is empty or no speech was detected.');
        case 413:
          throw new Error(detail || 'Recording is too large. Please keep it under 25 MB.');
        case 415:
          throw new Error(detail || 'Unsupported audio format.');
        case 503:
          throw new Error(detail || 'Speech recognition service is not available right now.');
        case 500:
          throw new Error(detail || 'Server error during transcription. Please try again.');
        default:
          throw new Error(detail || `Transcription failed (${err.response.status}).`);
      }
    }

    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      throw new Error('Transcription timed out. Please try a shorter recording.');
    }

    throw new Error(err.message || 'Network error. Please check your connection and try again.');
  }
}
