// Main Monitor View Coordinator for CMS8000 2D

class MonitorView {
  constructor() {
    this.ws = null;
    this.initClock();
    this.connectWebSocket();
  }

  initClock() {
    setInterval(() => {
      const now = new Date();
      const str = now.toISOString().replace('T', ' ').substring(0, 19);
      const el = document.getElementById('screenClock');
      if (el) el.innerText = str;
    }, 1000);
  }

  connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/monitor/P001`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      if (window.devPanelHandler) window.devPanelHandler.updateWsStatus(true);
    };

    this.ws.onclose = () => {
      if (window.devPanelHandler) window.devPanelHandler.updateWsStatus(false);
      setTimeout(() => this.connectWebSocket(), 2000);
    };

    this.ws.onerror = () => {
      if (window.devPanelHandler) window.devPanelHandler.updateWsStatus(false);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (window.devPanelHandler) window.devPanelHandler.logPayload(data);
        this.handleMessage(data);
      } catch (e) {
        console.error('WS Parse Error:', e);
      }
    };
  }

  handleMessage(data) {
    const eventType = data.event || data.type;

    if (eventType === 'DEVICE_STATUS') {
      if (data.sensors && window.portsHandler) window.portsHandler.updateSensorsUI(data.sensors);
      if (data.active_alarms && data.active_alarms.length > 0) {
        this.handleAlarmEvent(data.active_alarms[0]);
      } else {
        this.clearAlarmDisplay();
      }
    } else if (eventType === 'VITAL_UPDATE') {
      if (window.displayRenderer) window.displayRenderer.updateDigitalVitals(data);
    } else if (eventType === 'SENSOR_STATUS') {
      if (data.sensors && window.portsHandler) window.portsHandler.updateSensorsUI(data.sensors);
    } else if (eventType === 'ECG_STREAM') {
      const samples = (data.signal && data.signal.samples) ? data.signal.samples : data.samples;
      if (samples && samples.length > 0 && window.displayRenderer) {
        window.displayRenderer.pushEcgSamples(samples);
      }
    } else if (eventType === 'RESP_STREAM') {
      const samples = (data.signal && data.signal.samples) ? data.signal.samples : data.samples;
      if (samples && samples.length > 0 && window.displayRenderer) {
        window.displayRenderer.pushRespSamples(samples);
      }
    } else if (eventType === 'PLETH_STREAM') {
      const samples = (data.signal && data.signal.samples) ? data.signal.samples : data.samples;
      if (samples && samples.length > 0 && window.displayRenderer) {
        window.displayRenderer.pushPlethSamples(samples);
      }
    } else if (eventType === 'ALARM_EVENT') {
      this.handleAlarmEvent(data);
    } else if (eventType === 'NIBP_RESULT') {
      if (window.displayRenderer) window.displayRenderer.updateNIBPResult(data);
    }
  }

  handleAlarmEvent(data) {
    const alarmObj = data.alarm || data;
    const level = alarmObj.severity || alarmObj.level || 'NORMAL';
    const msg = alarmObj.message || alarmObj.description || 'ALARM ACTIVATED';

    const bannerTextEl = document.getElementById('alarmBannerText');
    const bannerEl = document.getElementById('screenAlarmBanner');
    const alarmLampEl = document.getElementById('alarmLamp');
    const alarmLampTextEl = document.getElementById('alarmLampText');

    if (bannerTextEl) bannerTextEl.innerText = msg;

    if (bannerEl) {
      bannerEl.classList.remove('warning', 'critical');
      if (level === 'CRITICAL') bannerEl.classList.add('critical');
      else if (level === 'WARNING') bannerEl.classList.add('warning');
    }

    if (alarmLampEl) {
      alarmLampEl.classList.remove('warning', 'critical');
      if (level === 'CRITICAL') alarmLampEl.classList.add('critical');
      else if (level === 'WARNING') alarmLampEl.classList.add('warning');
    }

    if (alarmLampTextEl) alarmLampTextEl.innerText = level === 'NORMAL' ? 'SYSTEM NORMAL' : msg;

    if (level === 'CRITICAL' && window.audioSynth) {
      window.audioSynth.playAlarmSound('CRITICAL');
    } else if (level === 'WARNING' && window.audioSynth) {
      window.audioSynth.playAlarmSound('WARNING');
    }
  }

  clearAlarmDisplay() {
    const bannerTextEl = document.getElementById('alarmBannerText');
    const bannerEl = document.getElementById('screenAlarmBanner');
    const alarmLampEl = document.getElementById('alarmLamp');
    const alarmLampTextEl = document.getElementById('alarmLampText');

    if (bannerTextEl) bannerTextEl.innerText = 'NO ALARM — MONITORING ACTIVE';
    if (bannerEl) bannerEl.classList.remove('warning', 'critical');
    if (alarmLampEl) alarmLampEl.classList.remove('warning', 'critical');
    if (alarmLampTextEl) alarmLampTextEl.innerText = 'SYSTEM NORMAL';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.monitorView = new MonitorView();
});
