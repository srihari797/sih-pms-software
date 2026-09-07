// Three.js 3D Scene Manager & Interactive Orbit Camera Controls

class Scene3DManager {
  constructor() {
    this.container = document.getElementById('canvas3dContainer');
    this.canvas = document.getElementById('canvas3d');

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0d1116);

    this.initCamera();
    this.initRenderer();
    this.initLighting();
    this.initFloor();
    this.initControls();

    // Instantiate Procedural 3D CMS8000 Device Model
    this.model = new CMS8000Model3D(this.scene);

    this.initRaycaster();
    this.bindViewPresetButtons();

    // Camera animation state
    this.isAnimatingCamera = false;
    this.targetCameraPos = new THREE.Vector3();
    this.targetLookAt = new THREE.Vector3();

    // Start 60 FPS WebGL Animation Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);

    // Handle Window Resize
    window.addEventListener('resize', () => this.onWindowResize());
  }

  initCamera() {
    const width = this.container.clientWidth || 980;
    const height = this.container.clientHeight || 560;
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    
    // Default View: Scaled close so 3D machine fills 75-85% of viewport
    this.camera.position.set(2.5, 1.8, 9.5);
  }

  initRenderer() {
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: "high-performance"
    });
    const width = this.container.clientWidth || 980;
    const height = this.container.clientHeight || 560;
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }

  initLighting() {
    // Ambient Studio Light
    const ambient = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(ambient);

    // Main Directional Key Light with Soft Shadow
    const keyLight = new THREE.DirectionalLight(0xffffff, 0.9);
    keyLight.position.set(8, 12, 10);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.bias = -0.0001;
    this.scene.add(keyLight);

    // Soft Fill Light
    const fillLight = new THREE.DirectionalLight(0xb0c4de, 0.4);
    fillLight.position.set(-8, 6, -8);
    this.scene.add(fillLight);

    // Rim Light (Highlights Bevel Edges)
    const rimLight = new THREE.DirectionalLight(0x00c6ff, 0.35);
    rimLight.position.set(0, -8, -10);
    this.scene.add(rimLight);
  }

  initFloor() {
    // Studio Floor & Contact Shadow
    const floorGeo = new THREE.PlaneGeometry(50, 50);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x141a22,
      roughness: 0.8,
      metalness: 0.2
    });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.position.y = -4.1;
    floorMesh.receiveShadow = true;
    this.scene.add(floorMesh);
  }

  initControls() {
    // OrbitControls for 360-degree rotation, zoom, pan, damping
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2 + 0.1;
    this.controls.minDistance = 4;
    this.controls.maxDistance = 20;
    this.controls.target.set(0, 0, 0);
  }

  initRaycaster() {
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Mouse Move (Hover Feedback)
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObjects(this.model.interactiveObjects);

      if (intersects.length > 0) {
        this.canvas.style.cursor = 'pointer';
      } else {
        this.canvas.style.cursor = 'default';
      }
    });

    // Mouse Click (3D Object Raycasting Interaction)
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObjects(this.model.interactiveObjects);

      if (intersects.length > 0) {
        const obj = intersects[0].object;
        this.handle3DObjectClick(obj);
      }
    });
  }

  handle3DObjectClick(obj) {
    if (!obj || !obj.userData) return;

    if (obj.userData.isButton) {
      // 3D Push Button Press Animation & Event Trigger
      this.model.animateButtonPress(obj);
      window.audioSynth.playBeep(600, 0.05);

      const key = obj.userData.key;
      if (key === 'power') window.controlsHandler.togglePower();
      else if (key === 'freeze') document.getElementById('btnFreeze').click();
      else if (key === 'nibp') document.getElementById('btnNIBP').click();
      else if (key === 'silence') document.getElementById('btnSilence').click();
      else if (key === 'menu') window.controlsHandler.toggleMenu();
      else if (key === 'print') window.controlsHandler.printThermalReport();

    } else if (obj.userData.isRotary) {
      // 3D Rotary Encoder Dial Turn
      this.model.rotateKnob(0.3);
      window.controlsHandler.toggleMenu();

    } else if (obj.userData.isSocket) {
      // 3D Side Socket Click
      const sensorKey = obj.userData.sensorKey;
      window.portsHandler.toggleSensor(sensorKey);
    }
  }

  bindViewPresetButtons() {
    const presets = {
      'btnPresetFront': [0, 0.5, 9.2],
      'btnPresetRear': [0, 0.5, -9.2],
      'btnPresetLeft': [-9.5, 0.5, 0],
      'btnPresetRight': [9.5, 0.5, 0],
      'btnPresetReset': [2.5, 1.8, 9.5]
    };

    Object.entries(presets).forEach(([btnId, pos]) => {
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.addEventListener('click', () => {
          this.animateCameraTo(new THREE.Vector3(...pos), new THREE.Vector3(0, 0, 0));
        });
      }
    });

    const btnFullscreen = document.getElementById('btnPresetFullscreen');
    if (btnFullscreen) {
      btnFullscreen.addEventListener('click', () => {
        if (!document.fullscreenElement) {
          this.container.requestFullscreen();
        } else {
          document.exitFullscreen();
        }
      });
    }
  }

  animateCameraTo(targetPos, targetLook) {
    this.isAnimatingCamera = true;
    this.targetCameraPos.copy(targetPos);
    this.targetLookAt.copy(targetLook);
    this.cameraAnimStart = performance.now();
    this.cameraStartPos = this.camera.position.clone();
  }

  animate() {
    requestAnimationFrame(this.animate);

    // Camera preset transition interpolation
    if (this.isAnimatingCamera) {
      const elapsed = performance.now() - this.cameraAnimStart;
      const progress = Math.min(elapsed / 600, 1.0);
      const ease = 0.5 - Math.cos(progress * Math.PI) / 2;

      this.camera.position.lerpVectors(this.cameraStartPos, this.targetCameraPos, ease);
      this.controls.target.lerp(this.targetLookAt, ease);

      if (progress >= 1.0) {
        this.isAnimatingCamera = false;
      }
    }

    this.controls.update();

    // Render Master 2D LCD Monitor Screen onto CanvasTexture
    if (window.monitorScreen2D) {
      window.monitorScreen2D.render();
    }

    // Update 3D screen Texture
    if (this.model) {
      this.model.updateScreenTexture();
    }

    this.renderer.render(this.scene, this.camera);
  }

  onWindowResize() {
    const width = this.container.clientWidth || 980;
    const height = this.container.clientHeight || 560;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.scene3DManager = new Scene3DManager();
});
