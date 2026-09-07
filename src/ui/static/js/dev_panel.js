// Developer Panel Debugger Handler

class DevPanelHandler {
  constructor() {
    this.packetCount = 0;
    this.container = document.getElementById('devPanel');
    this.toggleBtn = document.getElementById('btnToggleDev');

    this.toggleBtn.addEventListener('click', () => {
      this.container.classList.toggle('collapsed');
    });
  }

  updateWsStatus(connected) {
    const el = document.getElementById('devWsStatus');
    el.innerText = connected ? 'CONNECTED (REALTIME WS)' : 'DISCONNECTED';
    el.style.color = connected ? '#00ff66' : '#ff3344';
  }

  logPayload(data) {
    this.packetCount++;
    document.getElementById('devPacketCount').innerText = this.packetCount;

    if (data.session_id) {
      document.getElementById('devSessionId').innerText = data.session_id;
    }
    if (data.source) {
      document.getElementById('devSource').innerText = data.source;
    }

    document.getElementById('devJsonPreview').innerText = JSON.stringify(data, null, 2);
  }
}

window.devPanelHandler = new DevPanelHandler();
