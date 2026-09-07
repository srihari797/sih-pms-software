// Side Sensor Connector Ports Handler for CMS8000 2D

class PortsHandler {
  constructor() {
    this.sensorStates = {
      ecg: true,
      spo2: true,
      nibp: true,
      temp1: true,
      temp2: true
    };
    this.bindSocketEvents();
  }

  bindSocketEvents() {
    const sockets = {
      'socketECG': 'ecg',
      'socketSpO2': 'spo2',
      'socketNIBP': 'nibp',
      'socketTEMP1': 'temp1',
      'socketTEMP2': 'temp2'
    };

    Object.entries(sockets).forEach(([socketId, sensorKey]) => {
      const socketEl = document.getElementById(socketId);
      if (socketEl) {
        socketEl.addEventListener('click', () => {
          this.toggleSensor(sensorKey);
        });
      }
    });
  }

  async toggleSensor(sensorKey) {
    window.audioSynth.playBeep(800, 0.04);
    const newConnected = !this.sensorStates[sensorKey];
    this.sensorStates[sensorKey] = newConnected;

    const plugMap = {
      ecg: 'cableECG',
      spo2: 'cableSpO2',
      nibp: 'cableNIBP',
      temp1: 'cableTEMP1',
      temp2: 'cableTEMP2'
    };

    const plugEl = document.getElementById(plugMap[sensorKey]);
    if (plugEl) {
      plugEl.classList.toggle('connected', newConnected);
      plugEl.classList.toggle('disconnected', !newConnected);
    }

    try {
      await fetch('/api/v1/control/sensor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor: sensorKey, connected: newConnected })
      });
    } catch (e) {
      console.error('Sensor toggle error:', e);
    }
  }

  updateSensorsUI(sensors) {
    if (!sensors) return;

    const isConn = (val) => {
      if (typeof val === 'object' && val !== null && val.connected !== undefined) {
        return val.connected;
      }
      return Boolean(val);
    };

    this.sensorStates = {
      ecg: isConn(sensors.ecg),
      spo2: isConn(sensors.spo2),
      nibp: isConn(sensors.nibp),
      temp1: isConn(sensors.temp1 !== undefined ? sensors.temp1 : sensors.temperature_t1),
      temp2: isConn(sensors.temp2 !== undefined ? sensors.temp2 : sensors.temperature_t2)
    };

    const plugMap = {
      ecg: 'cableECG',
      spo2: 'cableSpO2',
      nibp: 'cableNIBP',
      temp1: 'cableTEMP1',
      temp2: 'cableTEMP2'
    };

    Object.entries(plugMap).forEach(([key, plugId]) => {
      const plugEl = document.getElementById(plugId);
      if (plugEl) {
        const conn = this.sensorStates[key];
        plugEl.classList.toggle('connected', conn);
        plugEl.classList.toggle('disconnected', !conn);
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.portsHandler = new PortsHandler();
});
