// Procedural 3D CMS8000 Patient Monitor Geometry Builder using Three.js

class CMS8000Model3D {
  constructor(scene) {
    this.scene = scene;
    this.screenCanvas = window.monitorScreen2D.canvas;

    // Interactive 3D Objects Registry for Raycasting
    this.interactiveObjects = [];
    this.buttonsMap = {};
    this.socketsMap = {};
    this.cablesMap = {};

    // Create CanvasTexture for live monitor screen
    this.screenTexture = new THREE.CanvasTexture(this.screenCanvas);
    this.screenTexture.minFilter = THREE.LinearFilter;
    this.screenTexture.magFilter = THREE.LinearFilter;

    // Group holding entire 3D CMS8000 device
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Materials (Matching physical CMS8000 white body, blue buttons)
    this.initMaterials();

    // Build 3D Components
    this.buildChassis();
    this.buildHandle();
    this.buildScreen();
    this.buildAlarmLamp();
    this.buildButtons();
    this.buildRotaryKnob();
    this.buildSpeakerGrill();
    this.buildSideSockets();
    this.buildCables();
    this.buildRearPanel();
    this.buildPrinterSlot();
    this.buildFeet();
  }

  initMaterials() {
    this.materials = {
      chassisPlastic: new THREE.MeshStandardMaterial({
        color: 0xf0f2f5,
        roughness: 0.35,
        metalness: 0.05
      }),
      bezelPlastic: new THREE.MeshStandardMaterial({
        color: 0x151a20,
        roughness: 0.5,
        metalness: 0.1
      }),
      screenGlass: new THREE.MeshStandardMaterial({
        map: this.screenTexture,
        roughness: 0.15,
        metalness: 0.05
      }),
      buttonLightBlue: new THREE.MeshStandardMaterial({
        color: 0x29b6f6,
        roughness: 0.4,
        metalness: 0.1
      }),
      buttonPowerRed: new THREE.MeshStandardMaterial({
        color: 0xe53935,
        roughness: 0.4,
        metalness: 0.1
      }),
      buttonNibpYellow: new THREE.MeshStandardMaterial({
        color: 0xfbc02d,
        roughness: 0.4,
        metalness: 0.1
      }),
      rotaryBlue: new THREE.MeshStandardMaterial({
        color: 0x0277bd,
        roughness: 0.3,
        metalness: 0.4
      }),
      socketMetal: new THREE.MeshStandardMaterial({
        color: 0x222830,
        roughness: 0.2,
        metalness: 0.8
      }),
      cableGreen: new THREE.MeshStandardMaterial({
        color: 0x00e676,
        roughness: 0.3,
        metalness: 0.1
      }),
      alarmLamp: new THREE.MeshStandardMaterial({
        color: 0x00e676,
        emissive: 0x00e676,
        emissiveIntensity: 0.5,
        roughness: 0.1
      }),
      paperWhite: new THREE.MeshStandardMaterial({
        color: 0xfffdf5,
        roughness: 0.9,
        metalness: 0.0
      }),
      metalDark: new THREE.MeshStandardMaterial({
        color: 0x2b3440,
        roughness: 0.4,
        metalness: 0.7
      })
    };
  }

  buildChassis() {
    // Main Body Box (Width: 10, Height: 7.5, Depth: 4)
    const bodyGeo = new THREE.BoxGeometry(10, 7.5, 4);
    const bodyMesh = new THREE.Mesh(bodyGeo, this.materials.chassisPlastic);
    bodyMesh.castShadow = true;
    bodyMesh.receiveShadow = true;
    this.group.add(bodyMesh);

    // Front Bezel Frame
    const bezelGeo = new THREE.BoxGeometry(9.4, 6.9, 0.4);
    const bezelMesh = new THREE.Mesh(bezelGeo, this.materials.bezelPlastic);
    bezelMesh.position.set(0, 0.1, 1.9);
    bezelMesh.castShadow = true;
    this.group.add(bezelMesh);
  }

  buildHandle() {
    // Top Carrying Handle Bar (White Plastic)
    const handleGeo = new THREE.CylinderGeometry(0.25, 0.25, 5.2, 16);
    const handleMesh = new THREE.Mesh(handleGeo, this.materials.chassisPlastic);
    handleMesh.rotation.z = Math.PI / 2;
    handleMesh.position.set(0, 4.2, 0);
    handleMesh.castShadow = true;
    this.group.add(handleMesh);

    // Handle Mount Pillars
    const pillar1 = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.8, 16), this.materials.chassisPlastic);
    pillar1.position.set(-2.2, 3.8, 0);
    const pillar2 = pillar1.clone();
    pillar2.position.set(2.2, 3.8, 0);
    this.group.add(pillar1);
    this.group.add(pillar2);
  }

  buildScreen() {
    // Display Screen Mesh mapped with Live CanvasTexture
    const screenGeo = new THREE.PlaneGeometry(6.6, 4.4);
    this.screenMesh = new THREE.Mesh(screenGeo, this.materials.screenGlass);
    this.screenMesh.position.set(-1.1, 0.8, 2.12);
    this.group.add(this.screenMesh);
  }

  buildAlarmLamp() {
    // Top Right Alarm Indicator Lamp Bar
    const lampGeo = new THREE.BoxGeometry(1.6, 0.4, 0.3);
    this.alarmLampMesh = new THREE.Mesh(lampGeo, this.materials.alarmLamp);
    this.alarmLampMesh.position.set(3.4, 3.2, 2.05);
    this.group.add(this.alarmLampMesh);
  }

  buildButtons() {
    // Button Definitions matching physical CMS8000 front panel
    const buttonDefs = [
      ['btnPower', 'POWER', this.materials.buttonPowerRed, -3.8, -2.4, 'power'],
      ['btnFreeze', 'FREEZE', this.materials.buttonLightBlue, -2.4, -2.4, 'freeze'],
      ['btnNIBP', 'NIBP', this.materials.buttonNibpYellow, -1.0, -2.4, 'nibp'],
      ['btnSilence', 'SILENCE', this.materials.buttonLightBlue, 0.4, -2.4, 'silence'],
      ['btnMenu', 'MENU', this.materials.buttonLightBlue, 1.8, -2.4, 'menu'],
      ['btnPrint', 'PRINT', this.materials.buttonLightBlue, 3.2, -2.4, 'print']
    ];

    buttonDefs.forEach(([id, label, mat, x, y, key]) => {
      const btnGeo = new THREE.BoxGeometry(1.1, 0.5, 0.3);
      const btnMesh = new THREE.Mesh(btnGeo, mat);
      btnMesh.position.set(x, y, 2.1);
      btnMesh.name = id;
      btnMesh.userData = { isButton: true, key: key, originalZ: 2.1 };
      
      this.group.add(btnMesh);
      this.interactiveObjects.push(btnMesh);
      this.buttonsMap[key] = btnMesh;
    });
  }

  buildRotaryKnob() {
    // 3D Blue Rotary Encoder Dial
    const knobGeo = new THREE.CylinderGeometry(0.7, 0.7, 0.5, 32);
    this.rotaryMesh = new THREE.Mesh(knobGeo, this.materials.rotaryBlue);
    this.rotaryMesh.rotation.x = Math.PI / 2;
    this.rotaryMesh.position.set(3.4, 0.6, 2.2);
    this.rotaryMesh.name = 'rotaryKnob';
    this.rotaryMesh.userData = { isRotary: true };

    // Radial Indicator Notch
    const notchGeo = new THREE.BoxGeometry(0.1, 0.35, 0.52);
    const notchMesh = new THREE.Mesh(notchGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }));
    notchMesh.position.set(0, 0.35, 0);
    this.rotaryMesh.add(notchMesh);

    this.group.add(this.rotaryMesh);
    this.interactiveObjects.push(this.rotaryMesh);
  }

  buildSpeakerGrill() {
    // 3D Speaker Grill Slits on Right Bezel
    for (let i = 0; i < 5; i++) {
      const slitGeo = new THREE.BoxGeometry(0.8, 0.06, 0.1);
      const slitMesh = new THREE.Mesh(slitGeo, this.materials.metalDark);
      slitMesh.position.set(3.4, -0.6 - (i * 0.15), 2.05);
      this.group.add(slitMesh);
    }
  }

  buildSideSockets() {
    // Color-coded Side Sockets (Yellow SpO2, Green ECG, White NIBP, Blue Temp1, Pink Temp2)
    const socketDefs = [
      ['ecg', 'ECG 5-LEAD', 2.2, 0x00ff41],
      ['spo2', 'SpO2 PROBE', 1.1, 0xffee00],
      ['nibp', 'NIBP CUFF', 0.0, 0xffffff],
      ['temp1', 'TEMP T1', -1.1, 0x00f0ff],
      ['temp2', 'TEMP T2', -2.2, 0xff00ea]
    ];

    socketDefs.forEach(([key, label, y, socketColor]) => {
      const socketMat = new THREE.MeshStandardMaterial({ color: socketColor, metalness: 0.6, roughness: 0.3 });
      const socketGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.4, 16);
      const socketMesh = new THREE.Mesh(socketGeo, socketMat);
      socketMesh.rotation.z = Math.PI / 2;
      socketMesh.position.set(-5.05, y, 0.5);
      socketMesh.name = `socket_${key}`;
      socketMesh.userData = { isSocket: true, sensorKey: key };

      this.group.add(socketMesh);
      this.interactiveObjects.push(socketMesh);
      this.socketsMap[key] = socketMesh;
    });
  }

  buildCables() {
    // 3D Flexible Curve Tube Cables
    const socketKeys = ['ecg', 'spo2', 'nibp', 'temp1', 'temp2'];
    const yPosMap = { ecg: 2.2, spo2: 1.1, nibp: 0.0, temp1: -1.1, temp2: -2.2 };

    socketKeys.forEach(key => {
      const y = yPosMap[key];
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-5.1, y, 0.5),
        new THREE.Vector3(-6.2, y - 0.2, 0.8),
        new THREE.Vector3(-6.8, y - 1.5, 0.5),
        new THREE.Vector3(-7.2, y - 3.0, 0.0)
      ]);

      const tubeGeo = new THREE.TubeGeometry(curve, 20, 0.12, 8, false);
      const cableMesh = new THREE.Mesh(tubeGeo, this.materials.cableGreen);
      cableMesh.name = `cable_${key}`;

      const plugGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.8, 16);
      const plugMesh = new THREE.Mesh(plugGeo, this.materials.metalDark);
      plugMesh.rotation.z = Math.PI / 2;
      plugMesh.position.set(-5.6, y, 0.5);

      const cableGroup = new THREE.Group();
      cableGroup.add(cableMesh);
      cableGroup.add(plugMesh);
      cableGroup.userData = { isConnected: true, sensorKey: key };

      this.group.add(cableGroup);
      this.cablesMap[key] = cableGroup;
    });
  }

  buildRearPanel() {
    // Rear Panel Interfaces (AC Power, RJ45 Ethernet, USB, Ground Post, Vents)
    const acGeo = new THREE.BoxGeometry(0.3, 0.8, 1.2);
    const acMesh = new THREE.Mesh(acGeo, this.materials.socketMetal);
    acMesh.position.set(-2.5, -1.5, -2.05);
    this.group.add(acMesh);

    const rjGeo = new THREE.BoxGeometry(0.3, 0.6, 0.8);
    const rjMesh = new THREE.Mesh(rjGeo, this.materials.metalDark);
    rjMesh.position.set(-0.5, -1.5, -2.05);
    this.group.add(rjMesh);

    const usbGeo = new THREE.BoxGeometry(0.3, 0.4, 0.6);
    const usbMesh = new THREE.Mesh(usbGeo, this.materials.metalDark);
    usbMesh.position.set(1.2, -1.5, -2.05);
    this.group.add(usbMesh);

    const groundGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.4, 16);
    const groundMesh = new THREE.Mesh(groundGeo, new THREE.MeshStandardMaterial({ color: 0xffaa00, metalness: 0.8 }));
    groundMesh.rotation.x = Math.PI / 2;
    groundMesh.position.set(2.8, -1.5, -2.1);
    this.group.add(groundMesh);

    for (let i = 0; i < 8; i++) {
      const ventGeo = new THREE.BoxGeometry(0.08, 2.0, 0.1);
      const ventMesh = new THREE.Mesh(ventGeo, this.materials.metalDark);
      ventMesh.position.set(-3.0 + (i * 0.3), 1.2, -2.02);
      this.group.add(ventMesh);
    }
  }

  buildPrinterSlot() {
    const slotGeo = new THREE.BoxGeometry(1.6, 0.08, 0.2);
    const slotMesh = new THREE.Mesh(slotGeo, this.materials.metalDark);
    slotMesh.position.set(3.4, -1.6, 2.05);
    this.group.add(slotMesh);

    const paperGeo = new THREE.PlaneGeometry(1.4, 2.0);
    this.paperMesh = new THREE.Mesh(paperGeo, this.materials.paperWhite);
    this.paperMesh.position.set(3.4, -2.5, 2.08);
    this.paperMesh.rotation.x = -0.2;
    this.paperMesh.visible = false;
    this.group.add(this.paperMesh);
  }

  buildFeet() {
    const footPositions = [
      [-4, -3.9, 1.5],
      [4, -3.9, 1.5],
      [-4, -3.9, -1.5],
      [4, -3.9, -1.5]
    ];

    footPositions.forEach(([x, y, z]) => {
      const footGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
      const footMesh = new THREE.Mesh(footGeo, this.materials.metalDark);
      footMesh.position.set(x, y, z);
      this.group.add(footMesh);
    });
  }

  updateScreenTexture() {
    if (this.screenTexture) {
      this.screenTexture.needsUpdate = true;
    }
  }

  setAlarmState(level) {
    if (level === 'CRITICAL') {
      this.materials.alarmLamp.color.setHex(0xff2233);
      this.materials.alarmLamp.emissive.setHex(0xff2233);
      this.materials.alarmLamp.emissiveIntensity = 0.9;
    } else if (level === 'WARNING') {
      this.materials.alarmLamp.color.setHex(0xffaa00);
      this.materials.alarmLamp.emissive.setHex(0xffaa00);
      this.materials.alarmLamp.emissiveIntensity = 0.7;
    } else {
      this.materials.alarmLamp.color.setHex(0x00e676);
      this.materials.alarmLamp.emissive.setHex(0x00e676);
      this.materials.alarmLamp.emissiveIntensity = 0.4;
    }
  }

  setSensorCableConnected(sensorKey, connected) {
    const cableGroup = this.cablesMap[sensorKey];
    if (cableGroup) {
      cableGroup.position.x = connected ? 0 : -1.2;
      cableGroup.userData.isConnected = connected;
    }
  }

  triggerPrintAnimation() {
    this.paperMesh.visible = true;
    this.paperMesh.position.y = -1.8;
    
    let step = 0;
    const interval = setInterval(() => {
      step += 0.05;
      this.paperMesh.position.y -= 0.05;
      if (step >= 1.0) {
        clearInterval(interval);
        setTimeout(() => {
          this.paperMesh.visible = false;
        }, 5000);
      }
    }, 50);
  }

  animateButtonPress(btnMesh) {
    if (!btnMesh) return;
    const origZ = btnMesh.userData.originalZ || 2.1;
    btnMesh.position.z = origZ - 0.08;
    setTimeout(() => {
      btnMesh.position.z = origZ;
    }, 150);
  }

  rotateKnob(angleDelta) {
    if (this.rotaryMesh) {
      this.rotaryMesh.rotation.z += angleDelta;
    }
  }
}

window.CMS8000Model3D = CMS8000Model3D;
