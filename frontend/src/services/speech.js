/**
 * High-Definition Voice Recognition & Natural Speech Engine
 * Enhanced for Indian Accents: English (India) [en-IN] & Hindi [hi-IN]
 * Features:
 * - Asynchronous natural voice resolution (Microsoft Swara/Neerja, Google हिन्दी/en-IN)
 * - Interim live speech streaming for instant visual feedback
 * - Web Audio API synthesized audio beeps for mic on/off confirmation
 * - Calibrated cadence and natural pitch
 */

class SpeechService {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.language = "en-IN";
    this.onResultCallback = null;
    this.onInterimCallback = null;
    this.onErrorCallback = null;
    this.onEndCallback = null;
    this.audioCtx = null;
    this.voicesLoaded = false;
    this.cachedVoices = [];

    // Initialize Voice Synthesis voices listener
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const loadVoices = () => {
        this.cachedVoices = window.speechSynthesis.getVoices();
        if (this.cachedVoices.length > 0) {
          this.voicesLoaded = true;
        }
      };
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    // Initialize Speech Recognition
    const SpeechRecognition = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 3;
      this.recognition.lang = this.language;

      let finalTranscript = "";

      this.recognition.onresult = (event) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript + " ";
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        if (this.onInterimCallback && interimTranscript) {
          this.onInterimCallback(interimTranscript);
        }

        if (finalTranscript.trim() && this.onResultCallback) {
          const sent = finalTranscript.trim();
          finalTranscript = "";
          this.onResultCallback(sent);
        }
      };

      this.recognition.onerror = (event) => {
        console.warn("Speech recognition notice:", event.error);
        if (event.error !== "no-speech") {
          this.isListening = false;
          if (this.onErrorCallback) this.onErrorCallback(event.error);
        }
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (this.onEndCallback) this.onEndCallback();
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
        // High-tech ascending double-beep
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
      // AudioContext not allowed before user gesture
    }
  }

  setLanguage(langCode) {
    this.language = langCode === "hi" ? "hi-IN" : "en-IN";
    if (this.recognition) {
      this.recognition.lang = this.language;
    }
  }

  startListening(onResult, onInterim, onError, onEnd) {
    if (!this.recognition) {
      if (onError) onError("Speech Recognition not supported in this browser. Please use text input.");
      return;
    }
    this.onResultCallback = onResult;
    this.onInterimCallback = onInterim;
    this.onErrorCallback = onError;
    this.onEndCallback = onEnd;

    try {
      this.playChime("start");
      this.recognition.lang = this.language;
      this.recognition.start();
      this.isListening = true;
    } catch (e) {
      console.warn("Recognition start info:", e);
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.playChime("stop");
      this.recognition.stop();
      this.isListening = false;
    }
  }

  // High quality natural Indian voice synthesizer
  speak(text, lang = "en") {
    if (!('speechSynthesis' in window) || !text) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const isHindi = lang === "hi";
    utterance.lang = isHindi ? "hi-IN" : "en-IN";
    utterance.rate = 0.94; // slightly slower, natural human cadence
    utterance.pitch = 1.02;

    const voices = this.cachedVoices.length > 0 ? this.cachedVoices : window.speechSynthesis.getVoices();
    
    let preferredVoice = null;
    if (isHindi) {
      // Look for natural Hindi voices
      preferredVoice = voices.find(v => 
        (v.lang === "hi-IN" || v.lang.startsWith("hi")) && 
        (v.name.includes("Natural") || v.name.includes("Swara") || v.name.includes("Google") || v.name.includes("Kalpana"))
      ) || voices.find(v => v.lang.startsWith("hi"));
    } else {
      // Look for natural Indian English voices
      preferredVoice = voices.find(v => 
        (v.lang === "en-IN" || v.lang.includes("India")) && 
        (v.name.includes("Natural") || v.name.includes("Neerja") || v.name.includes("Heera") || v.name.includes("Google"))
      ) || voices.find(v => v.lang === "en-IN");
    }

    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    window.speechSynthesis.speak(utterance);
  }
}

export const speechService = new SpeechService();
