// ============================================
// GESTURE CALIBRATION & TRAINING UI
// Advanced calibration for different lighting/camera conditions
// ============================================

class GestureCalibrationUI {
    constructor() {
        this.isCalibrating = false;
        this.calibrationData = {
            lighting: 'normal',  // low, normal, bright
            cameraQuality: 'normal',  // low, normal, high
            smoothing: 0.3,
            speed: 2.0,
            sensitivity: 1.0
        };
        
        console.log('⚙️ Gesture Calibration UI loaded');
    }

    showCalibrationModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = 'calibration-modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h2>🖐️ Gesture Control Calibration</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="settings-section">
                        <h3>Environment Settings</h3>
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">Lighting Condition</span>
                            <select id="lighting-select" class="jarvis-select">
                                <option value="low">Low Light (Dark room)</option>
                                <option value="normal" selected>Normal Light</option>
                                <option value="bright">Bright Light (Window/Sun)</option>
                            </select>
                        </label>
                        
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">Camera Quality</span>
                            <select id="camera-quality-select" class="jarvis-select">
                                <option value="low">Low (Blur/Old camera)</option>
                                <option value="normal" selected>Normal</option>
                                <option value="high">High (HD camera)</option>
                            </select>
                        </label>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Cursor Behavior</h3>
                        
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">
                                Smoothing: <span id="smoothing-value">0.3</span>
                            </span>
                            <input type="range" id="smoothing-slider" min="0.1" max="0.9" step="0.1" value="0.3" style="width: 100%;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                <span>Jittery (Fast)</span>
                                <span>Smooth (Slow)</span>
                            </div>
                        </label>
                        
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">
                                Speed: <span id="speed-value">2.0</span>
                            </span>
                            <input type="range" id="speed-slider" min="0.5" max="5.0" step="0.5" value="2.0" style="width: 100%;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                <span>Slow</span>
                                <span>Very Fast</span>
                            </div>
                        </label>
                        
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">
                                Sensitivity: <span id="sensitivity-value">1.0</span>
                            </span>
                            <input type="range" id="sensitivity-slider" min="0.5" max="2.0" step="0.1" value="1.0" style="width: 100%;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                <span>Less Sensitive</span>
                                <span>More Sensitive</span>
                            </div>
                        </label>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Quick Presets</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;">
                            <button class="friday-btn-secondary" onclick="window.gestureCalibration.applyPreset('precise')" style="padding: 0.75rem;">
                                🎯 Precise
                            </button>
                            <button class="friday-btn-secondary" onclick="window.gestureCalibration.applyPreset('balanced')" style="padding: 0.75rem;">
                                ⚖️ Balanced
                            </button>
                            <button class="friday-btn-secondary" onclick="window.gestureCalibration.applyPreset('fast')" style="padding: 0.75rem;">
                                ⚡ Fast
                            </button>
                        </div>
                    </div>
                    
                    <div class="settings-section" style="background: rgba(0, 217, 255, 0.1); padding: 1rem; border-radius: 8px;">
                        <h4 style="margin-bottom: 0.5rem;">📊 Current Performance</h4>
                        <div style="font-size: 0.9rem; color: var(--jarvis-text-dim); line-height: 1.8;">
                            <div>FPS: <span id="gesture-fps">--</span></div>
                            <div>Latency: <span id="gesture-latency">--</span>ms</div>
                            <div>Hands Detected: <span id="hands-count">0</span></div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="friday-btn" onclick="window.gestureCalibration.saveCalibration()">
                        ✅ Save & Apply
                    </button>
                    <button class="friday-btn-secondary" onclick="window.gestureCalibration.testCalibration()">
                        🧪 Test Settings
                    </button>
                    <button class="friday-btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Setup event listeners
        this.setupCalibrationListeners();
    }

    setupCalibrationListeners() {
        // Smoothing slider
        const smoothingSlider = document.getElementById('smoothing-slider');
        const smoothingValue = document.getElementById('smoothing-value');
        if (smoothingSlider) {
            smoothingSlider.addEventListener('input', (e) => {
                smoothingValue.textContent = e.target.value;
                this.calibrationData.smoothing = parseFloat(e.target.value);
            });
        }
        
        // Speed slider
        const speedSlider = document.getElementById('speed-slider');
        const speedValue = document.getElementById('speed-value');
        if (speedSlider) {
            speedSlider.addEventListener('input', (e) => {
                speedValue.textContent = e.target.value;
                this.calibrationData.speed = parseFloat(e.target.value);
            });
        }
        
        // Sensitivity slider
        const sensitivitySlider = document.getElementById('sensitivity-slider');
        const sensitivityValue = document.getElementById('sensitivity-value');
        if (sensitivitySlider) {
            sensitivitySlider.addEventListener('input', (e) => {
                sensitivityValue.textContent = e.target.value;
                this.calibrationData.sensitivity = parseFloat(e.target.value);
            });
        }
        
        // Lighting select
        const lightingSelect = document.getElementById('lighting-select');
        if (lightingSelect) {
            lightingSelect.addEventListener('change', (e) => {
                this.calibrationData.lighting = e.target.value;
                this.applyLightingOptimization(e.target.value);
            });
        }
        
        // Camera quality select
        const cameraSelect = document.getElementById('camera-quality-select');
        if (cameraSelect) {
            cameraSelect.addEventListener('change', (e) => {
                this.calibrationData.cameraQuality = e.target.value;
                this.applyCameraOptimization(e.target.value);
            });
        }
    }

    applyPreset(presetName) {
        const presets = {
            precise: {
                smoothing: 0.2,
                speed: 1.0,
                sensitivity: 1.5,
                message: '🎯 Precise mode - Best for detailed work'
            },
            balanced: {
                smoothing: 0.3,
                speed: 2.0,
                sensitivity: 1.0,
                message: '⚖️ Balanced mode - Best for general use'
            },
            fast: {
                smoothing: 0.5,
                speed: 4.0,
                sensitivity: 0.8,
                message: '⚡ Fast mode - Best for quick actions'
            }
        };
        
        const preset = presets[presetName];
        if (!preset) return;
        
        // Update sliders
        document.getElementById('smoothing-slider').value = preset.smoothing;
        document.getElementById('smoothing-value').textContent = preset.smoothing;
        document.getElementById('speed-slider').value = preset.speed;
        document.getElementById('speed-value').textContent = preset.speed;
        document.getElementById('sensitivity-slider').value = preset.sensitivity;
        document.getElementById('sensitivity-value').textContent = preset.sensitivity;
        
        // Update calibration data
        this.calibrationData.smoothing = preset.smoothing;
        this.calibrationData.speed = preset.speed;
        this.calibrationData.sensitivity = preset.sensitivity;
        
        if (window.notificationSystem) {
            window.notificationSystem.show(preset.message, 'info');
        }
    }

    applyLightingOptimization(lighting) {
        console.log(`💡 Applying ${lighting} light optimization`);
        
        const optimizations = {
            low: {
                minDetectionConfidence: 0.4,
                minTrackingConfidence: 0.3,
                message: '🌙 Low light mode - Reduced thresholds for better detection'
            },
            normal: {
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.4,
                message: '☀️ Normal mode - Balanced detection'
            },
            bright: {
                minDetectionConfidence: 0.6,
                minTrackingConfidence: 0.5,
                message: '🔆 Bright mode - Higher thresholds to reduce false positives'
            }
        };
        
        const opt = optimizations[lighting];
        if (opt && window.ultraGestureTracker && window.ultraGestureTracker.hands) {
            // Update MediaPipe settings dynamically
            window.ultraGestureTracker.hands.setOptions({
                minDetectionConfidence: opt.minDetectionConfidence,
                minTrackingConfidence: opt.minTrackingConfidence
            });
            
            if (window.notificationSystem) {
                window.notificationSystem.show(opt.message, 'info');
            }
        }
    }

    applyCameraOptimization(quality) {
        console.log(`📹 Applying ${quality} camera optimization`);
        
        const optimizations = {
            low: {
                skipFrames: 2,
                message: '📹 Low quality mode - Processing every 3rd frame for stability'
            },
            normal: {
                skipFrames: 0,
                message: '📹 Normal mode - Processing all frames'
            },
            high: {
                skipFrames: 0,
                message: '📹 High quality mode - Maximum frame rate'
            }
        };
        
        const opt = optimizations[quality];
        if (opt && window.ultraGestureTracker) {
            window.ultraGestureTracker.performance.skipFrames = opt.skipFrames;
            
            if (window.notificationSystem) {
                window.notificationSystem.show(opt.message, 'info');
            }
        }
    }

    async saveCalibration() {
        try {
            console.log('💾 Saving calibration:', this.calibrationData);
            
            // Save to localStorage
            localStorage.setItem('gesture_calibration', JSON.stringify(this.calibrationData));
            
            // Send to backend
            const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
            const response = await fetch(`${API_BASE_URL}/api/gesture/calibrate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    smoothing: this.calibrationData.smoothing,
                    speed: this.calibrationData.speed
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (window.notificationSystem) {
                    window.notificationSystem.show(
                        '✅ Calibration saved! Settings applied.',
                        'success'
                    );
                }
                
                // Close modal
                document.getElementById('calibration-modal')?.remove();
            }
            
        } catch (error) {
            console.error('Failed to save calibration:', error);
            if (window.notificationSystem) {
                window.notificationSystem.show(
                    '❌ Failed to save calibration',
                    'error'
                );
            }
        }
    }

    testCalibration() {
        if (window.notificationSystem) {
            window.notificationSystem.show(
                '🧪 Testing gesture controls... Move your hand to see the cursor!',
                'info',
                3000
            );
        }
        
        // If gesture tracking not active, start it
        if (!window.ultraGestureTracker?.isActive) {
            const btn = document.getElementById('gesture-tracking-btn');
            if (btn) btn.click();
        }
    }

    loadSavedCalibration() {
        const saved = localStorage.getItem('gesture_calibration');
        if (saved) {
            try {
                this.calibrationData = JSON.parse(saved);
                console.log('✅ Loaded saved calibration:', this.calibrationData);
                return this.calibrationData;
            } catch (error) {
                console.error('Failed to load calibration:', error);
            }
        }
        return null;
    }
}

// Global instance
window.gestureCalibration = new GestureCalibrationUI();

// Auto-load saved calibration on startup
window.addEventListener('DOMContentLoaded', () => {
    window.gestureCalibration.loadSavedCalibration();
});

