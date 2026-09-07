// Master 2D Screen Canvas Renderer for CMS8000 LCD Display (1024x680)

class MonitorScreen2D {
  constructor() {
    this.canvas = document.createElement('canvas');
    this.canvas.width = 1024;
    this.canvas.height = 680;
    this.ctx = this.canvas.getContext('2d');

    // Sample buffers for continuous right-to-left sweep
    this.ecgBuffer = [];
    this.respBuffer = [];
    this.plethBuffer = [];

    // Sweep cursor X positions
    this.ecgX = 0;
    this.respX = 0;
    this.plethX = 0;
    this.sweepSpeed = 2.5;

    this.isFrozen = false;
    this.menuOpen = false;
    this.activeMenuTab = 'patient';
    this.menuData = {};

    // Central Monitor State
    this.state = {
      patientId: 'P001',
      patientName: 'DOE, JOHN',
      bedNo: 'BED-04',
      mode: 'ADULT',
      clockStr: '2026-09-06 12:00:00',
      alarmText: 'NO ALARM — MONITORING ACTIVE',
      alarmLevel: 'NORMAL',
      hr: 82,
      spo2: 98,
      pr: 82,
      sys: 120,
      dia: 80,
      map: 93,
      nibpStatus: 'IDLE',
      rr: 18,
      t1: 36.8,
      t2: 36.9,
      source: 'SIMULATOR',
      sensors: { ecg: true, spo2: true, nibp: true, temp1: true, temp2: true }
    };

    // Offscreen wave sweep canvases for flicker-free rendering
    this.waveCanvas = document.createElement('canvas');
    this.waveCanvas.width = 720;
    this.waveCanvas.height = 540;
    this.waveCtx = this.waveCanvas.getContext('2d');
    this.clearWaveCanvas();
  }

  clearWaveCanvas() {
    this.waveCtx.fillStyle = '#010805';
    this.waveCtx.fillRect(0, 0, 720, 540);
    // Draw medical waveform grid
    this.waveCtx.strokeStyle = '#05180f';
    this.waveCtx.lineWidth = 1;
    for (let x = 0; x < 720; x += 20) {
      this.waveCtx.beginPath();
      this.waveCtx.moveTo(x, 0);
      this.waveCtx.lineTo(x, 540);
      this.waveCtx.stroke();
    }
    for (let y = 0; y < 540; y += 20) {
      this.waveCtx.beginPath();
      this.waveCtx.moveTo(0, y);
      this.waveCtx.lineTo(720, y);
      this.waveCtx.stroke();
    }
  }

  setFrozen(frozen) {
    this.isFrozen = frozen;
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

  updateState(newState) {
    this.state = { ...this.state, ...newState };
  }

  render() {
    const ctx = this.ctx;
    ctx.fillStyle = '#020b08';
    ctx.fillRect(0, 0, 1024, 680);

    // 1. Draw Top Screen Status Bar
    this.drawTopBar();

    // 2. Draw Alarm Banner Bar
    this.drawAlarmBanner();

    // 3. Draw Continuous Waveform Sweep (ECG, RESP, PLETH)
    this.drawWaveforms();
    ctx.drawImage(this.waveCanvas, 10, 75, 710, 550);

    // 4. Draw Right Parameter Readout Blocks
    this.drawParameterBlocks();

    // 5. Draw Bottom Status Bar
    this.drawBottomBar();

    // 6. Draw Embedded Screen Menu if Open
    if (this.menuOpen) {
      this.drawEmbeddedMenu();
    }
  }

  drawTopBar() {
    const ctx = this.ctx;
    ctx.fillStyle = '#061610';
    ctx.fillRect(0, 0, 1024, 34);
    ctx.strokeStyle = '#0d2e20';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, 1024, 34);

    ctx.font = 'bold 13px -apple-system, sans-serif';
    ctx.fillStyle = '#00e676';
    ctx.fillText('CMS8000 PATIENT MONITORING SYSTEM', 16, 22);

    ctx.font = 'bold 12px "Courier New", monospace';
    ctx.fillStyle = '#00cc66';
    const now = new Date();
    const timeStr = now.toISOString().replace('T', ' ').substring(0, 19);
    ctx.fillText(timeStr, 840, 22);
  }

  drawAlarmBanner() {
    const ctx = this.ctx;
    const level = this.state.alarmLevel;
    if (level === 'CRITICAL') {
      ctx.fillStyle = '#4d0008';
      ctx.fillRect(0, 34, 1024, 32);
      ctx.font = 'bold 14px -apple-system, sans-serif';
      ctx.fillStyle = '#ff3344';
      ctx.fillText(`⚠️ *** CRITICAL ALARM *** : ${this.state.alarmText}`, 320, 56);
    } else if (level === 'WARNING') {
      ctx.fillStyle = '#3d2a00';
      ctx.fillRect(0, 34, 1024, 32);
      ctx.font = 'bold 14px -apple-system, sans-serif';
      ctx.fillStyle = '#ffbb00';
      ctx.fillText(`⚠️ WARNING : ${this.state.alarmText}`, 350, 56);
    } else {
      ctx.fillStyle = '#03140d';
      ctx.fillRect(0, 34, 1024, 32);
      ctx.font = 'bold 13px -apple-system, sans-serif';
      ctx.fillStyle = '#00e676';
      ctx.fillText('NO ALARM — MONITORING ACTIVE', 400, 56);
    }
  }

  drawWaveforms() {
    if (this.isFrozen) return;

    const wCtx = this.waveCtx;
    const width = 720;

    // ECG Lead II (Green)
    this.drawChannel(wCtx, this.ecgBuffer, '#00ff41', 100, 0.45, 'ecgX', 'II ECG x1.0', 16);

    // RESP (Yellow)
    this.drawChannel(wCtx, this.respBuffer, '#ffee00', 280, 0.35, 'respX', 'RESP x1.0', 196);

    // PLETH (Cyan)
    this.drawChannel(wCtx, this.plethBuffer, '#00f0ff', 450, 0.35, 'plethX', 'PLETH', 366);
  }

  drawChannel(wCtx, buffer, color, centerY, scale, xKey, label, labelY) {
    if (buffer.length === 0) return;

    const width = 720;
    const samplesToDraw = Math.min(buffer.length, 4);

    // Channel Title
    wCtx.fillStyle = color;
    wCtx.font = 'bold 12px -apple-system, sans-serif';
    wCtx.fillText(label, 12, labelY);

    for (let i = 0; i < samplesToDraw; i++) {
      const sample = buffer.shift();
      const nextX = (this[xKey] || 0) + this.sweepSpeed;
      const nextY = centerY - (sample * 80 * scale);

      // Erase ahead sweep gap
      wCtx.fillStyle = '#010805';
      wCtx.fillRect(nextX, centerY - 80, 16, 160);

      // Redraw gridlines in erase gap
      wCtx.strokeStyle = '#05180f';
      wCtx.lineWidth = 1;
      for (let gy = centerY - 80; gy <= centerY + 80; gy += 20) {
        wCtx.beginPath();
        wCtx.moveTo(nextX, gy);
        wCtx.lineTo(nextX + 16, gy);
        wCtx.stroke();
      }

      // Draw Wave Segment
      wCtx.beginPath();
      wCtx.strokeStyle = color;
      wCtx.lineWidth = 2.0;
      wCtx.shadowColor = color;
      wCtx.shadowBlur = 4;
      wCtx.moveTo(this[xKey] || 0, this[`prevY_${xKey}`] || centerY);
      wCtx.lineTo(nextX, nextY);
      wCtx.stroke();

      this[xKey] = nextX >= width ? 0 : nextX;
      this[`prevY_${xKey}`] = nextY;
    }
  }

  drawParameterBlocks() {
    const ctx = this.ctx;
    const left = 730;
    const width = 280;

    // 1. HR BOX (Green)
    this.drawParamBox(ctx, left, 75, width, 100, '#00ff41', 'HR', 'bpm', this.state.hr, '120 / 50');

    // 2. SpO2 & PR BOX (Cyan)
    this.drawParamBox(ctx, left, 185, width, 100, '#00f0ff', 'SpO₂', '%', this.state.spo2, `PR: ${this.state.pr || '--'} bpm`);

    // 3. NIBP BOX (Orange)
    const bpStr = this.state.sys && this.state.dia ? `${this.state.sys}/${this.state.dia}` : '--/--';
    this.drawParamBox(ctx, left, 295, width, 115, '#ff9900', 'NIBP', 'mmHg', bpStr, `MAP: ${this.state.map || '--'}`);
    // NIBP Badge
    ctx.fillStyle = '#332000';
    ctx.fillRect(left + 12, 380, 70, 20);
    ctx.fillStyle = '#ffaa00';
    ctx.font = 'bold 10px sans-serif';
    ctx.fillText(this.state.nibpStatus, left + 20, 394);

    // 4. RESP BOX (Yellow)
    this.drawParamBox(ctx, left, 420, width, 100, '#ffee00', 'RESP', '/min', this.state.rr, '30 / 10');

    // 5. TEMP BOX (Pink)
    ctx.fillStyle = '#03120c';
    ctx.fillRect(left, 530, width, 95);
    ctx.strokeStyle = '#ff00ea';
    ctx.lineWidth = 1;
    ctx.strokeRect(left, 530, width, 95);
    ctx.fillStyle = '#ff00ea';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText('TEMP', left + 12, 550);
    ctx.fillText('°C', left + width - 30, 550);
    ctx.font = 'bold 22px "Courier New", monospace';
    ctx.fillText(`T1: ${this.state.t1 || '--.-'}`, left + 100, 575);
    ctx.fillText(`T2: ${this.state.t2 || '--.-'}`, left + 100, 605);
  }

  drawParamBox(ctx, x, y, width, height, color, title, unit, value, subText) {
    ctx.fillStyle = '#03120c';
    ctx.fillRect(x, y, width, height);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, width, height);

    ctx.fillStyle = color;
    ctx.font = 'bold 14px -apple-system, sans-serif';
    ctx.fillText(title, x + 12, y + 22);

    ctx.font = 'bold 11px sans-serif';
    ctx.fillText(unit, x + width - 40, y + 22);

    ctx.font = 'bold 36px "Courier New", monospace';
    ctx.textAlign = 'right';
    ctx.fillText(value !== null && value !== undefined ? value : '--', x + width - 16, y + 68);

    ctx.font = 'bold 11px sans-serif';
    ctx.fillStyle = '#88aa99';
    ctx.fillText(subText, x + width - 16, y + 90);
    ctx.textAlign = 'left';
  }

  drawBottomBar() {
    const ctx = this.ctx;
    ctx.fillStyle = '#061610';
    ctx.fillRect(0, 635, 1024, 45);
    ctx.strokeStyle = '#0d2e20';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 635, 1024, 45);

    ctx.font = 'bold 12px -apple-system, sans-serif';
    ctx.fillStyle = '#00cc66';
    ctx.fillText(`MONITORING ACTIVE — SOURCE: ${this.state.source}`, 20, 662);

    if (this.isFrozen) {
      ctx.fillStyle = '#0044cc';
      ctx.fillRect(900, 645, 100, 26);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 13px sans-serif';
      ctx.fillText('FREEZE', 924, 663);
    }
  }

  drawEmbeddedMenu() {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(4, 18, 12, 0.95)';
    ctx.fillRect(60, 60, 904, 560);
    ctx.strokeStyle = '#00e676';
    ctx.lineWidth = 2;
    ctx.strokeRect(60, 60, 904, 560);

    // Menu Header
    ctx.fillStyle = '#00ff66';
    ctx.font = 'bold 18px sans-serif';
    ctx.fillText('MONITOR MAIN MENU', 80, 96);

    // Tabs
    const tabs = ['PATIENT', 'ALARMS', 'TRENDS', 'EVENTS', 'SYSTEM', 'SENSORS'];
    tabs.forEach((tab, i) => {
      const tabX = 80 + (i * 140);
      const isSelected = this.activeMenuTab === tab.toLowerCase();
      ctx.fillStyle = isSelected ? '#00e676' : '#092015';
      ctx.fillRect(tabX, 115, 130, 32);
      ctx.strokeStyle = '#0d4229';
      ctx.strokeRect(tabX, 115, 130, 32);

      ctx.fillStyle = isSelected ? '#000000' : '#77bba0';
      ctx.font = 'bold 12px sans-serif';
      ctx.fillText(tab, tabX + 24, 136);
    });

    // Content Body Area
    ctx.fillStyle = '#020d09';
    ctx.fillRect(80, 150, 864, 440);
    ctx.strokeStyle = '#0d3824';
    ctx.strokeRect(80, 150, 864, 440);

    ctx.fillStyle = '#00ee77';
    ctx.font = '14px sans-serif';
    ctx.fillText(`CURRENT VIEW: ${this.activeMenuTab.toUpperCase()} CONFIGURATION`, 100, 190);
  }
}

window.monitorScreen2D = new MonitorScreen2D();
