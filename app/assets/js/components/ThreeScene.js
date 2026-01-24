
class ThreeScene {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        
        this.init();
    }

    init() {
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        // Basic Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambientLight);

        // Camera Position
        this.camera.position.z = 5;

        // Resize Listener
        window.addEventListener('resize', this.onWindowResize.bind(this), false);

        // Start Loop
        this.createRain();
        this.animate();
    }

    createRain() {
        const geometry = new THREE.BufferGeometry();
        const count = 1500;
        const positions = new Float32Array(count * 3);

        for(let i = 0; i < count * 3; i++) {
            positions[i] = (Math.random() - 0.5) * 50; // Spread x, y, z
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.PointsMaterial({
            color: 0xaaaaaa,
            size: 0.1,
            transparent: true,
            opacity: 0.8
        });

        this.rainSystem = new THREE.Points(geometry, material);
        this.scene.add(this.rainSystem);
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(this.animate.bind(this));
        
        // Rain Animation - Fall down
        if (this.rainSystem) {
            const positions = this.rainSystem.geometry.attributes.position.array;
            for(let i = 1; i < positions.length; i += 3) {
                positions[i] -= 0.1; // Move Y down
                if (positions[i] < -10) {
                    positions[i] = 10; // Reset to top
                }
            }
            this.rainSystem.geometry.attributes.position.needsUpdate = true;
        }
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.weatherScene = new ThreeScene('canvas-container');
});
