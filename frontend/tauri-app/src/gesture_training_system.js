// ============================================
// GESTURE TRAINING & LEARNING SYSTEM
// Train custom gestures and improve recognition
// ============================================

class GestureTrainingSystem {
    constructor() {
        this.customGestures = {};
        this.trainingMode = false;
        this.recordedSamples = [];
        this.currentGestureName = null;
        
        // Load saved custom gestures
        this.loadCustomGestures();
        
        console.log('🎓 Gesture Training System loaded');
    }

    showTrainingUI() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = 'training-modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h2>🎓 Gesture Training</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="settings-section">
                        <h3>Create Custom Gesture</h3>
                        <p style="color: var(--jarvis-text-dim); margin-bottom: 1rem;">
                            Record a custom hand gesture and assign an action to it.
                        </p>
                        
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">Gesture Name</span>
                            <input type="text" id="gesture-name-input" placeholder="e.g., Wave Hello" 
                                   style="width: 100%; padding: 0.75rem; background: rgba(0, 217, 255, 0.1);
                                          border: 1px solid var(--jarvis-border); border-radius: 8px;
                                          color: white; font-size: 1rem;">
                        </label>
                        
                        <label style="display: block; margin-bottom: 1rem;">
                            <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">Action</span>
                            <select id="gesture-action-select" class="jarvis-select">
                                <option value="click">Single Click</option>
                                <option value="double_click">Double Click</option>
                                <option value="right_click">Right Click</option>
                                <option value="scroll_up">Scroll Up</option>
                                <option value="scroll_down">Scroll Down</option>
                                <option value="volume_up">Volume Up</option>
                                <option value="volume_down">Volume Down</option>
                                <option value="next_track">Next Track</option>
                                <option value="prev_track">Previous Track</option>
                                <option value="maximize">Maximize Window</option>
                                <option value="minimize">Minimize Window</option>
                                <option value="close_window">Close Window</option>
                                <option value="show_desktop">Show Desktop</option>
                                <option value="screenshot">Take Screenshot</option>
                                <option value="custom">Custom Command...</option>
                            </select>
                        </label>
                        
                        <div id="custom-command-input" style="display: none; margin-bottom: 1rem;">
                            <label style="display: block;">
                                <span style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim);">Custom Command</span>
                                <input type="text" id="custom-command-text" placeholder="e.g., chrome.exe" 
                                       style="width: 100%; padding: 0.75rem; background: rgba(0, 217, 255, 0.1);
                                              border: 1px solid var(--jarvis-border); border-radius: 8px;
                                              color: white; font-size: 1rem;">
                            </label>
                        </div>
                        
                        <button id="start-recording-btn" class="friday-btn" onclick="window.gestureTraining.startRecording()" style="width: 100%; margin-top: 1rem;">
                            🔴 Start Recording Gesture
                        </button>
                        
                        <div id="recording-status" style="display: none; margin-top: 1rem; padding: 1rem;
                                                          background: rgba(255, 51, 102, 0.2); border-radius: 8px;
                                                          border: 1px solid var(--jarvis-error);">
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <div style="width: 12px; height: 12px; background: var(--jarvis-error); border-radius: 50%; animation: pulse 1s infinite;"></div>
                                <div>
                                    <strong>Recording...</strong><br>
                                    <span style="font-size: 0.85rem; opacity: 0.9;">Perform the gesture 3 times</span>
                                </div>
                            </div>
                            <div style="margin-top: 0.75rem; font-size: 0.9rem;">
                                Samples: <span id="samples-count">0</span> / 3
                            </div>
                        </div>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Saved Custom Gestures</h3>
                        <div id="custom-gestures-list" style="max-height: 200px; overflow-y: auto;">
                            <p style="color: var(--jarvis-text-dim); font-size: 0.9rem;">
                                No custom gestures yet. Create one above!
                            </p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="friday-btn-secondary" onclick="this.closest('.modal-overlay').remove();">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Setup event listeners
        this.setupTrainingListeners();
        
        // Load and display custom gestures
        this.displayCustomGestures();
    }

    setupTrainingListeners() {
        // Show custom command input when "Custom" is selected
        const actionSelect = document.getElementById('gesture-action-select');
        const customInput = document.getElementById('custom-command-input');
        
        if (actionSelect && customInput) {
            actionSelect.addEventListener('change', (e) => {
                customInput.style.display = e.target.value === 'custom' ? 'block' : 'none';
            });
        }
    }

    startRecording() {
        const gestureNameInput = document.getElementById('gesture-name-input');
        const gestureName = gestureNameInput?.value.trim();
        
        if (!gestureName) {
            if (window.notificationSystem) {
                window.notificationSystem.show('Please enter a gesture name!', 'warning');
            }
            return;
        }
        
        this.currentGestureName = gestureName;
        this.trainingMode = true;
        this.recordedSamples = [];
        
        // Show recording status
        const recordingStatus = document.getElementById('recording-status');
        if (recordingStatus) {
            recordingStatus.style.display = 'block';
        }
        
        // Update button
        const btn = document.getElementById('start-recording-btn');
        if (btn) {
            btn.textContent = '⏹️ Stop Recording';
            btn.onclick = () => this.stopRecording();
        }
        
        console.log(`🔴 Started recording gesture: ${gestureName}`);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(
                `Recording "${gestureName}"... Perform the gesture 3 times`,
                'info',
                3000
            );
        }
    }

    stopRecording() {
        this.trainingMode = false;
        
        // Hide recording status
        const recordingStatus = document.getElementById('recording-status');
        if (recordingStatus) {
            recordingStatus.style.display = 'none';
        }
        
        // Reset button
        const btn = document.getElementById('start-recording-btn');
        if (btn) {
            btn.textContent = '🔴 Start Recording Gesture';
            btn.onclick = () => this.startRecording();
        }
        
        if (this.recordedSamples.length >= 3) {
            this.saveCustomGesture();
        } else {
            if (window.notificationSystem) {
                window.notificationSystem.show(
                    'Not enough samples. Please record at least 3 samples.',
                    'warning'
                );
            }
        }
        
        console.log('⏹️ Stopped recording');
    }

    recordSample(landmarkData) {
        if (!this.trainingMode) return;
        
        this.recordedSamples.push({
            landmarks: landmarkData,
            timestamp: Date.now()
        });
        
        // Update samples count
        const samplesCount = document.getElementById('samples-count');
        if (samplesCount) {
            samplesCount.textContent = this.recordedSamples.length;
        }
        
        console.log(`📸 Recorded sample ${this.recordedSamples.length}/3`);
        
        // Auto-stop after 3 samples
        if (this.recordedSamples.length >= 3) {
            setTimeout(() => this.stopRecording(), 500);
        }
    }

    saveCustomGesture() {
        const actionSelect = document.getElementById('gesture-action-select');
        const action = actionSelect?.value || 'click';
        
        const customCommand = document.getElementById('custom-command-text');
        const customValue = customCommand?.value.trim();
        
        const gesture = {
            name: this.currentGestureName,
            action: action,
            customCommand: action === 'custom' ? customValue : null,
            samples: this.recordedSamples,
            created: new Date().toISOString()
        };
        
        this.customGestures[this.currentGestureName] = gesture;
        
        // Save to localStorage
        localStorage.setItem('custom_gestures', JSON.stringify(this.customGestures));
        
        console.log('✅ Custom gesture saved:', gesture);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(
                `✅ Gesture "${this.currentGestureName}" saved!`,
                'success'
            );
        }
        
        // Refresh list
        this.displayCustomGestures();
    }

    loadCustomGestures() {
        const saved = localStorage.getItem('custom_gestures');
        if (saved) {
            try {
                this.customGestures = JSON.parse(saved);
                console.log(`✅ Loaded ${Object.keys(this.customGestures).length} custom gestures`);
            } catch (error) {
                console.error('Failed to load custom gestures:', error);
            }
        }
    }

    displayCustomGestures() {
        const list = document.getElementById('custom-gestures-list');
        if (!list) return;
        
        const gestures = Object.values(this.customGestures);
        
        if (gestures.length === 0) {
            list.innerHTML = `
                <p style="color: var(--jarvis-text-dim); font-size: 0.9rem;">
                    No custom gestures yet. Create one above!
                </p>
            `;
            return;
        }
        
        list.innerHTML = gestures.map(gesture => `
            <div style="padding: 0.75rem; background: rgba(0, 217, 255, 0.1); border-radius: 8px; margin-bottom: 0.5rem;
                        display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${gesture.name}</strong>
                    <div style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                        Action: ${gesture.action} | Samples: ${gesture.samples.length}
                    </div>
                </div>
                <button onclick="window.gestureTraining.deleteGesture('${gesture.name}')"
                        style="background: rgba(255, 51, 102, 0.2); border: 1px solid var(--jarvis-error);
                               color: var(--jarvis-error); padding: 0.5rem 1rem; border-radius: 6px;
                               cursor: pointer; font-weight: 600;">
                    Delete
                </button>
            </div>
        `).join('');
    }

    deleteGesture(gestureName) {
        delete this.customGestures[gestureName];
        localStorage.setItem('custom_gestures', JSON.stringify(this.customGestures));
        
        this.displayCustomGestures();
        
        if (window.notificationSystem) {
            window.notificationSystem.show(
                `Deleted gesture "${gestureName}"`,
                'info'
            );
        }
    }
}

// Global instance
window.gestureTraining = new GestureTrainingSystem();

console.log('✅ Gesture Training System module loaded');

