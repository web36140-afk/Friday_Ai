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
        
        // Snap overlay
        this.snapOverlayActive = false;
        this.snapGrid = { cols: 3, rows: 3 };
        
        // Advanced smoothing for cursor (ENHANCED)
        this.smoothing = {
            positions: [],
            maxHistory: 8,  // Increased history for better smoothing
            alpha: 0.25,    // Lower = smoother (0.1-0.5 range) - dynamically adjusted
            kalmanFilter: {
                x: { estimate: 0, error: 1, processNoise: 0.001, measurementNoise: 0.1 },
                y: { estimate: 0, error: 1, processNoise: 0.001, measurementNoise: 0.1 }
            }
        };
        
        // Per-finger smoothing (for all 5 fingertips)
        this.fingerSmoothing = {
            indices: [4, 8, 12, 16, 20],
            history: new Map(), // fingerIndex -> [{x,y,time}, ...]
            maxHistory: 6,
            alpha: 0.35
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
        
        // Confidence tracking
        this.confidence = {
            value: 1.0,
            lowFrames: 0
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

            // Fetch multi-monitor virtual bounds
            try {
                const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const resp = await fetch(`${API_BASE_URL}/api/display/monitors`);
                const data = await resp.json();
                if (data?.success) {
                    this.virtual = data.virtual; // {left, top, width, height}
                    this.monitors = data.monitors || [];
                    console.log('🖥️ Virtual desktop:', this.virtual, 'Monitors:', this.monitors.length);
                }
            } catch (e) {
                console.warn('Display info unavailable, using window size');
                this.virtual = { left: 0, top: 0, width: window.innerWidth, height: window.innerHeight };
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
                frameRate: { ideal: 60, max: 60 },
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
    
    smoothPointEMA(last, current, alpha) {
        if (!last) return current;
        return {
            x: last.x + (current.x - last.x) * alpha,
            y: last.y + (current.y - last.y) * alpha
        };
    }
    
    smoothFingerTip(index, point) {
        const key = String(index);
        const hist = this.fingerSmoothing.history.get(key) || [];
        const alpha = this.fingerSmoothing.alpha;
        const last = hist.length ? hist[hist.length - 1] : null;
        // Outlier rejection: if jump > threshold, clamp toward last
        let candidate = point;
        if (last) {
            const dx = point.x - last.x;
            const dy = point.y - last.y;
            const dist = Math.hypot(dx, dy);
            const maxJump = 120; // pixels per frame
            if (dist > maxJump) {
                const scale = maxJump / dist;
                candidate = { x: last.x + dx * scale, y: last.y + dy * scale };
            }
        }
        const smoothed = this.smoothPointEMA(last, candidate, alpha);
        hist.push({ x: smoothed.x, y: smoothed.y, time: Date.now() });
        if (hist.length > this.fingerSmoothing.maxHistory) hist.shift();
        this.fingerSmoothing.history.set(key, hist);
        return smoothed;
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
        
        // Create a canvas overlay for fingertip visualization & HUD
        const canvas = document.createElement('canvas');
        canvas.id = 'gesture-hud';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.cssText = `
            position: fixed;
            left: 0; top: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 999998;
        `;
        document.body.appendChild(canvas);
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
        
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
            
            // Smooth all five fingertips for stability (indices: 4,8,12,16,20)
            const vw = (this.virtual?.width || window.innerWidth);
            const vh = (this.virtual?.height || window.innerHeight);
            const fingertipIndices = this.fingerSmoothing.indices;
            this.fingers = this.fingers || { left: {}, right: {} };
            for (const fi of fingertipIndices) {
                const tip = landmarks[fi];
                const pt = { x: (1 - tip.x) * vw, y: tip.y * vh };
                const smoothed = this.smoothFingerTip(fi, pt);
                this.fingers[handedness.toLowerCase()][fi] = smoothed;
            }
            
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
        
        // Render fingertip overlay and HUD
        this.renderHUD();
        
        // Confidence and auto-recalibration
        this.updateConfidence();
        this.autoRecalibrateIfNeeded();
    }

    async processCursorControl(landmarks) {
        // Use INDEX finger tip for cursor (landmark 8)
        const indexTip = landmarks[8];
        
        // Convert normalized coordinates to screen coordinates
        const vw = (this.virtual?.width || window.innerWidth);
        const vh = (this.virtual?.height || window.innerHeight);
        let rawX = (1 - indexTip.x) * vw;  // Mirror for natural feel across virtual space
        let rawY = indexTip.y * vh;

        // Apply sensitivity scaling if configured
        const sens = this.pointerSensitivity || 1.0;
        rawX = Math.max(0, Math.min(vw, rawX * sens));
        rawY = Math.max(0, Math.min(vh, rawY * sens));
        
        // Apply KALMAN FILTER for ultra-smooth tracking with dynamic responsiveness
        const prev = this.smoothing.positions.length ? this.smoothing.positions[this.smoothing.positions.length - 1] : null;
        const speed = prev ? Math.hypot(rawX - prev.x, rawY - prev.y) : 0;
        const kfX = this.smoothing.kalmanFilter.x;
        const kfY = this.smoothing.kalmanFilter.y;
        const baseNoise = 0.08;
        const extra = Math.min(0.25, speed / 800); // increase noise when moving fast to stay responsive
        kfX.measurementNoise = baseNoise + extra;
        kfY.measurementNoise = baseNoise + extra;
        let screenX = this.applyKalmanFilter('x', rawX);
        let screenY = this.applyKalmanFilter('y', rawY);
        
        // Apply EXPONENTIAL MOVING AVERAGE for additional smoothing
        if (this.smoothing.positions.length > 0) {
            const lastPos = this.smoothing.positions[this.smoothing.positions.length - 1];
            const dynAlpha = Math.min(0.5, 0.15 + Math.min(0.35, speed / 1200)); // faster when moving fast
            screenX = lastPos.x + (screenX - lastPos.x) * dynAlpha;
            screenY = lastPos.y + (screenY - lastPos.y) * dynAlpha;
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
            this.cursorElement.style.left = `${(screenX / vw) * window.innerWidth}px`;
            this.cursorElement.style.top = `${(screenY / vh) * window.innerHeight}px`;
        }
        
        // Send cursor position to backend for OS-level control
        this.sendCursorUpdate(screenX, screenY); // fire-and-forget to keep loop hot
    }

    renderHUD() {
        if (!this.ctx || !this.canvas) return;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        ctx.clearRect(0, 0, w, h);
        
        // Draw fingertip positions with small trails
        if (this.fingers) {
            const hands = ['left', 'right'];
            for (const hand of hands) {
                const tips = this.fingers[hand] || {};
                Object.keys(tips).forEach((idxStr) => {
                    const tip = tips[idxStr];
                    if (!tip) return;
                    const color = hand === 'right' ? '#00d9ff' : '#ff4d4d';
                    ctx.fillStyle = color;
                    ctx.strokeStyle = color;
                    // Tip dot
                    ctx.beginPath();
                    const vw = (this.virtual?.width || window.innerWidth);
                    const vh = (this.virtual?.height || window.innerHeight);
                    const px = (tip.x / vw) * w;
                    const py = (tip.y / vh) * h;
                    ctx.arc(px, py, 4, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // Trail from history buffer (fade)
                    const hist = this.fingerSmoothing.history.get(idxStr) || [];
                    for (let i = Math.max(0, hist.length - 5); i < hist.length - 1; i++) {
                        const a = hist[i], b = hist[i + 1];
                        const ax = (a.x / vw) * w, ay = (a.y / vh) * h;
                        const bx = (b.x / vw) * w, by = (b.y / vh) * h;
                        ctx.globalAlpha = 0.2 + (i - (hist.length - 6)) * 0.15;
                        ctx.beginPath();
                        ctx.moveTo(ax, ay);
                        ctx.lineTo(bx, by);
                        ctx.stroke();
                        ctx.globalAlpha = 1.0;
                    }
                });
            }
        }
        
        // HUD text: FPS and latency
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto';
        const fps = window.gestureOptimizer?.getFPS?.() || '';
        const latency = Math.round(this.performance.lastProcessTime);
        const confPct = Math.round((this.confidence?.value || 0) * 100);
        ctx.fillText(`FPS: ${fps || '--'} | Latency: ${latency}ms | Confidence: ${confPct}%`, 12, 20);
        
        // Snap grid overlay
        if (this.snapOverlayActive) {
            const cols = this.snapGrid.cols, rows = this.snapGrid.rows;
            ctx.strokeStyle = 'rgba(0,217,255,0.6)';
            for (let c = 1; c < cols; c++) {
                const x = Math.round((c / cols) * w);
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
            }
            for (let r = 1; r < rows; r++) {
                const y = Math.round((r / rows) * h);
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
            }
            // Highlight current cell under cursor
            const vw = (this.virtual?.width || window.innerWidth);
            const vh = (this.virtual?.height || window.innerHeight);
            const cx = (this.virtualCursor.x / vw) * w;
            const cy = (this.virtualCursor.y / vh) * h;
            const col = Math.min(cols - 1, Math.max(0, Math.floor((cx / w) * cols)));
            const row = Math.min(rows - 1, Math.max(0, Math.floor((cy / h) * rows)));
            const cellW = w / cols, cellH = h / rows;
            ctx.fillStyle = 'rgba(0,217,255,0.12)';
            ctx.fillRect(col * cellW, row * cellH, cellW, cellH);
            ctx.fillStyle = 'rgba(255,255,255,0.85)';
            ctx.fillText(`Snap: ${cols}x${rows} (${col+1},${row+1})`, 12, 38);
        }
    }
    
    updateConfidence() {
        // Simple confidence estimation based on fingertip continuity and motion stability
        const fingertipIndices = this.fingerSmoothing.indices;
        let continuity = 0;
        let samples = 0;
        let jitterScore = 0;
        fingertipIndices.forEach((fi) => {
            const hist = this.fingerSmoothing.history.get(String(fi)) || [];
            if (hist.length >= 3) {
                continuity += 1;
                // Jitter over last 3 deltas
                const a = hist[hist.length - 3], b = hist[hist.length - 2], c = hist[hist.length - 1];
                const j1 = Math.hypot(b.x - a.x, b.y - a.y);
                const j2 = Math.hypot(c.x - b.x, c.y - b.y);
                jitterScore += (j1 + j2) / 2;
                samples += 1;
            }
        });
        const contRatio = continuity / fingertipIndices.length; // 0..1
        const avgJitter = samples ? (jitterScore / samples) : 0; // pixels
        // Map jitter to penalty (0 at 0px, 1 at >= 80px)
        const jitterPenalty = Math.max(0, Math.min(1, avgJitter / 80));
        // Incorporate processing delay
        const latencyPenalty = Math.max(0, Math.min(1, (this.performance.lastProcessTime - 16) / 34)); // 16ms good, >50ms bad
        const conf = Math.max(0, Math.min(1, contRatio * (1 - 0.5 * jitterPenalty) * (1 - 0.3 * latencyPenalty)));
        this.confidence.value = conf;
        if (conf < 0.55) this.confidence.lowFrames++; else this.confidence.lowFrames = 0;
    }
    
    autoRecalibrateIfNeeded() {
        // If confidence is low for ~1.5s, auto-apply balanced preset and lower detection thresholds
        if (this.confidence.lowFrames > 90) {
            this.confidence.lowFrames = 0;
            if (window.gestureCalibration) {
                window.gestureCalibration.applyPreset?.('balanced');
                window.gestureCalibration.applyLightingOptimization?.('low');
                if (window.notificationSystem) {
                    window.notificationSystem.show('🔧 Auto-optimized gesture tracking for stability', 'info', 2000);
                }
            } else if (this.hands) {
                // Fallback: relax thresholds
                this.hands.setOptions({
                    minDetectionConfidence: 0.3,
                    minTrackingConfidence: 0.3
                });
            }
        }
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
            const absDx = Math.abs(dx);
            const absDy = Math.abs(dy);
            const diagonal = Math.abs(absDx - absDy) < Math.min(absDx, absDy) * 0.3; // ~ within 30%
            if (diagonal) {
                if (dx < 0 && dy < 0) direction = 'up-left';
                else if (dx > 0 && dy < 0) direction = 'up-right';
                else if (dx < 0 && dy > 0) direction = 'down-left';
                else direction = 'down-right';
            } else if (absDx > absDy) {
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
            const vw = (this.virtual?.width || window.innerWidth);
            const vh = (this.virtual?.height || window.innerHeight);
            window.gestureOptimizer.batchCursorUpdate(
                x / vw,
                y / vh
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
                const vw = (this.virtual?.width || window.innerWidth);
                const vh = (this.virtual?.height || window.innerHeight);
                fetch(`${API_BASE_URL}/api/gesture/cursor`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        x: x / vw,
                        y: y / vh,
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
        
        // If snap overlay active, snap to highlighted cell and exit
        if (this.snapOverlayActive) {
            try {
                const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const vw = (this.virtual?.width || window.innerWidth);
                const vh = (this.virtual?.height || window.innerHeight);
                const w = this.canvas?.width || window.innerWidth;
                const h = this.canvas?.height || window.innerHeight;
                const cols = this.snapGrid.cols, rows = this.snapGrid.rows;
                const cx = (this.virtualCursor.x / vw) * w;
                const cy = (this.virtualCursor.y / vh) * h;
                const col = Math.min(cols - 1, Math.max(0, Math.floor((cx / w) * cols)));
                const row = Math.min(rows - 1, Math.max(0, Math.floor((cy / h) * rows)));
                await fetch(`${API_BASE_URL}/api/windows/snap_grid?cols=${cols}&rows=${rows}&col=${col}&row=${row}`, { method: 'POST' });
            } catch {}
            this.snapOverlayActive = false;
            return;
        }
        
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
            // Map swipe to window snap for productivity
            const dir = swipe.direction;
            if (['left', 'right', 'up', 'down'].includes(dir)) {
                await fetch(`${API_BASE_URL}/api/windows/snap`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ direction: dir })
                });
            } else if (['up-left', 'up-right', 'down-left', 'down-right'].includes(dir)) {
                const mapCorner = { 'up-left': 'tl', 'up-right': 'tr', 'down-left': 'bl', 'down-right': 'br' };
                await fetch(`${API_BASE_URL}/api/windows/snap_corner`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ corner: mapCorner[dir] })
                });
            } else {
                // Fallback: send as gesture swipe to backend
                await fetch(`${API_BASE_URL}/api/gesture/swipe`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ direction: swipe.direction })
                });
            }

            // App-specific bindings (simple defaults)
            await this.applyAppBindings(dir);
        } catch (error) {
            console.error('Swipe failed:', error);
        }
    }

    async applyAppBindings(direction) {
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const resp = await fetch(`${API_BASE_URL}/api/windows/active_window`);
            const data = await resp.json();
            if (!data?.success) return;
            const exe = (data.exe || '').toLowerCase();

            // Custom bindings from localStorage override defaults
            const custom = this.loadAppBindings();
            const appCfg = custom[exe];
            if (appCfg && appCfg[direction]) {
                await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: appCfg[direction] }) });
                return;
            }

            // VSCode: left/right = switch tabs, up = command palette, down = close tab
            if (exe.includes('code.exe')) {
                if (direction === 'left') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+pageup' }) });
                if (direction === 'right') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+pagedown' }) });
                if (direction === 'up') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+shift+p' }) });
                if (direction === 'down') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+w' }) });
            }

            // Chrome/Edge: left/right = switch tabs, up = new tab, down = close tab
            if (exe.includes('chrome') || exe.includes('msedge')) {
                if (direction === 'left') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+shift+tab' }) });
                if (direction === 'right') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+tab' }) });
                if (direction === 'up') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+t' }) });
                if (direction === 'down') await fetch(`${API_BASE_URL}/api/keyboard/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ combo: 'ctrl+w' }) });
            }
        } catch {}
    }
    
    loadAppBindings() {
        try {
            return JSON.parse(localStorage.getItem('app_gesture_bindings') || '{}');
        } catch { return {}; }
    }
    
    saveAppBindings(cfg) {
        localStorage.setItem('app_gesture_bindings', JSON.stringify(cfg));
    }
    
    async configureAppBindingPrompt() {
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const resp = await fetch(`${API_BASE_URL}/api/windows/active_window`);
            const data = await resp.json();
            if (!data?.success) return;
            const exe = (data.exe || '').toLowerCase();
            const dir = prompt(`Bind gesture for ${exe}\nEnter direction (left/right/up/down/up-left/up-right/down-left/down-right):`);
            if (!dir) return;
            const combo = prompt(`Enter hotkey combo (e.g., ctrl+alt+t):`);
            if (!combo) return;
            const cfg = this.loadAppBindings();
            cfg[exe] = cfg[exe] || {};
            cfg[exe][dir] = combo;
            this.saveAppBindings(cfg);
            if (window.notificationSystem) window.notificationSystem.show(`🔗 Bound ${dir} → ${combo} for ${exe}`, 'success');
        } catch {}
    }

    async updateAppProfile() {
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const resp = await fetch(`${API_BASE_URL}/api/windows/active_window`);
            const data = await resp.json();
            if (!data?.success) return;
            const exe = (data.exe || '').toLowerCase();
            // Simple profiles: adjust sensitivity per app
            if (exe.includes('code.exe')) {
                this.pointerSensitivity = 0.9; // precision for VSCode
            } else if (exe.includes('photoshop')) {
                this.pointerSensitivity = 0.8; // finer control
            } else if (exe.includes('chrome') || exe.includes('msedge')) {
                this.pointerSensitivity = 1.0;
            } else {
                // default from calibration if set
                const saved = localStorage.getItem('gesture_calibration');
                if (saved) {
                    try {
                        const cfg = JSON.parse(saved);
                        this.pointerSensitivity = cfg.sensitivity || 1.0;
                    } catch {}
                } else {
                    this.pointerSensitivity = 1.0;
                }
            }
        } catch {}
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
                if (typeof this.videoElement.requestVideoFrameCallback === 'function') {
                    this.videoElement.requestVideoFrameCallback(async () => {
                        await this.hands.send({ image: this.videoElement });
                        requestAnimationFrame(processFrame);
                    });
                    return;
                } else {
                    await this.hands.send({ image: this.videoElement });
                }
            }
            requestAnimationFrame(processFrame);
        };
        
        this.isActive = true;

        // Periodically update app profile (every 3s for responsiveness)
        if (!this._profileTimer) {
            this._profileTimer = setInterval(() => this.updateAppProfile(), 3000);
        }
        processFrame();
        
        // Bind overlay toggle hotkey (Ctrl+Alt+S) and bindings editor (Ctrl+Alt+B)
        if (!this._hotkeysBound) {
            this._hotkeysBound = true;
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 's') {
                    this.snapOverlayActive = !this.snapOverlayActive;
                    if (window.notificationSystem) window.notificationSystem.show(this.snapOverlayActive ? '🧩 Snap grid ON' : '🧩 Snap grid OFF', 'info');
                }
                if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'b') {
                    this.configureAppBindingPrompt();
                }
            });
        }
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
        if (this._profileTimer) {
            clearInterval(this._profileTimer);
            this._profileTimer = null;
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

