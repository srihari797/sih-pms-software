// Physical Controls & Rotary Dial Handler for CMS8000

class ControlsHandler {
  constructor() {
    this.powerState = 'MONITORING';
    this.rotaryAngle = 0;
    this.menuOpen = false;
    this.activeMenuTab = 'patient';
    this.menuTabsOrder = ['patient', 'alarms', 'trends', 'events', 'system', 'sensors'];
    this.bindEvents();
  }

  bindEvents() {
    // Power button
    const btnPower = document.getElementById('btnPower');
    if (btnPower) btnPower.addEventListener('click', () => this.togglePower());

    // Freeze button
    const btnFreeze = document.getElementById('btnFreeze');
    if (btnFreeze) {
      btnFreeze.addEventListener('click', async () => {
        const isFrozen = !window.displayRenderer.isFrozen;
        window.displayRenderer.setFrozen(isFrozen);
        window.audioSynth.playBeep(440, 0.05);
        try {
          await fetch('/api/v1/device/freeze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ frozen: isFrozen })
          });
        } catch (e) {
          console.error('Freeze error:', e);
        }
      });
    }

    // NIBP button
    const btnNIBP = document.getElementById('btnNIBP');
    if (btnNIBP) {
      btnNIBP.addEventListener('click', async () => {
        window.audioSynth.playBeep(523, 0.08);
        try {
          await fetch('/api/v1/control/nibp', { method: 'POST' });
        } catch (e) {
          console.error('NIBP trigger error:', e);
        }
      });
    }

    // Silence button
    const btnSilence = document.getElementById('btnSilence');
    if (btnSilence) {
      btnSilence.addEventListener('click', async () => {
        const isSilenced = window.audioSynth.toggleSilence();
        btnSilence.style.opacity = isSilenced ? '0.5' : '1.0';
        try {
          await fetch('/api/v1/device/silence', { method: 'POST' });
        } catch (e) {
          console.error('Silence error:', e);
        }
      });
    }

    // Menu button
    const btnMenu = document.getElementById('btnMenu');
    if (btnMenu) btnMenu.addEventListener('click', () => this.toggleMenu());

    const btnMenuClose = document.getElementById('btnMenuClose');
    if (btnMenuClose) btnMenuClose.addEventListener('click', () => this.closeMenu());

    // Menu tabs click handlers
    document.querySelectorAll('.menu-tab').forEach(tabBtn => {
      tabBtn.addEventListener('click', (e) => {
        const tab = e.target.getAttribute('data-tab');
        this.switchMenuTab(tab);
      });
    });

    // Thermal Recorder Print button
    const btnPrint = document.getElementById('btnPrint');
    if (btnPrint) btnPrint.addEventListener('click', () => this.printThermalReport());

    // Rotate View buttons (Front / Rear Panel)
    const btnRotateView = document.getElementById('btnRotateView');
    if (btnRotateView) btnRotateView.addEventListener('click', () => this.toggleRearView(true));

    const btnRotateBack = document.getElementById('btnRotateBack');
    if (btnRotateBack) btnRotateBack.addEventListener('click', () => this.toggleRearView(false));

    // Scenario buttons
    const scenButtons = {
      'btnScenNormal': 'NORMAL',
      'btnScenStressed': 'STRESSED',
      'btnScenDeteriorating': 'DETERIORATING',
      'btnScenCritical': 'CRITICAL'
    };

    Object.entries(scenButtons).forEach(([btnId, scenario]) => {
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.addEventListener('click', () => {
          this.selectScenario(scenario, btnId);
        });
      }
    });

    const btnEmergency = document.getElementById('btnScenEmergency');
    if (btnEmergency) {
      btnEmergency.addEventListener('click', async () => {
        window.audioSynth.playBeep(1200, 0.2, 'sawtooth');
        this.setActiveScenarioBtn('btnScenEmergency');
        try {
          await fetch('/api/v1/control/emergency', { method: 'POST' });
        } catch (e) {
          console.error('Emergency error:', e);
        }
      });
    }

    // Rotary knob rotation and click
    const rotaryKnob = document.getElementById('rotaryKnob');
    if (rotaryKnob) {
      rotaryKnob.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 15 : -15;
        this.rotateKnob(delta);
      });

      rotaryKnob.addEventListener('click', () => {
        window.audioSynth.playBeep(800, 0.04);
        if (!this.menuOpen) {
          this.toggleMenu();
        } else {
          // Cycle menu tabs with rotary knob click
          const currIdx = this.menuTabsOrder.indexOf(this.activeMenuTab);
          const nextIdx = (currIdx + 1) % this.menuTabsOrder.length;
          this.switchMenuTab(this.menuTabsOrder[nextIdx]);
        }
      });
    }
  }

  rotateKnob(delta) {
    this.rotaryAngle = (this.rotaryAngle + delta) % 360;
    const knob = document.getElementById('rotaryKnob');
    if (knob) knob.style.transform = `rotate(${this.rotaryAngle}deg)`;
    window.audioSynth.playBeep(1200, 0.01);

    if (this.menuOpen) {
      const step = delta > 0 ? 1 : -1;
      const currIdx = this.menuTabsOrder.indexOf(this.activeMenuTab);
      let nextIdx = (currIdx + step) % this.menuTabsOrder.length;
      if (nextIdx < 0) nextIdx = this.menuTabsOrder.length - 1;
      this.switchMenuTab(this.menuTabsOrder[nextIdx]);
    }
  }

  toggleRearView(showRear) {
    window.audioSynth.playBeep(500, 0.05);
    const frontChassis = document.getElementById('monitorChassis');
    const rearChassis = document.getElementById('rearChassis');

    if (showRear) {
      if (frontChassis) frontChassis.classList.add('hidden');
      if (rearChassis) rearChassis.classList.remove('hidden');
    } else {
      if (rearChassis) rearChassis.classList.add('hidden');
      if (frontChassis) frontChassis.classList.remove('hidden');
    }
  }

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
    const overlay = document.getElementById('embeddedMenuOverlay');
    if (overlay) overlay.classList.toggle('hidden', !this.menuOpen);
    if (this.menuOpen) {
      this.switchMenuTab(this.activeMenuTab);
    }
  }

  closeMenu() {
    this.menuOpen = false;
    const overlay = document.getElementById('embeddedMenuOverlay');
    if (overlay) overlay.classList.add('hidden');
  }

  async switchMenuTab(tabName) {
    this.activeMenuTab = tabName;
    document.querySelectorAll('.menu-tab').forEach(tab => {
      tab.classList.toggle('active', tab.getAttribute('data-tab') === tabName);
    });

    let extraData = {};
    if (tabName === 'trends') {
      try {
        const res = await fetch('/api/v1/device/trends?limit=10');
        extraData.trends = await res.json();
      } catch (e) { console.error(e); }
    } else if (tabName === 'events') {
      try {
        const res = await fetch('/api/v1/device/events?limit=10');
        extraData.events = await res.json();
      } catch (e) { console.error(e); }
    } else if (tabName === 'sensors') {
      try {
        const res = await fetch('/api/v1/device/status');
        extraData = await res.json();
      } catch (e) { console.error(e); }
    }

    window.displayRenderer.renderMenuContent(tabName, extraData);
  }

  async printThermalReport() {
    window.audioSynth.playBeep(700, 0.1);
    const strip = document.getElementById('printedPaperStrip');
    const body = document.getElementById('paperBody');
    if (strip) strip.classList.remove('hidden');
    if (body) body.innerText = 'PRINTING VITAL STRIP...';

    try {
      const res = await fetch('/api/v1/device/print', { method: 'POST' });
      const report = await res.json();
      const vitals = report.vitals || {};
      
      if (body) {
        body.innerHTML = `
          <div><strong>TIME:</strong> ${(vitals.recorded_at || '').substring(11, 19)}</div>
          <div><strong>HR:</strong> ${vitals.hr || '--'} bpm</div>
          <div><strong>SpO₂:</strong> ${vitals.spo2 || '--'} %</div>
          <div><strong>NIBP:</strong> ${vitals.sys || '--'}/${vitals.dia || '--'} mmHg</div>
          <div><strong>RESP:</strong> ${vitals.rr || '--'} /min</div>
          <div><strong>TEMP:</strong> ${vitals.temp1 || '--'} °C</div>
          <div style="margin-top:4px;font-weight:bold;">-- STRIP COMPLETE --</div>
        `;
      }
    } catch (e) {
      if (body) body.innerText = 'ERROR PRINTING STRIP';
    }

    setTimeout(() => {
      if (strip) strip.classList.add('hidden');
    }, 6000);
  }

  async selectScenario(scenario, btnId) {
    window.audioSynth.playBeep(600, 0.05);
    this.setActiveScenarioBtn(btnId);
    try {
      await fetch('/api/v1/control/scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      });
    } catch (e) {
      console.error('Scenario error:', e);
    }
  }

  setActiveScenarioBtn(activeId) {
    document.querySelectorAll('.scen-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById(activeId);
    if (btn) btn.classList.add('active');
  }

  async togglePower() {
    window.audioSynth.playBeep(300, 0.1);
    const nextState = this.powerState === 'MONITORING' ? 'POWER_OFF' : 'BOOTING';

    const powerOffEl = document.getElementById('powerOffScreen');
    const bootEl = document.getElementById('bootScreen');

    if (nextState === 'BOOTING') {
      if (powerOffEl) powerOffEl.style.display = 'none';
      if (bootEl) bootEl.style.display = 'flex';
      const bootText = document.getElementById('bootStatusText');
      if (bootText) bootText.innerText = 'INITIALIZING CMS8000 SYSTEM...';

      setTimeout(async () => {
        if (bootEl) bootEl.style.display = 'none';
        this.powerState = 'MONITORING';
        await fetch('/api/v1/control/power', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ state: 'MONITORING' })
        });
      }, 2500);

    } else {
      if (powerOffEl) powerOffEl.style.display = 'flex';
      this.powerState = 'POWER_OFF';
      await fetch('/api/v1/control/power', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: 'POWER_OFF' })
      });
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.controlsHandler = new ControlsHandler();
});
