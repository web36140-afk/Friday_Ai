// ============================================
// GESTURE OVERLAY UI - Professional Visual Feedback
// Shows real-time gesture detection and controls
// ============================================

class GestureOverlayUI {
    constructor() {
        this.overlayElement = null;
        this.gestureIndicators = {};
        this.isVisible = false;
        
        console.log('🎨 Gesture Overlay UI loaded');
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'gesture-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 999998;
            display: none;
        `;
        
        overlay.innerHTML = `
            <!-- Top Status Bar -->
            <div style="position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
                        background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(10, 20, 40, 0.9));
                        padding: 1rem 2rem; border-radius: 12px;
                        border: 1px solid rgba(0, 217, 255, 0.3);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);">
                <div style="display: flex; align-items: center; gap: 1.5rem; color: white;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div id="hand-status-indicator" style="width: 10px; height: 10px; background: #ff3366; border-radius: 50%; animation: pulse 1s infinite;"></div>
                        <span style="font-weight: 600; font-size: 0.95rem;">Hand Tracking</span>
                    </div>
                    <div style="font-size: 0.85rem; opacity: 0.8;">
                        FPS: <span id="tracking-fps">--</span> | 
                        Hands: <span id="hands-detected">0</span>
                    </div>
                </div>
            </div>
            
            <!-- Gesture Indicators (Right Side) -->
            <div style="position: absolute; top: 100px; right: 20px; display: flex; flex-direction: column; gap: 0.75rem;">
                <!-- Pinch Indicator -->
                <div id="gesture-indicator-pinch" class="gesture-indicator" data-gesture="pinch">
                    <span class="gesture-icon">👌</span>
                    <span class="gesture-label">Pinch to Click</span>
                    <div class="gesture-strength-bar"></div>
                </div>
                
                <!-- Grab Indicator -->
                <div id="gesture-indicator-grab" class="gesture-indicator" data-gesture="grab">
                    <span class="gesture-icon">✊</span>
                    <span class="gesture-label">Grab to Drag</span>
                    <div class="gesture-strength-bar"></div>
                </div>
                
                <!-- Swipe Indicator -->
                <div id="gesture-indicator-swipe" class="gesture-indicator" data-gesture="swipe">
                    <span class="gesture-icon">👋</span>
                    <span class="gesture-label">Swipe to Scroll</span>
                </div>
                
                <!-- Victory/Peace (Screenshot) -->
                <div id="gesture-indicator-peace" class="gesture-indicator" data-gesture="peace">
                    <span class="gesture-icon">✌️</span>
                    <span class="gesture-label">Peace - Screenshot</span>
                </div>
                
                <!-- Thumbs Up (Like/Approve) -->
                <div id="gesture-indicator-thumbs" class="gesture-indicator" data-gesture="thumbs">
                    <span class="gesture-icon">👍</span>
                    <span class="gesture-label">Thumbs Up - Confirm</span>
                </div>
            </div>
            
            <!-- Quick Actions (Bottom) -->
            <div style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                        background: rgba(0, 0, 0, 0.85);
                        padding: 0.75rem 1.5rem; border-radius: 50px;
                        border: 1px solid rgba(0, 217, 255, 0.3);
                        display: flex; gap: 1.5rem; align-items: center;">
                <div style="color: white; font-size: 0.85rem; font-weight: 600;">
                    Quick Actions:
                </div>
                <div style="display: flex; gap: 1rem; font-size: 0.8rem; color: var(--jarvis-text-dim);">
                    <span>👆 Point = Move</span>
                    <span>👌 Pinch = Click</span>
                    <span>✊ Grab = Drag</span>
                    <span>👋 Swipe = Scroll</span>
                </div>
            </div>
            
            <!-- Gesture Help Toggle (Bottom Right) -->
            <button id="gesture-help-toggle" onclick="window.gestureOverlay.toggleHelp()"
                    style="position: absolute; bottom: 20px; right: 20px;
                           background: rgba(0, 217, 255, 0.2);
                           border: 1px solid rgba(0, 217, 255, 0.4);
                           color: white; padding: 0.75rem 1.25rem;
                           border-radius: 8px; cursor: pointer;
                           pointer-events: all;
                           font-weight: 600; font-size: 0.9rem;
                           transition: all 0.3s;">
                ❓ Help
            </button>
        `;
        
        document.body.appendChild(overlay);
        this.overlayElement = overlay;
        
        // Add gesture indicator styles
        this.injectStyles();
        
        console.log('✨ Gesture overlay created');
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .gesture-indicator {
                background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(10, 20, 40, 0.9));
                border: 1px solid rgba(0, 217, 255, 0.2);
                border-radius: 12px;
                padding: 0.75rem 1rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                opacity: 0.5;
                transition: all 0.3s;
                min-width: 200px;
            }
            
            .gesture-indicator.active {
                opacity: 1;
                border-color: var(--jarvis-success);
                background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 217, 255, 0.2));
                box-shadow: 0 4px 20px rgba(0, 255, 136, 0.4);
                transform: scale(1.05);
            }
            
            .gesture-icon {
                font-size: 1.5rem;
            }
            
            .gesture-label {
                color: white;
                font-size: 0.85rem;
                font-weight: 600;
                flex: 1;
            }
            
            .gesture-strength-bar {
                width: 40px;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                overflow: hidden;
                position: relative;
            }
            
            .gesture-strength-bar::after {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: var(--strength, 0%);
                background: linear-gradient(90deg, var(--jarvis-primary), var(--jarvis-success));
                transition: width 0.1s ease;
            }
            
            #gesture-help-toggle:hover {
                background: rgba(0, 217, 255, 0.4);
                box-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
            }
        `;
        document.head.appendChild(style);
    }

    show() {
        if (!this.overlayElement) {
            this.createOverlay();
        }
        
        this.overlayElement.style.display = 'block';
        this.isVisible = true;
        
        console.log('👁️ Gesture overlay visible');
    }

    hide() {
        if (this.overlayElement) {
            this.overlayElement.style.display = 'none';
        }
        
        this.isVisible = false;
        console.log('🙈 Gesture overlay hidden');
    }

    updateGestureState(gestureName, isActive, strength = 0) {
        const indicator = document.getElementById(`gesture-indicator-${gestureName}`);
        if (!indicator) return;
        
        if (isActive) {
            indicator.classList.add('active');
            
            // Update strength bar if applicable
            const strengthBar = indicator.querySelector('.gesture-strength-bar');
            if (strengthBar) {
                strengthBar.style.setProperty('--strength', `${strength * 100}%`);
            }
        } else {
            indicator.classList.remove('active');
        }
    }

    updateFPS(fps) {
        const fpsElement = document.getElementById('tracking-fps');
        if (fpsElement) {
            fpsElement.textContent = fps.toFixed(0);
        }
    }

    updateHandsCount(count) {
        const handsElement = document.getElementById('hands-detected');
        const statusIndicator = document.getElementById('hand-status-indicator');
        
        if (handsElement) {
            handsElement.textContent = count;
        }
        
        if (statusIndicator) {
            if (count > 0) {
                statusIndicator.style.background = 'var(--jarvis-success)';
                statusIndicator.style.animation = 'none';
            } else {
                statusIndicator.style.background = '#ff3366';
                statusIndicator.style.animation = 'pulse 1s infinite';
            }
        }
    }

    toggleHelp() {
        const helpModal = document.createElement('div');
        helpModal.className = 'modal-overlay';
        helpModal.innerHTML = `
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h2>🖐️ Gesture Control Guide</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="settings-section">
                        <h3>Basic Gestures</h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                            <div style="padding: 1rem; background: rgba(0, 217, 255, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👆</div>
                                <strong>Point</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Use index finger to control cursor
                                </p>
                            </div>
                            <div style="padding: 1rem; background: rgba(0, 217, 255, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👌</div>
                                <strong>Pinch to Click</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Pinch thumb + index finger together
                                </p>
                            </div>
                            <div style="padding: 1rem; background: rgba(0, 217, 255, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✊</div>
                                <strong>Grab to Drag</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Close all fingers to drag items
                                </p>
                            </div>
                            <div style="padding: 1rem; background: rgba(0, 217, 255, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👋</div>
                                <strong>Swipe to Scroll</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Quick hand movement up/down/left/right
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Advanced Gestures</h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                            <div style="padding: 1rem; background: rgba(255, 170, 0, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✌️</div>
                                <strong>Peace Sign</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Take screenshot
                                </p>
                            </div>
                            <div style="padding: 1rem; background: rgba(255, 170, 0, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👍</div>
                                <strong>Thumbs Up</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Confirm action / Like
                                </p>
                            </div>
                            <div style="padding: 1rem; background: rgba(255, 170, 0, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✋</div>
                                <strong>Open Palm</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Stop / Pause
                                </p>
                            </div>
                            <div style="padding: 1rem; background: rgba(255, 170, 0, 0.1); border-radius: 8px;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤙</div>
                                <strong>Call Sign</strong>
                                <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                    Voice call / Start recording
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Desktop Control</h3>
                        <div style="line-height: 1.8; color: var(--jarvis-text-dim);">
                            <div>✅ <strong>Drag & Drop:</strong> Grab gesture + move hand</div>
                            <div>✅ <strong>Window Maximize:</strong> Swipe up</div>
                            <div>✅ <strong>Window Minimize:</strong> Swipe down</div>
                            <div>✅ <strong>Snap Left/Right:</strong> Swipe left/right near window</div>
                            <div>✅ <strong>Scroll:</strong> Swipe up/down</div>
                            <div>✅ <strong>Zoom:</strong> Pinch gesture (two hands)</div>
                            <div>✅ <strong>Close Window:</strong> Swipe left + grab</div>
                        </div>
                    </div>
                    
                    <div class="settings-section" style="background: rgba(0, 217, 255, 0.1); padding: 1rem; border-radius: 8px;">
                        <h4>💡 Tips for Best Performance</h4>
                        <ul style="margin-left: 1.5rem; line-height: 1.8; color: var(--jarvis-text-dim);">
                            <li>Keep hand 30-60cm from camera</li>
                            <li>Ensure good lighting (or use calibration for low light)</li>
                            <li>Move slowly for precise control</li>
                            <li>Use calibration settings for your environment</li>
                            <li>Close fist fully for reliable drag operations</li>
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="friday-btn" onclick="window.gestureCalibration.showCalibrationModal(); this.closest('.modal-overlay').remove();">
                        ⚙️ Open Calibration
                    </button>
                    <button class="friday-btn-secondary" onclick="this.closest('.modal-overlay').remove();">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpModal);
    }
}

// Global instance
window.gestureOverlay = new GestureOverlayUI();

// Auto-show overlay when gesture tracking starts
window.addEventListener('gesture-tracking-started', () => {
    if (window.gestureOverlay) {
        window.gestureOverlay.show();
    }
});

window.addEventListener('gesture-tracking-stopped', () => {
    if (window.gestureOverlay) {
        window.gestureOverlay.hide();
    }
});

console.log('✅ Gesture Overlay UI module loaded');

