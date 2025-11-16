// ============================================
// FRIDAY HAND TRACKING MODULE
// ============================================
// Control FRIDAY with hand gestures using MediaPipe Hands

class HandTrackingController {
    constructor() {
        this.hands = null;
        this.camera = null;
        this.isActive = false;
        this.lastGesture = null;
        this.gestureDebounce = null;
        this.gestureHoldTime = 1000; // Hold gesture for 1 second
        
        // Gesture callbacks
        this.onGesture = null;
        
        console.log('🖐️ Hand Tracking Controller initialized');
    }

    async initialize() {
        try {
            // Initialize MediaPipe Hands
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                }
            });

            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.7,
                minTrackingConfidence: 0.5
            });

            this.hands.onResults((results) => this.onHandResults(results));

            console.log('✅ MediaPipe Hands initialized');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize hand tracking:', error);
            return false;
        }
    }

    async start() {
        if (this.isActive) {
            console.log('Hand tracking already active');
            return;
        }

        try {
            const videoElement = document.getElementById('hand-video');
            const canvasElement = document.getElementById('hand-canvas');

            // Get camera stream
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    width: 640, 
                    height: 480,
                    facingMode: 'user'
                }
            });

            videoElement.srcObject = stream;
            
            // Initialize camera
            this.camera = new Camera(videoElement, {
                onFrame: async () => {
                    await this.hands.send({ image: videoElement });
                },
                width: 640,
                height: 480
            });

            await this.camera.start();
            this.isActive = true;

            // Show overlay
            document.getElementById('hand-tracking-overlay').style.display = 'flex';

            console.log('🎥 Hand tracking started');
        } catch (error) {
            console.error('❌ Failed to start camera:', error);
            alert('Camera access denied. Please enable camera permissions.');
        }
    }

    stop() {
        if (!this.isActive) return;

        try {
            // Stop camera
            if (this.camera) {
                this.camera.stop();
            }

            // Stop video stream
            const videoElement = document.getElementById('hand-video');
            if (videoElement.srcObject) {
                videoElement.srcObject.getTracks().forEach(track => track.stop());
            }

            // Hide overlay
            document.getElementById('hand-tracking-overlay').style.display = 'none';

            this.isActive = false;
            console.log('🛑 Hand tracking stopped');
        } catch (error) {
            console.error('Error stopping hand tracking:', error);
        }
    }

    onHandResults(results) {
        const canvasElement = document.getElementById('hand-canvas');
        const videoElement = document.getElementById('hand-video');
        const canvasCtx = canvasElement.getContext('2d');

        // Set canvas size to match video
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        // Clear canvas
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

        // Draw hand landmarks if detected
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            for (const landmarks of results.multiHandLandmarks) {
                // Draw connections
                drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
                    color: '#00ff41',
                    lineWidth: 2
                });
                
                // Draw landmarks
                drawLandmarks(canvasCtx, landmarks, {
                    color: '#00ff41',
                    fillColor: '#0d1117',
                    lineWidth: 1,
                    radius: 3
                });

                // Recognize gesture
                const gesture = this.recognizeGesture(landmarks);
                this.handleGesture(gesture);
            }
        } else {
            // No hand detected
            this.updateGestureIndicator('none', '👋', 'Show hand to camera');
        }

        canvasCtx.restore();
    }

    recognizeGesture(landmarks) {
        // Calculate finger states
        const fingers = this.getFingerStates(landmarks);
        
        // Open Palm (all fingers extended) - WAKE WORD
        if (fingers.every(f => f)) {
            return 'open_palm';
        }
        
        // Fist (all fingers closed) - STOP
        if (fingers.every(f => !f)) {
            return 'fist';
        }
        
        // Thumbs Up - NEW CHAT
        if (!fingers[1] && !fingers[2] && !fingers[3] && !fingers[4] && landmarks[4].y < landmarks[3].y) {
            return 'thumbs_up';
        }
        
        // Peace Sign (index + middle extended) - REPEAT
        if (fingers[1] && fingers[2] && !fingers[3] && !fingers[4]) {
            return 'peace';
        }
        
        // Pointing (only index extended) - SELECT
        if (fingers[1] && !fingers[2] && !fingers[3] && !fingers[4]) {
            return 'pointing';
        }

        return 'unknown';
    }

    getFingerStates(landmarks) {
        // Thumb, Index, Middle, Ring, Pinky
        const fingerTips = [4, 8, 12, 16, 20];
        const fingerPIPs = [3, 6, 10, 14, 18];
        
        const states = [];
        
        for (let i = 0; i < 5; i++) {
            const tip = landmarks[fingerTips[i]];
            const pip = landmarks[fingerPIPs[i]];
            
            // Finger is extended if tip is higher than PIP (lower y value)
            if (i === 0) { // Thumb (check x instead)
                states.push(Math.abs(tip.x - pip.x) > 0.05);
            } else {
                states.push(tip.y < pip.y);
            }
        }
        
        return states;
    }

    handleGesture(gesture) {
        if (gesture === 'unknown' || gesture === this.lastGesture) {
            return;
        }

        // Debounce gesture detection
        if (this.gestureDebounce) {
            clearTimeout(this.gestureDebounce);
        }

        this.gestureDebounce = setTimeout(() => {
            this.lastGesture = gesture;
            this.executeGesture(gesture);
        }, 500); // 500ms hold time

        // Update UI
        this.updateGestureIndicator(gesture);
    }

    updateGestureIndicator(gesture, emoji = null, name = null) {
        const indicator = document.getElementById('gesture-indicator');
        const emojiElement = indicator.querySelector('.gesture-emoji');
        const nameElement = indicator.querySelector('.gesture-name');

        const gestureMap = {
            'open_palm': { emoji: '👋', name: 'Open Palm - Activating...', color: '#00ff41' },
            'fist': { emoji: '✊', name: 'Fist - Stopping...', color: '#ff4444' },
            'thumbs_up': { emoji: '👍', name: 'Thumbs Up - New Chat', color: '#00aaff' },
            'peace': { emoji: '✌️', name: 'Peace - Repeat', color: '#ffaa00' },
            'pointing': { emoji: '👉', name: 'Pointing', color: '#aa00ff' },
            'none': { emoji: emoji || '👋', name: name || 'No gesture', color: '#666' }
        };

        const gestureInfo = gestureMap[gesture] || gestureMap['none'];
        
        emojiElement.textContent = gestureInfo.emoji;
        nameElement.textContent = gestureInfo.name;
        indicator.style.borderColor = gestureInfo.color;
        indicator.style.boxShadow = `0 0 20px ${gestureInfo.color}40`;
    }

    executeGesture(gesture) {
        console.log('🖐️ Gesture detected:', gesture);

        // Execute gesture action
        switch (gesture) {
            case 'open_palm':
                // Wake FRIDAY
                console.log('👋 Open Palm - Waking FRIDAY');
                if (this.onGesture) {
                    this.onGesture('wake');
                }
                // Trigger wake word detection
                window.dispatchEvent(new CustomEvent('gesture-wake'));
                break;

            case 'fist':
                // Stop speaking
                console.log('✊ Fist - Stopping');
                if (this.onGesture) {
                    this.onGesture('stop');
                }
                window.dispatchEvent(new CustomEvent('gesture-stop'));
                break;

            case 'thumbs_up':
                // New chat
                console.log('👍 Thumbs Up - New Chat');
                if (this.onGesture) {
                    this.onGesture('new_chat');
                }
                window.dispatchEvent(new CustomEvent('gesture-new-chat'));
                break;

            case 'peace':
                // Repeat last
                console.log('✌️ Peace - Repeat');
                if (this.onGesture) {
                    this.onGesture('repeat');
                }
                window.dispatchEvent(new CustomEvent('gesture-repeat'));
                break;

            default:
                break;
        }

        // Clear last gesture after execution
        setTimeout(() => {
            this.lastGesture = null;
        }, 2000);
    }
}

// Global instance
window.handTracker = new HandTrackingController();

// Initialize when page loads
window.addEventListener('DOMContentLoaded', async () => {
    const initialized = await window.handTracker.initialize();
    
    if (!initialized) {
        console.error('Failed to initialize hand tracking');
        return;
    }

    // Hand tracking button
    const handBtn = document.getElementById('hand-tracking-btn');
    if (handBtn) {
        handBtn.addEventListener('click', () => {
            if (window.handTracker.isActive) {
                window.handTracker.stop();
                handBtn.classList.remove('active');
            } else {
                window.handTracker.start();
                handBtn.classList.add('active');
            }
        });
    }

    // Close button
    const closeBtn = document.getElementById('close-hand-tracking');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            window.handTracker.stop();
            if (handBtn) {
                handBtn.classList.remove('active');
            }
        });
    }
});

console.log('🖐️ Hand Tracking module loaded');

