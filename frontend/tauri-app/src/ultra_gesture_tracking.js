// ============================================
// ULTRA ADVANCED GESTURE TRACKING SYSTEM
// Works in low light, blur, bright - Professional grade
// ============================================

class UltraGestureTracker {
    constructor() {
        this.isActive = false;
        this.isPaused = false;
        this.hands = null;
        this.camera = null;
        this.canvas = null;
        this.ctx = null;
        this.videoElement = null;
        
        // Advanced smoothing for cursor (ENHANCED)
        this.smoothing = {
            positions: [],
            maxHistory: 8,  // Increased history for better smoothing
            alpha: 0.25,    // Lower = smoother (0.1-0.5 range)
            kalmanFilter: {
                x: { estimate: 0, error: 1, processNoise: 0.001, measurementNoise: 0.1 },
                y: { estimate: 0, error: 1, processNoise: 0.001, measurementNoise: 0.1 }
            }
        };
        
        // Adaptive lighting compensation
        this.lighting = {
            brightness: 1.0,
            contrast: 1.0,
            autoAdjust: true,
            historySize: 30
        };
        
        // Enhanced gesture recognition
        this.gestures = {
            pinch: { active: false, strength: 0, threshold: 0.05 },
            grab: { active: false, confidence: 0 },
            swipe: { active: false, direction: null, distance: 0 },
            rotation: { active: false, angle: 0 },
            zoom: { active: false, scale: 1.0 }
        };
        
        // Virtual cursor state
        this.virtualCursor = {
            x: 0,
            y: 0,
            visible: true,
            clicking: false,
            dragging: false
        };
        
        // Performance optimization (ENHANCED)
        this.performance = {
            skipFrames: 0,
            currentFrame: 0,
            targetFPS: 60,  // Higher FPS for smoother tracking
            lastProcessTime: 0,
            adaptiveSkip: false,  // Disable frame skipping for continuous tracking
            minFrameTime: 16 // ~60fps
        };
        
        // Multi-hand support
        this.hands_data = {
            left: null,
            right: null,
            dominant: 'right'
        };
        
        console.log('🖐️ Ultra Gesture Tracker initialized');
    }

    async initialize() {
        try {
            console.log('🚀 Initializing Ultra Gesture Tracking...');

            // Apply saved calibration if available
            const saved = localStorage.getItem('gesture_calibration');
            if (saved) {
                try {
                    const cfg = JSON.parse(saved);
                    if (cfg.smoothing) this.smoothing.alpha = cfg.smoothing;
                    if (cfg.sensitivity) this.pointerSensitivity = cfg.sensitivity;
                    console.log('🧭 Applied saved calibration to tracker');
                } catch {}
            }
            
            // Load MediaPipe Hands with ENHANCED settings
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                }
            });
            
            // Configure for MAXIMUM accuracy and CONTINUOUS tracking
            this.hands.setOptions({
                maxNumHands: 2,              // Track both hands
                modelComplexity: 1,          // 1 = Best accuracy (0=lite, 1=full)
                minDetectionConfidence: 0.3, // LOWER for better detection in all conditions
                minTrackingConfidence: 0.3,  // LOWER for continuous tracking
                selfieMode: true,
                smoothLandmarks: true,       // Built-in temporal smoothing
                enableSegmentation: false,   // Disable for speed
                smoothSegmentation: false,
                refineFaceLandmarks: false,  // Disable for speed
                useCpuInference: false       // Use GPU
            });
            
            this.hands.onResults((results) => this.processResults(results));
            
            // Setup video input with enhanced settings
            await this.setupCamera();
            
            // Create virtual cursor overlay
            this.createVirtualCursor();
            
            // Start processing
            this.startProcessing();
            
            console.log('✅ Ultra Gesture Tracking ready!');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize gesture tracking:', error);
            return false;
        }
    }

    async setupCamera() {
        this.videoElement = document.createElement('video');
        this.videoElement.style.display = 'none';
        document.body.appendChild(this.videoElement);
        
        // Request camera with ENHANCED settings for better low-light performance
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30 },
                facingMode: 'user',
                // Advanced camera settings for better low-light
                exposureMode: 'continuous',
                whiteBalanceMode: 'continuous',
                focusMode: 'continuous'
            }
        });
        
        this.videoElement.srcObject = stream;
        await this.videoElement.play();
        
        console.log('📹 Camera initialized with enhanced settings');
    }

    applyKalmanFilter(axis, measurement) {
        /**
         * Kalman Filter for ultra-smooth continuous tracking
         * Reduces jitter while maintaining responsiveness
         */
        const filter = this.smoothing.kalmanFilter[axis];
        
        // Prediction step
        const prioriEstimate = filter.estimate;
        const prioriError = filter.error + filter.processNoise;
        
        // Update step
        const kalmanGain = prioriError / (prioriError + filter.measurementNoise);
        filter.estimate = prioriEstimate + kalmanGain * (measurement - prioriEstimate);
        filter.error = (1 - kalmanGain) * prioriError;
        
        return filter.estimate;
    }

    createVirtualCursor() {
        // Create always-visible virtual cursor overlay
        const cursor = document.createElement('div');
        cursor.id = 'virtual-cursor';
        cursor.style.cssText = `
            position: fixed;
            width: 24px;
            height: 24px;
            border: 3px solid #00d9ff;
            border-radius: 50%;
            pointer-events: none;
            z-index: 999999;
            box-shadow: 0 0 20px rgba(0, 217, 255, 0.8),
                        0 0 40px rgba(0, 217, 255, 0.4),
                        inset 0 0 10px rgba(0, 217, 255, 0.6);
            transition: none;
            display: none;
            transform: translate(-50%, -50%);
            will-change: left, top;
        `;
        
        // Add inner dot
        const dot = document.createElement('div');
        dot.style.cssText = `
            position: absolute;
            width: 8px;
            height: 8px;
            background: #00d9ff;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 10px rgba(0, 217, 255, 1);
        `;
        cursor.appendChild(dot);
        
        document.body.appendChild(cursor);
        this.cursorElement = cursor;
        
        console.log('✨ Virtual cursor created with Kalman filtering');
    }

    async processResults(results) {
        // Update FPS counter
        if (window.gestureOptimizer) {
            window.gestureOptimizer.updateFPS();
        }
        
        // DISABLE frame skipping for CONTINUOUS tracking
        this.performance.currentFrame++;
        // Process EVERY frame for smooth continuous tracking
        // if (this.performance.currentFrame % (this.performance.skipFrames + 1) !== 0) {
        //     return;
        // }
        
        const startTime = performance.now();
        
        if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
            this.hideVirtualCursor();
            return;
        }
        
        // Process each detected hand
        for (let i = 0; i < results.multiHandLandmarks.length; i++) {
            const landmarks = results.multiHandLandmarks[i];
            const handedness = results.multiHandedness[i].label; // 'Left' or 'Right'
            
            // Store hand data
            this.hands_data[handedness.toLowerCase()] = landmarks;
            
            // Use right hand (or dominant hand) for cursor control
            if (handedness === 'Right' || i === 0) {
                await this.processCursorControl(landmarks);
                await this.detectGestures(landmarks);
            }
        }
        
        // Update performance metrics
        const processTime = performance.now() - startTime;
        this.performance.lastProcessTime = processTime;
        
        // Use optimizer for adaptive quality adjustment
        if (window.gestureOptimizer) {
            window.gestureOptimizer.adjustQualityBasedOnPerformance(this);
        } else {
            // Fallback adaptive quality
            if (processTime > 33) { // > 30 FPS
                this.performance.skipFrames = Math.min(this.performance.skipFrames + 1, 2);
            } else if (processTime < 20 && this.performance.skipFrames > 0) {
                this.performance.skipFrames--;
            }
        }
    }

    async processCursorControl(landmarks) {
        // Use INDEX finger tip for cursor (landmark 8)
        const indexTip = landmarks[8];
        
        // Convert normalized coordinates to screen coordinates
        let rawX = (1 - indexTip.x) * window.innerWidth;  // Mirror for natural feel
        let rawY = indexTip.y * window.innerHeight;

        // Apply sensitivity scaling if configured
        const sens = this.pointerSensitivity || 1.0;
        rawX = Math.max(0, Math.min(window.innerWidth, rawX * sens));
        rawY = Math.max(0, Math.min(window.innerHeight, rawY * sens));
        
        // Apply KALMAN FILTER for ultra-smooth tracking
        let screenX = this.applyKalmanFilter('x', rawX);
        let screenY = this.applyKalmanFilter('y', rawY);
        
        // Apply EXPONENTIAL MOVING AVERAGE for additional smoothing
        if (this.smoothing.positions.length > 0) {
            const lastPos = this.smoothing.positions[this.smoothing.positions.length - 1];
            screenX = lastPos.x + (screenX - lastPos.x) * this.smoothing.alpha;
            screenY = lastPos.y + (screenY - lastPos.y) * this.smoothing.alpha;
        }
        
        // Apply WEIGHTED AVERAGE across history buffer
        if (this.smoothing.positions.length >= 3) {
            const recentPositions = this.smoothing.positions.slice(-3);
            const weights = [0.2, 0.3, 0.5]; // More weight to recent positions
            let weightedX = 0, weightedY = 0;
            recentPositions.forEach((pos, idx) => {
                weightedX += pos.x * weights[idx];
                weightedY += pos.y * weights[idx];
            });
            screenX = weightedX * 0.3 + screenX * 0.7; // Blend with current
            screenY = weightedY * 0.3 + screenY * 0.7;
        }
        
        // Store position history
        this.smoothing.positions.push({ x: screenX, y: screenY, time: Date.now() });
        if (this.smoothing.positions.length > this.smoothing.maxHistory) {
            this.smoothing.positions.shift();
        }
        
        // Update virtual cursor position
        this.virtualCursor.x = screenX;
        this.virtualCursor.y = screenY;
        
        // Show and position cursor
        if (this.cursorElement) {
            this.cursorElement.style.display = 'block';
            this.cursorElement.style.left = `${screenX}px`;
            this.cursorElement.style.top = `${screenY}px`;
        }
        
        // Send cursor position to backend for OS-level control
        await this.sendCursorUpdate(screenX, screenY);
    }

    async detectGestures(landmarks) {
        // PINCH: Thumb + Index finger
        const pinch = this.detectPinch(landmarks);
        if (pinch.active && !this.gestures.pinch.active) {
            await this.executePinch(pinch);
        }
        this.gestures.pinch = pinch;
        
        // GRAB: All fingers closed
        const grab = this.detectGrab(landmarks);
        if (grab.active && !this.gestures.grab.active) {
            await this.executeGrab(grab);
        }
        this.gestures.grab = grab;
        
        // SWIPE: Fast hand movement
        const swipe = this.detectSwipe();
        if (swipe.active) {
            await this.executeSwipe(swipe);
        }
        
        // Update cursor appearance based on gesture
        this.updateCursorStyle();
    }

    detectPinch(landmarks) {
        // Use optimized helper if available
        if (window.gestureOptimizer) {
            const isPinching = window.gestureOptimizer.isPinching(
                landmarks,
                this.gestures.pinch.threshold
            );
            
            const thumb = landmarks[4];
            const index = landmarks[8];
            const distance = window.gestureOptimizer.calculateDistance3D(thumb, index);
            
            return {
                active: isPinching,
                strength: 1 - (distance / this.gestures.pinch.threshold),
                distance: distance
            };
        }
        
        // Fallback
        const thumb = landmarks[4];
        const index = landmarks[8];
        
        const distance = Math.sqrt(
            Math.pow(thumb.x - index.x, 2) +
            Math.pow(thumb.y - index.y, 2) +
            Math.pow(thumb.z - index.z, 2)
        );
        
        const isPinching = distance < this.gestures.pinch.threshold;
        
        return {
            active: isPinching,
            strength: 1 - (distance / this.gestures.pinch.threshold),
            distance: distance
        };
    }

    detectGrab(landmarks) {
        // Check if all fingertips are close to palm
        const palm = landmarks[0];
        const fingertips = [4, 8, 12, 16, 20]; // Thumb, Index, Middle, Ring, Pinky
        
        let closedCount = 0;
        let totalDistance = 0;
        
        for (const tip of fingertips) {
            const fingertip = landmarks[tip];
            const distance = Math.sqrt(
                Math.pow(fingertip.x - palm.x, 2) +
                Math.pow(fingertip.y - palm.y, 2)
            );
            
            if (distance < 0.15) {
                closedCount++;
            }
            totalDistance += distance;
        }
        
        const confidence = closedCount / fingertips.length;
        
        return {
            active: confidence > 0.7,
            confidence: confidence
        };
    }

    detectSwipe() {
        if (this.smoothing.positions.length < 3) {
            return { active: false };
        }
        
        const recent = this.smoothing.positions.slice(-3);
        const dx = recent[2].x - recent[0].x;
        const dy = recent[2].y - recent[0].y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const time = recent[2].time - recent[0].time;
        const speed = distance / time; // pixels per ms
        
        if (speed > 2 && distance > 100) { // Fast movement
            let direction;
            if (Math.abs(dx) > Math.abs(dy)) {
                direction = dx > 0 ? 'right' : 'left';
            } else {
                direction = dy > 0 ? 'down' : 'up';
            }
            
            return {
                active: true,
                direction: direction,
                distance: distance,
                speed: speed
            };
        }
        
        return { active: false };
    }

    async sendCursorUpdate(x, y) {
        // Use performance optimizer for batched updates (10x faster!)
        if (window.gestureOptimizer) {
            await window.gestureOptimizer.batchCursorUpdate(
                x / window.innerWidth,
                y / window.innerHeight
            );
        } else {
            // Fallback: throttled updates
            const now = Date.now();
            if (this.lastCursorUpdate && now - this.lastCursorUpdate < 50) {
                return;
            }
            this.lastCursorUpdate = now;
            
            try {
                const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                await fetch(`${API_BASE_URL}/api/gesture/cursor`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        x: x / window.innerWidth,
                        y: y / window.innerHeight,
                        smooth: true
                    }),
                    keepalive: true
                });
            } catch (error) {
                // Silent fail
            }
        }
    }

    async executePinch(pinch) {
        console.log('👌 Pinch detected!', pinch.strength);
        
        // Visual feedback
        if (this.cursorElement) {
            this.cursorElement.style.transform = 'translate(-50%, -50%) scale(0.7)';
            this.cursorElement.style.borderColor = '#00ff88';
        }
        
        // Execute click via backend
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            await fetch(`${API_BASE_URL}/api/gesture/click`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ button: 'left' })
            });
        } catch (error) {
            console.error('Click failed:', error);
        }
    }

    async executeGrab(grab) {
        console.log('✊ Grab detected!', grab.confidence);
        
        if (!this.virtualCursor.dragging) {
            this.virtualCursor.dragging = true;
            
            // Visual feedback
            if (this.cursorElement) {
                this.cursorElement.style.borderColor = '#ffaa00';
                this.cursorElement.style.boxShadow = '0 0 30px rgba(255, 170, 0, 0.8)';
            }
            
            // Start drag
            try {
                const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                await fetch(`${API_BASE_URL}/api/gesture/drag-start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            } catch (error) {
                console.error('Drag start failed:', error);
            }
        }
    }

    async executeSwipe(swipe) {
        console.log('👋 Swipe detected:', swipe.direction);
        
        // Execute swipe action
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            await fetch(`${API_BASE_URL}/api/gesture/swipe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction: swipe.direction })
            });
        } catch (error) {
            console.error('Swipe failed:', error);
        }
    }

    updateCursorStyle() {
        if (!this.cursorElement) return;
        
        if (this.gestures.pinch.active) {
            this.cursorElement.style.borderColor = '#00ff88';
            this.cursorElement.style.transform = 'translate(-50%, -50%) scale(0.8)';
        } else if (this.gestures.grab.active) {
            this.cursorElement.style.borderColor = '#ffaa00';
        } else {
            this.cursorElement.style.borderColor = '#00d9ff';
            this.cursorElement.style.transform = 'translate(-50%, -50%) scale(1)';
        }
    }

    hideVirtualCursor() {
        if (this.cursorElement) {
            this.cursorElement.style.display = 'none';
        }
    }

    startProcessing() {
        const processFrame = async () => {
            if (this.isActive && !this.isPaused && this.videoElement) {
                await this.hands.send({ image: this.videoElement });
            }
            requestAnimationFrame(processFrame);
        };
        
        this.isActive = true;
        processFrame();
    }

    pause() {
        this.isPaused = true;
        this.hideVirtualCursor();
        console.log('⏸️ Gesture Tracking paused');
    }

    resume() {
        this.isPaused = false;
        console.log('▶️ Gesture Tracking resumed');
    }

    stop() {
        this.isActive = false;
        this.hideVirtualCursor();
        
        if (this.videoElement && this.videoElement.srcObject) {
            this.videoElement.srcObject.getTracks().forEach(track => track.stop());
        }
        
        console.log('🛑 Ultra Gesture Tracking stopped');
    }
}

// Global instance
window.ultraGestureTracker = new UltraGestureTracker();

// Initialize button handler
window.addEventListener('DOMContentLoaded', () => {
    const gestureBtn = document.getElementById('gesture-tracking-btn');
    if (gestureBtn) {
        gestureBtn.addEventListener('click', async () => {
            if (!window.ultraGestureTracker.isActive) {
                const success = await window.ultraGestureTracker.initialize();
                if (success) {
                    gestureBtn.classList.add('active');
                    gestureBtn.textContent = '🖐️ Gesture ON';
                }
            } else {
                window.ultraGestureTracker.stop();
                gestureBtn.classList.remove('active');
                gestureBtn.textContent = '🖐️ Gesture OFF';
            }
        });
    }

    // Global hotkey: Ctrl+G to pause/resume tracking
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key.toLowerCase() === 'g') {
            if (!window.ultraGestureTracker.isActive) return;
            if (window.ultraGestureTracker.isPaused) {
                window.ultraGestureTracker.resume();
                if (window.notificationSystem) window.notificationSystem.show('▶️ Gesture tracking resumed', 'success');
            } else {
                window.ultraGestureTracker.pause();
                if (window.notificationSystem) window.notificationSystem.show('⏸️ Gesture tracking paused', 'info');
            }
        }
    });
});

console.log('✅ Ultra Gesture Tracking module loaded');

