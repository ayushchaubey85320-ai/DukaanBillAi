/**
 * High-Definition Voice Recognition & Natural Speech Engine
 * Enhanced for Indian Accents: English (India) [en-IN] & Hindi [hi-IN]
 * Features:
 * - Manual mic open/close control: stays listening until user manually taps stop
 * - Auto-restart on intermittent browser silence pauses during manual recording
 * - Instant TTS cancellation when opening mic or pressing stop
 * - Audio visualizer state notifications
 * - Web Audio API synthesized audio chimes for tactile feedback
 */

class SpeechService {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.manualListeningActive = false;
    this.accumulatedTranscript = "";
    this.interimTranscript = "";
    this.language = "en-IN";
    this.onTranscriptUpdateCallback = null;
    this.onErrorCallback = null;
    this.onSpeakingChangeCallback = null;
    this.audioCtx = null;
    this.cachedVoices = [];
    this.isSpeaking = false;

    // Initialize Voice Synthesis voices listener
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const loadVoices = () => {
        this.cachedVoices = window.speechSynthesis.getVoices();
      };
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    // Initialize Web Speech Recognition
    const SpeechRecognition = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 3;
      this.recognition.lang = this.language;

      this.recognition.onresult = (event) => {
        let currentInterim = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            this.accumulatedTranscript += (this.accumulatedTranscript ? " " : "") + transcript.trim();
          } else {
            currentInterim += transcript;
          }
        }
        this.interimTranscript = currentInterim;

        // Provide full combined text to caller in real time
        const fullDisplay = (this.accumulatedTranscript + (currentInterim ? " " + currentInterim : "")).trim();
        if (this.onTranscriptUpdateCallback) {
          this.onTranscriptUpdateCallback(fullDisplay, currentInterim);
        }
      };

      this.recognition.onerror = (event) => {
        console.warn("Speech recognition event:", event.error);
        if (event.error !== "no-speech") {
          if (this.onErrorCallback) this.onErrorCallback(event.error);
        }
      };

      this.recognition.onend = () => {
        // If manual recording is still active, auto-restart so the user isn't cut off by browser silence timeout!
        if (this.manualListeningActive) {
          try {
            this.recognition.start();
          } catch (e) {
            // Already started or restarting
          }
        } else {
          this.isListening = false;
        }
      };
    }
  }

  // Synthesize pleasant audio chime for mic feedback using Web Audio API
  playChime(type = "start") {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      if (!this.audioCtx) this.audioCtx = new AudioContext();

      const ctx = this.audioCtx;
      if (ctx.state === "suspended") ctx.resume();

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;
      if (type === "start") {
        // High-tech ascending chime
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.12); // A5
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
        osc.start(now);
        osc.stop(now + 0.24);
      } else {
        // Soft descending confirmation tone
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(440, now + 0.14);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.22);
      }
    } catch (e) {
      // AudioContext policy
    }
  }

  setLanguage(langCode) {
    this.language = langCode === "hi" ? "hi-IN" : "en-IN";
    if (this.recognition) {
      this.recognition.lang = this.language;
    }
  }

  // Manual Mic Control: User controls when to open and when to close!
  startManualListening({ onTranscriptUpdate, onError, initialText = "" }) {
    // Immediately stop any playing assistant speech to avoid microphone feedback
    this.cancelSpeech();

    if (!this.recognition) {
      if (onError) onError("Speech Recognition is not supported on this device/browser. Please type.");
      return;
    }

    this.accumulatedTranscript = initialText ? initialText.trim() : "";
    this.interimTranscript = "";
    this.onTranscriptUpdateCallback = onTranscriptUpdate;
    this.onErrorCallback = onError;
    this.manualListeningActive = true;
    this.isListening = true;

    try {
      this.playChime("start");
      this.recognition.lang = this.language;
      this.recognition.start();
    } catch (e) {
      console.warn("Recognition start notice:", e);
    }
  }

  stopManualListening() {
    this.manualListeningActive = false;
    this.isListening = false;
    this.playChime("stop");

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }

    const finalText = (this.accumulatedTranscript + (this.interimTranscript ? " " + this.interimTranscript : "")).trim();
    this.accumulatedTranscript = "";
    this.interimTranscript = "";
    return finalText;
  }

  cancelManualListening() {
    this.manualListeningActive = false;
    this.isListening = false;
    this.accumulatedTranscript = "";
    this.interimTranscript = "";
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {}
    }
  }

  // TTS Speech Control
  cancelSpeech() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
      if (this.onSpeakingChangeCallback) {
        this.onSpeakingChangeCallback(false);
      }
    }
  }

  setSpeakingChangeListener(cb) {
    this.onSpeakingChangeCallback = cb;
  }

  speak(text, lang = "en") {
    if (!('speechSynthesis' in window) || !text) return;

    this.cancelSpeech();

    const utterance = new SpeechSynthesisUtterance(text);
    const isHindi = lang === "hi";
    utterance.lang = isHindi ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;
    utterance.pitch = 1.02;

    const voices = this.cachedVoices.length > 0 ? this.cachedVoices : window.speechSynthesis.getVoices();
    let preferredVoice = null;
    if (isHindi) {
      preferredVoice = voices.find(v => 
        (v.lang === "hi-IN" || v.lang.startsWith("hi")) && 
        (v.name.includes("Natural") || v.name.includes("Swara") || v.name.includes("Google") || v.name.includes("Kalpana"))
      ) || voices.find(v => v.lang.startsWith("hi"));
    } else {
      preferredVoice = voices.find(v => 
        (v.lang === "en-IN" || v.lang.includes("India")) && 
        (v.name.includes("Natural") || v.name.includes("Neerja") || v.name.includes("Heera") || v.name.includes("Google"))
      ) || voices.find(v => v.lang === "en-IN");
    }

    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      if (this.onSpeakingChangeCallback) this.onSpeakingChangeCallback(true);
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      if (this.onSpeakingChangeCallback) this.onSpeakingChangeCallback(false);
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      if (this.onSpeakingChangeCallback) this.onSpeakingChangeCallback(false);
    };

    window.speechSynthesis.speak(utterance);
  }
}

export const speechService = new SpeechService();
