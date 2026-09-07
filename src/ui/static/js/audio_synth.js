// Web Audio API Medical Sound Synthesizer

class AudioSynthesizer {
  constructor() {
    this.ctx = null;
    this.silenced = false;
  }

  initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playBeep(freq = 880, duration = 0.08, type = 'sine') {
    if (this.silenced) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      // Audio context error fallback
    }
  }

  playAlarmSound(level) {
    if (this.silenced) return;
    if (level === 'CRITICAL') {
      this.playBeep(987.77, 0.15, 'square'); // High pitch B5
      setTimeout(() => this.playBeep(987.77, 0.15, 'square'), 180);
    } else if (level === 'WARNING') {
      this.playBeep(659.25, 0.2, 'sine'); // E5
    }
  }

  toggleSilence() {
    this.silenced = !this.silenced;
    return this.silenced;
  }
}

window.audioSynth = new AudioSynthesizer();
