// DisplayRenderer: 2D Oscilloscope Sweep & Vitals UI Handler for Contec CMS8000

class DisplayRenderer {
  constructor() {
    this.isFrozen = false;

    // Sample buffers for continuous oscilloscope sweep
    this.ecgBuffer = [];
    this.respBuffer = [];
    this.plethBuffer = [];

    // Sweep cursor X positions
    this.ecgX = 0;
    this.respX = 0;
    this.plethX = 0;
    this.sweepSpeed = 2.0;

    // Previous point coordinates
    this.ecgPrevY = 60;
    this.respPrevY = 60;
    this.plethPrevY = 60;

    // Get HTML5 Canvas contexts
    this.ecgCanvas = document.getElementById('ecgCanvas');
    this.respCanvas = document.getElementById('respCanvas');
    this.plethCanvas = document.getElementById('plethCanvas');

    this.ecgCtx = this.ecgCanvas ? this.ecgCanvas.getContext('2d') : null;
    this.respCtx = this.respCanvas ? this.respCanvas.getContext('2d') : null;
    this.plethCtx = this.plethCanvas ? this.plethCanvas.getContext('2d') : null;

    this.initGridBackgrounds();
    this.startSweepAnimation();
  }

  initGridBackgrounds() {
    [
      { ctx: this.ecgCtx, canvas: this.ecgCanvas },
      { ctx: this.respCtx, canvas: this.respCanvas },
      { ctx: this.plethCtx, canvas: this.plethCanvas }
    ].forEach(({ ctx, canvas }) => {
      if (!ctx || !canvas) return;
      ctx.fillStyle = '#010805';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      this.drawGridLines(ctx, canvas.width, canvas.height, 0, canvas.width);
    });
  }

  drawGridLines(ctx, width, height, startX, endX) {
    ctx.strokeStyle = '#05180f';
    ctx.lineWidth = 1;

    for (let x = Math.floor(startX / 20) * 20; x < endX; x += 20) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 20) {
      ctx.beginPath();
      ctx.moveTo(startX, y);
      ctx.lineTo(endX, y);
      ctx.stroke();
    }
  }

  setFrozen(frozen) {
    this.isFrozen = frozen;
    const tag = document.getElementById('freezeTag');
    if (tag) tag.classList.toggle('active', frozen);
  }

  pushEcgSamples(samples) {
    if (this.isFrozen) return;
    this.ecgBuffer.push(...samples);
  }

  pushRespSamples(samples) {
    if (this.isFrozen) return;
    this.respBuffer.push(...samples);
  }

  pushPlethSamples(samples) {
    if (this.isFrozen) return;
    this.plethBuffer.push(...samples);
  }

  startSweepAnimation() {
    const animate = () => {
      if (!this.isFrozen) {
        this.renderEcgChannel();
        this.renderRespChannel();
        this.renderPlethChannel();
      }
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }

  renderEcgChannel() {
    if (!this.ecgCtx || !this.ecgCanvas) return;
    const ctx = this.ecgCtx;
    const w = this.ecgCanvas.width;
    const h = this.ecgCanvas.height;
    const centerY = h / 2;

    const sample = this.ecgBuffer.length > 0 ? this.ecgBuffer.shift() : 0.0;
    const nextY = centerY - (sample * 45);

    this.sweepSegment(ctx, 'ecgX', 'ecgPrevY', nextY, w, h, '#00ff41', 2.0);
  }

  renderRespChannel() {
    if (!this.respCtx || !this.respCanvas) return;
    const ctx = this.respCtx;
    const w = this.respCanvas.width;
    const h = this.respCanvas.height;
    const centerY = h / 2;

    const sample = this.respBuffer.length > 0 ? this.respBuffer.shift() : 0.0;
    const nextY = centerY - (sample * 35);

    this.sweepSegment(ctx, 'respX', 'respPrevY', nextY, w, h, '#ffee00', 2.0);
  }

  renderPlethChannel() {
    if (!this.plethCtx || !this.plethCanvas) return;
    const ctx = this.plethCtx;
    const w = this.plethCanvas.width;
    const h = this.plethCanvas.height;
    const centerY = h / 2;

    const sample = this.plethBuffer.length > 0 ? this.plethBuffer.shift() : 0.0;
    const nextY = centerY - (sample * 35);

    this.sweepSegment(ctx, 'plethX', 'plethPrevY', nextY, w, h, '#00f0ff', 2.0);
  }

  sweepSegment(ctx, xKey, prevYKey, nextY, width, height, color, lineWidth) {
    let currX = this[xKey];
    let prevY = this[prevYKey];

    let nextX = currX + this.sweepSpeed;
    if (nextX >= width) {
      nextX = 0;
      currX = 0;
    }

    // Clear sweep erase bar ahead of cursor
    const eraseWidth = 16;
    ctx.fillStyle = '#010805';
    ctx.fillRect(currX, 0, eraseWidth, height);
    this.drawGridLines(ctx, width, height, currX, currX + eraseWidth);

    // Draw glowing stroke line
    ctx.beginPath();
    ctx.moveTo(currX, prevY);
    ctx.lineTo(nextX, nextY);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.shadowColor = color;
    ctx.shadowBlur = 4;
    ctx.stroke();
    ctx.shadowBlur = 0;

    this[xKey] = nextX;
    this[prevYKey] = nextY;
  }

  updateDigitalVitals(vitalsMsg) {
    let hrVal = null;
    let spo2Val = null;
    let prVal = null;
    let sysVal = null;
    let diaVal = null;
    let mapVal = null;
    let rrVal = null;
    let t1Val = null;
    let t2Val = null;

    if (vitalsMsg.data) {
      // Canonical VITAL_UPDATE contract
      const d = vitalsMsg.data;
      if (d.heart_rate) hrVal = d.heart_rate.value;
      if (d.spo2) spo2Val = d.spo2.value;
      if (d.pulse_rate) prVal = d.pulse_rate.value;
      if (d.respiratory_rate) rrVal = d.respiratory_rate.value;
      if (d.blood_pressure) {
        sysVal = d.blood_pressure.systolic;
        diaVal = d.blood_pressure.diastolic;
        mapVal = d.blood_pressure.map;
      }
      if (d.temperature) {
        if (d.temperature.t1) t1Val = d.temperature.t1.value;
        if (d.temperature.t2) t2Val = d.temperature.t2.value;
      }
    } else {
      // Legacy dict fallback
      hrVal = vitalsMsg.hr;
      spo2Val = vitalsMsg.spo2;
      prVal = vitalsMsg.pr !== undefined ? vitalsMsg.pr : vitalsMsg.hr;
      rrVal = vitalsMsg.rr;
      if (vitalsMsg.bp) {
        sysVal = vitalsMsg.bp.sys;
        diaVal = vitalsMsg.bp.dia;
        mapVal = vitalsMsg.bp.map;
      }
      if (vitalsMsg.temp) {
        t1Val = vitalsMsg.temp.t1;
        t2Val = vitalsMsg.temp.t2;
      }
    }

    // Update DOM Display Elements
    const hrEl = document.getElementById('valHR');
    if (hrEl) hrEl.innerText = hrVal !== null && hrVal !== undefined ? hrVal : '--';

    const spo2El = document.getElementById('valSpO2');
    if (spo2El) spo2El.innerText = spo2Val !== null && spo2Val !== undefined ? spo2Val : '--';

    const prEl = document.getElementById('valPR');
    if (prEl) prEl.innerText = prVal !== null && prVal !== undefined ? prVal : (hrVal !== null && hrVal !== undefined ? hrVal : '--');

    const rrEl = document.getElementById('valRR');
    if (rrEl) rrEl.innerText = rrVal !== null && rrVal !== undefined ? rrVal : '--';

    const bpEl = document.getElementById('valBP');
    if (bpEl) {
      if (sysVal !== null && sysVal !== undefined && diaVal !== null && diaVal !== undefined) {
        bpEl.innerText = `${sysVal}/${diaVal}`;
      } else {
        bpEl.innerText = '--/--';
      }
    }

    const mapEl = document.getElementById('valMAP');
    if (mapEl) mapEl.innerText = mapVal !== null && mapVal !== undefined ? mapVal : '--';

    const t1El = document.getElementById('valT1');
    if (t1El) t1El.innerText = t1Val !== null && t1Val !== undefined ? t1Val : '--';

    const t2El = document.getElementById('valT2');
    if (t2El) t2El.innerText = t2Val !== null && t2Val !== undefined ? t2Val : '--';

    // Pulse/blink visual indicator on incoming vital update
    ['valHR', 'valSpO2', 'valRR', 'valBP', 'heartIcon', 'pulseIcon'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.style.opacity = '0.35';
        setTimeout(() => { el.style.opacity = '1.0'; }, 150);
      }
    });
  }

  updateNIBPResult(nibpMsg) {
    const meas = nibpMsg.measurement;
    if (!meas) return;

    const bpEl = document.getElementById('valBP');
    if (bpEl && meas.systolic !== null && meas.diastolic !== null) {
      bpEl.innerText = `${meas.systolic}/${meas.diastolic}`;
    }
    const mapEl = document.getElementById('valMAP');
    if (mapEl && meas.map !== null) {
      mapEl.innerText = meas.map;
    }
    const badgeEl = document.getElementById('nibpStateBadge');
    if (badgeEl && meas.status) {
      badgeEl.innerText = meas.status.toUpperCase();
    }
  }

  renderMenuContent(tabName, data = {}) {
    const container = document.getElementById('menuContent');
    if (!container) return;

    if (tabName === 'patient') {
      container.innerHTML = `
        <div style="line-height: 1.8;">
          <h4 style="color:#00ff66; margin-bottom:10px;">PATIENT DEMOGRAPHICS</h4>
          <div><strong>PATIENT ID:</strong> P001</div>
          <div><strong>NAME:</strong> DOE, JOHN</div>
          <div><strong>BED NUMBER:</strong> BED-04</div>
          <div><strong>PATIENT TYPE:</strong> ADULT</div>
          <div><strong>ADMIT DATE:</strong> 2026-09-06</div>
          <div><strong>PHYSICIAN:</strong> DR. SMITH</div>
        </div>
      `;
    } else if (tabName === 'alarms') {
      container.innerHTML = `
        <div style="line-height: 1.8;">
          <h4 style="color:#00ff66; margin-bottom:10px;">ALARM LIMIT CONFIGURATION</h4>
          <table class="trend-table">
            <thead>
              <tr><th>PARAMETER</th><th>HIGH LIMIT</th><th>LOW LIMIT</th><th>STATUS</th></tr>
            </thead>
            <tbody>
              <tr><td>HR (Heart Rate)</td><td>120 bpm</td><td>50 bpm</td><td>ON</td></tr>
              <tr><td>SpO2 (Pulse Ox)</td><td>100 %</td><td>90 %</td><td>ON</td></tr>
              <tr><td>NIBP (Sys/Dia)</td><td>160/100</td><td>90/60</td><td>ON</td></tr>
              <tr><td>RESP (Resp Rate)</td><td>30 /min</td><td>8 /min</td><td>ON</td></tr>
              <tr><td>TEMP (Body Temp)</td><td>38.5 °C</td><td>35.0 °C</td><td>ON</td></tr>
            </tbody>
          </table>
        </div>
      `;
    } else if (tabName === 'trends') {
      const trends = data.trends || [];
      let rows = trends.map(t => `
        <tr>
          <td>${t.timestamp || 'RECENT'}</td>
          <td>${t.hr}</td>
          <td>${t.spo2}%</td>
          <td>${t.sys}/${t.dia}</td>
          <td>${t.rr}</td>
          <td>${t.t1}°C</td>
        </tr>
      `).join('');

      if (!rows) {
        rows = `<tr><td colspan="6" style="text-align:center;">NO TREND DATA RECORDED YET</td></tr>`;
      }

      container.innerHTML = `
        <div>
          <h4 style="color:#00ff66; margin-bottom:10px;">VITAL TREND HISTORICAL LOGS</h4>
          <table class="trend-table">
            <thead>
              <tr><th>TIME</th><th>HR</th><th>SpO2</th><th>NIBP</th><th>RESP</th><th>TEMP</th></tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } else if (tabName === 'events') {
      const events = data.events || [];
      let rows = events.map(e => `
        <tr>
          <td>${e.timestamp || 'RECENT'}</td>
          <td><span style="color:${e.level === 'CRITICAL' ? '#ff3344' : '#ffbb00'}">${e.level || 'INFO'}</span></td>
          <td>${e.message || e.description}</td>
        </tr>
      `).join('');

      if (!rows) {
        rows = `<tr><td colspan="3" style="text-align:center;">NO ALARM EVENTS RECORDED YET</td></tr>`;
      }

      container.innerHTML = `
        <div>
          <h4 style="color:#00ff66; margin-bottom:10px;">SYSTEM ALARM & EVENT LOGS</h4>
          <table class="event-table">
            <thead>
              <tr><th>TIME</th><th>LEVEL</th><th>DESCRIPTION</th></tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } else if (tabName === 'system') {
      container.innerHTML = `
        <div style="line-height: 1.8;">
          <h4 style="color:#00ff66; margin-bottom:10px;">CMS8000 SYSTEM INFORMATION</h4>
          <div><strong>MODEL:</strong> CONTEC CMS8000 PATIENT MONITOR</div>
          <div><strong>FIRMWARE:</strong> V3.8.4-RELEASE</div>
          <div><strong>SERIAL NO:</strong> CMS8000-20260906-8000X</div>
          <div><strong>DSP MODULE:</strong> CMS-DSP-v2.1 [OK]</div>
          <div><strong>OPERATING MODE:</strong> SIMULATION ENGINE ACTIVE</div>
          <div><strong>BATTERY STATUS:</strong> 98% (CHARGING)</div>
        </div>
      `;
    } else if (tabName === 'sensors') {
      const s = data.sensors || { ecg: true, spo2: true, nibp: true, temp1: true, temp2: true };
      const getConnStr = (sensorObj) => {
        const isConn = typeof sensorObj === 'object' && sensorObj !== null ? sensorObj.connected : Boolean(sensorObj);
        return isConn ? 'CONNECTED' : 'DISCONNECTED';
      };
      container.innerHTML = `
        <div style="line-height: 1.8;">
          <h4 style="color:#00ff66; margin-bottom:10px;">PATIENT SENSOR SOCKET STATUS</h4>
          <div>ECG 5-LEAD CABLE: <strong style="color:${getConnStr(s.ecg) === 'CONNECTED' ? '#00ff66' : '#ff3344'}">${getConnStr(s.ecg)}</strong></div>
          <div>SpO2 FINGER PROBE: <strong style="color:${getConnStr(s.spo2) === 'CONNECTED' ? '#00ff66' : '#ff3344'}">${getConnStr(s.spo2)}</strong></div>
          <div>NIBP BLOOD PRESSURE CUFF: <strong style="color:${getConnStr(s.nibp) === 'CONNECTED' ? '#00ff66' : '#ff3344'}">${getConnStr(s.nibp)}</strong></div>
          <div>TEMP PROBE T1: <strong style="color:${getConnStr(s.temp1 || s.temperature_t1) === 'CONNECTED' ? '#00ff66' : '#ff3344'}">${getConnStr(s.temp1 || s.temperature_t1)}</strong></div>
          <div>TEMP PROBE T2: <strong style="color:${getConnStr(s.temp2 || s.temperature_t2) === 'CONNECTED' ? '#00ff66' : '#ff3344'}">${getConnStr(s.temp2 || s.temperature_t2)}</strong></div>
        </div>
      `;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.displayRenderer = new DisplayRenderer();
});
