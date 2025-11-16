// ============================================
// FRIDAY ADVANCED HAND TRACKING MODULE
// ============================================
// Full device control with hand gestures

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class AdvancedHandTrackingController {
    constructor() {
        this.hands = null;
        this.camera = null;
        this.isActive = false;
        this.lastGesture = null;
        this.gestureDebounce = null;
        this.gestureHoldTime = 600;  // Reduced for faster response
        this.gestureConfidenceThreshold = 0.75;
        
        // Cursor control - ENHANCED
        this.cursorControlEnabled = false;
        this.smoothingFactor = 0.3;  // More responsive
        this.lastCursorX = 0;
        this.lastCursorY = 0;
        this.cursorHistory = [];  // For better smoothing
        this.maxCursorHistory = 5;
        
        // Pinch state for dragging - ENHANCED
        this.isPinching = false;
        this.pinchStartTime = null;
        this.draggedElement = null;
        this.pinchConfidence = 0;
        
        // Volume control - ENHANCED
        this.volumeControlActive = false;
        this.lastVolume = 50;
        this.volumeSmoothingBuffer = [];
        
        // Previous landmarks for gesture detection
        this.previousLandmarks = null;
        this.gestureConfidenceHistory = {};
        
        // App shortcuts
        this.appShortcuts = {
            'spotify': 'spotify.exe',
            'chrome': 'chrome.exe',
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'explorer': 'explorer.exe'
        };
        
        // Gesture statistics
        this.stats = {
            totalGestures: 0,
            successfulActions: 0,
            failedActions: 0
        };
        
        console.log('🖐️ Enhanced Hand Tracking initialized with improved accuracy');
    }

    async initialize() {
        try {
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                }
            });

            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,  // Balance between speed and accuracy
                minDetectionConfidence: 0.8,  // Higher for better accuracy
                minTrackingConfidence: 0.7,  // Smoother tracking
                selfieMode: true  // Mirror for natural interaction
            });

            this.hands.onResults((results) => this.onHandResults(results));

            console.log('✅ Advanced Hand Tracking initialized');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize:', error);
            return false;
        }
    }

    async start() {
        if (this.isActive) return;

        try {
            const videoElement = document.getElementById('hand-video');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            });

            videoElement.srcObject = stream;
            
            this.camera = new Camera(videoElement, {
                onFrame: async () => {
                    await this.hands.send({ image: videoElement });
                },
                width: 640,
                height: 480
            });

            await this.camera.start();
            this.isActive = true;

            document.getElementById('hand-tracking-overlay').style.display = 'flex';
            this.updateGestureList();

            console.log('🎥 Advanced Hand Tracking started');
        } catch (error) {
            console.error('❌ Camera error:', error);
            alert('Camera access required for hand tracking');
        }
    }

    stop() {
        if (!this.isActive) return;

        if (this.camera) this.camera.stop();
        
        const videoElement = document.getElementById('hand-video');
        if (videoElement.srcObject) {
            videoElement.srcObject.getTracks().forEach(track => track.stop());
        }

        document.getElementById('hand-tracking-overlay').style.display = 'none';
        this.isActive = false;
        this.cursorControlEnabled = false;
        console.log('🛑 Hand Tracking stopped');
    }

    onHandResults(results) {
        const canvasElement = document.getElementById('hand-canvas');
        const videoElement = document.getElementById('hand-video');
        const canvasCtx = canvasElement.getContext('2d');

        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            const landmarks = results.multiHandLandmarks[0];
            
            // Draw hand
            drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
                color: '#00ff41',
                lineWidth: 2
            });
            
            drawLandmarks(canvasCtx, landmarks, {
                color: '#00ff41',
                fillColor: '#0d1117',
                lineWidth: 1,
                radius: 3
            });

            // Process gestures
            this.processGestures(landmarks);
            
            // Cursor control
            if (this.cursorControlEnabled) {
                this.updateCursor(landmarks);
            }
            
            // Store for next frame
            this.previousLandmarks = landmarks;
        } else {
            this.updateGestureIndicator('none', '🖐️', 'Show hand');
            this.previousLandmarks = null;
        }

        canvasCtx.restore();
    }

    processGestures(landmarks) {
        const gesture = this.recognizeGesture(landmarks);
        
        if (gesture !== 'unknown' && gesture !== this.lastGesture) {
            this.executeGesture(gesture, landmarks);
            this.lastGesture = gesture;
            
            // Clear after delay
            setTimeout(() => {
                this.lastGesture = null;
            }, 1500);
        }
    }

    recognizeGesture(landmarks) {
        const fingers = this.getFingerStates(landmarks);
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const middleTip = landmarks[12];
        const ringTip = landmarks[16];
        const pinkyTip = landmarks[20];
        const wrist = landmarks[0];

        // Calculate distances
        const thumbIndexDist = this.distance(thumbTip, indexTip);
        const thumbMiddleDist = this.distance(thumbTip, middleTip);
        
        // PINCH (thumb + index close) - CURSOR CONTROL / DRAG
        if (thumbIndexDist < 0.05) {
            return 'pinch';
        }
        
        // POINTING (only index) - ACTIVATE CURSOR
        if (fingers[1] && !fingers[2] && !fingers[3] && !fingers[4]) {
            return 'pointing';
        }
        
        // OPEN PALM (all fingers) - WAKE FRIDAY
        if (fingers.every(f => f)) {
            return 'open_palm';
        }
        
        // FIST (all closed) - STOP
        if (fingers.every(f => !f)) {
            return 'fist';
        }
        
        // THUMBS UP - NEW CHAT
        if (!fingers[1] && !fingers[2] && !fingers[3] && !fingers[4] && thumbTip.y < landmarks[3].y) {
            return 'thumbs_up';
        }
        
        // PEACE (index + middle) - REPEAT
        if (fingers[1] && fingers[2] && !fingers[3] && !fingers[4]) {
            return 'peace';
        }
        
        // THREE FINGERS (index + middle + ring) - VOLUME CONTROL
        if (fingers[1] && fingers[2] && fingers[3] && !fingers[4]) {
            return 'three_fingers';
        }
        
        // FOUR FINGERS (no thumb) - MUSIC CONTROL
        if (fingers[1] && fingers[2] && fingers[3] && fingers[4] && !fingers[0]) {
            return 'four_fingers';
        }
        
        // SWIPE LEFT/RIGHT
        if (this.previousLandmarks) {
            const prevWrist = this.previousLandmarks[0];
            const deltaX = wrist.x - prevWrist.x;
            
            if (Math.abs(deltaX) > 0.15) {
                return deltaX > 0 ? 'swipe_right' : 'swipe_left';
            }
        }
        
        // SWIPE UP/DOWN
        if (this.previousLandmarks) {
            const prevWrist = this.previousLandmarks[0];
            const deltaY = wrist.y - prevWrist.y;
            
            if (Math.abs(deltaY) > 0.15) {
                return deltaY > 0 ? 'swipe_down' : 'swipe_up';
            }
        }

        return 'unknown';
    }

    getFingerStates(landmarks) {
        const fingerTips = [4, 8, 12, 16, 20];
        const fingerPIPs = [3, 6, 10, 14, 18];
        const states = [];
        
        for (let i = 0; i < 5; i++) {
            const tip = landmarks[fingerTips[i]];
            const pip = landmarks[fingerPIPs[i]];
            
            if (i === 0) {
                states.push(Math.abs(tip.x - pip.x) > 0.05);
            } else {
                states.push(tip.y < pip.y);
            }
        }
        
        return states;
    }

    distance(p1, p2) {
        return Math.sqrt(
            Math.pow(p1.x - p2.x, 2) + 
            Math.pow(p1.y - p2.y, 2) + 
            Math.pow(p1.z - p2.z, 2)
        );
    }

    executeGesture(gesture, landmarks) {
        console.log('🖐️ Gesture:', gesture);
        
        switch (gesture) {
            case 'pointing':
                this.cursorControlEnabled = true;
                this.updateGestureIndicator(gesture, '☝️', 'Cursor Control Active');
                break;

            case 'pinch':
                this.handlePinch(landmarks);
                break;

            case 'open_palm':
                this.updateGestureIndicator(gesture, '👋', 'Waking FRIDAY...');
                window.dispatchEvent(new CustomEvent('gesture-wake'));
                break;

            case 'fist':
                this.cursorControlEnabled = false;
                this.updateGestureIndicator(gesture, '✊', 'Stop');
                window.dispatchEvent(new CustomEvent('gesture-stop'));
                break;

            case 'thumbs_up':
                this.updateGestureIndicator(gesture, '👍', 'New Chat');
                window.dispatchEvent(new CustomEvent('gesture-new-chat'));
                break;

            case 'peace':
                this.updateGestureIndicator(gesture, '✌️', 'Repeat');
                window.dispatchEvent(new CustomEvent('gesture-repeat'));
                break;

            case 'three_fingers':
                this.handleVolumeControl(landmarks);
                break;

            case 'four_fingers':
                this.handleMusicControl();
                break;

            case 'swipe_left':
                this.updateGestureIndicator(gesture, '👈', 'Previous Track');
                this.executeSystemCommand('music_previous');
                break;

            case 'swipe_right':
                this.updateGestureIndicator(gesture, '👉', 'Next Track');
                this.executeSystemCommand('music_next');
                break;

            case 'swipe_up':
                this.updateGestureIndicator(gesture, '☝️', 'Volume Up');
                this.executeSystemCommand('volume_up');
                break;

            case 'swipe_down':
                this.updateGestureIndicator(gesture, '👇', 'Volume Down');
                this.executeSystemCommand('volume_down');
                break;
        }
    }

    updateCursor(landmarks) {
        const indexTip = landmarks[8];
        
        // Map hand position to screen coordinates (with deadzone)
        const deadzone = 0.05;  // 5% deadzone at edges
        let x = indexTip.x;
        let y = indexTip.y;
        
        // Apply deadzone
        if (x < deadzone) x = deadzone;
        if (x > 1 - deadzone) x = 1 - deadzone;
        if (y < deadzone) y = deadzone;
        if (y > 1 - deadzone) y = 1 - deadzone;
        
        const screenX = (1 - x) * window.innerWidth;
        const screenY = y * window.innerHeight;
        
        // Add to history for better smoothing
        this.cursorHistory.push({ x: screenX, y: screenY });
        if (this.cursorHistory.length > this.maxCursorHistory) {
            this.cursorHistory.shift();
        }
        
        // Calculate smoothed position (average of history)
        const avgX = this.cursorHistory.reduce((sum, pos) => sum + pos.x, 0) / this.cursorHistory.length;
        const avgY = this.cursorHistory.reduce((sum, pos) => sum + pos.y, 0) / this.cursorHistory.length;
        
        this.lastCursorX = avgX;
        this.lastCursorY = avgY;
        
        // Visual cursor indicator with trail effect
        this.showVirtualCursor(this.lastCursorX, this.lastCursorY);
    }

    showVirtualCursor(x, y) {
        let cursor = document.getElementById('virtual-cursor');
        if (!cursor) {
            cursor = document.createElement('div');
            cursor.id = 'virtual-cursor';
            cursor.style.cssText = `
                position: fixed;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: rgba(0, 255, 65, 0.8);
                border: 2px solid #00ff41;
                pointer-events: none;
                z-index: 99999;
                box-shadow: 0 0 20px #00ff41;
                transition: all 0.05s ease;
            `;
            document.body.appendChild(cursor);
        }
        
        cursor.style.left = `${x}px`;
        cursor.style.top = `${y}px`;
        cursor.style.display = this.cursorControlEnabled ? 'block' : 'none';
    }

    handlePinch(landmarks) {
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const distance = this.distance(thumbTip, indexTip);
        
        // More accurate pinch detection
        if (distance < 0.04 && !this.isPinching) {
            this.isPinching = true;
            this.pinchStartTime = Date.now();
            this.pinchConfidence++;
            this.updateGestureIndicator('pinch', '🤏', 'Click');
            
            // Simulate click at cursor position
            if (this.cursorControlEnabled) {
                console.log('🖱️ Virtual Click at:', Math.round(this.lastCursorX), Math.round(this.lastCursorY));
                
                // Find element at cursor position
                const element = document.elementFromPoint(this.lastCursorX, this.lastCursorY);
                if (element && element.click) {
                    element.click();
                    console.log('✅ Clicked element:', element.tagName);
                    this.stats.successfulActions++;
                }
            }
        } else if (distance > 0.06) {
            this.isPinching = false;
        }
    }

    handleVolumeControl(landmarks) {
        const indexTip = landmarks[8];
        const volume = Math.round((1 - indexTip.y) * 100);
        
        if (Math.abs(volume - this.lastVolume) > 5) {
            this.lastVolume = volume;
            this.updateGestureIndicator('three_fingers', '🔊', `Volume: ${volume}%`);
            this.executeSystemCommand('set_volume', { volume });
        }
    }

    handleMusicControl() {
        this.updateGestureIndicator('four_fingers', '🎵', 'Play/Pause Music');
        this.executeSystemCommand('music_toggle');
    }

    async executeSystemCommand(command, params = {}) {
        try {
            console.log('⚙️ Executing gesture command:', command, params);
            
            // Execute via FRIDAY gesture control API
            const response = await fetch(`${API_BASE_URL}/api/gesture/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    gesture: command,
                    params: params
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ Gesture command result:', result);
            
            // Show feedback
            if (result.success) {
                this.showGestureFeedback(command, 'success');
            } else {
                this.showGestureFeedback(command, 'error');
            }
            
            return result;
            
        } catch (error) {
            console.error('❌ Gesture command failed:', error);
            this.showGestureFeedback(command, 'error');
        }
    }
    
    showGestureFeedback(command, status) {
        // Create temporary toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            background: ${status === 'success' ? '#00ff41' : '#ff4444'};
            color: #000;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            z-index: 99999;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        `;
        toast.textContent = `${status === 'success' ? '✓' : '✗'} ${command.replace('_', ' ')}`;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    updateGestureIndicator(gesture, emoji, name) {
        const indicator = document.getElementById('gesture-indicator');
        if (!indicator) return;
        
        const emojiElement = indicator.querySelector('.gesture-emoji');
        const nameElement = indicator.querySelector('.gesture-name');
        
        emojiElement.textContent = emoji;
        nameElement.textContent = name;
        
        const colors = {
            'open_palm': '#00ff41',
            'fist': '#ff4444',
            'thumbs_up': '#00aaff',
            'peace': '#ffaa00',
            'pointing': '#aa00ff',
            'pinch': '#ff00ff',
            'three_fingers': '#00ffff',
            'four_fingers': '#ffff00',
            'swipe_left': '#ff8800',
            'swipe_right': '#ff8800',
            'swipe_up': '#00ff88',
            'swipe_down': '#ff0088'
        };
        
        const color = colors[gesture] || '#666';
        indicator.style.borderColor = color;
        indicator.style.boxShadow = `0 0 20px ${color}40`;
    }

    updateGestureList() {
        const container = document.querySelector('.hand-tracking-gestures');
        if (!container) return;
        
        container.innerHTML = `
            <div class="gesture-help"><span>👋</span>Open Palm → Wake FRIDAY</div>
            <div class="gesture-help"><span>✊</span>Fist → Stop</div>
            <div class="gesture-help"><span>👍</span>Thumbs Up → New Chat</div>
            <div class="gesture-help"><span>✌️</span>Peace → Repeat</div>
            <div class="gesture-help"><span>☝️</span>Pointing → Cursor Control</div>
            <div class="gesture-help"><span>🤏</span>Pinch → Click</div>
            <div class="gesture-help"><span>🖖</span>3 Fingers → Volume</div>
            <div class="gesture-help"><span>🖐️</span>4 Fingers → Music</div>
            <div class="gesture-help"><span>👈</span>Swipe Left → Previous</div>
            <div class="gesture-help"><span>👉</span>Swipe Right → Next</div>
            <div class="gesture-help"><span>☝️</span>Swipe Up → Vol+</div>
            <div class="gesture-help"><span>👇</span>Swipe Down → Vol-</div>
        `;
    }
    
    // Get gesture statistics
    getStats() {
        return {
            ...this.stats,
            active: this.isActive,
            cursorControl: this.cursorControlEnabled
        };
    }
}

// Global instance
window.handTrackerAdvanced = new AdvancedHandTrackingController();

// Initialize
window.addEventListener('DOMContentLoaded', async () => {
    const initialized = await window.handTrackerAdvanced.initialize();
    
    if (!initialized) {
        console.error('Failed to initialize advanced hand tracking');
        return;
    }

    // Button handler
    const handBtn = document.getElementById('hand-tracking-btn');
    if (handBtn) {
        handBtn.addEventListener('click', () => {
            if (window.handTrackerAdvanced.isActive) {
                window.handTrackerAdvanced.stop();
                handBtn.classList.remove('active');
            } else {
                window.handTrackerAdvanced.start();
                handBtn.classList.add('active');
            }
        });
    }

    // Close button
    const closeBtn = document.getElementById('close-hand-tracking');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            window.handTrackerAdvanced.stop();
            if (handBtn) handBtn.classList.remove('active');
        });
    }
});

console.log('🖐️ Advanced Hand Tracking module loaded');

