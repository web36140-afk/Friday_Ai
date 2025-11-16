// ============================================
// ENHANCED WAKE WORD DETECTION SYSTEM
// ============================================
// Advanced wake word with multiple variations and real-life usability

class EnhancedWakeWordSystem {
    constructor() {
        this.isActive = false;
        this.recognition = null;
        this.isListeningForCommand = false;
        this.wakeWordVariations = [
            // English
            'friday', 'hey friday', 'ok friday', 'hi friday',
            // Hindi
            'फ्राइडे', 'हे फ्राइडे', 
            // Nepali  
            'फ्राइडे'
        ];
        
        // Statistics
        this.detectionCount = 0;
        this.lastDetectionTime = null;
        
        console.log('🎤 Enhanced Wake Word System initialized');
    }

    start() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.error('Speech recognition not supported');
            return false;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;  // Faster detection
        this.recognition.lang = window.fridayState?.language || 'en-US';
        this.recognition.maxAlternatives = 3;  // Check multiple possibilities

        this.recognition.onresult = (event) => {
            const last = event.results.length - 1;
            const result = event.results[last];
            
            if (!result.isFinal && result[0].confidence > 0.6) {
                // Check interim results for faster response
                this.checkForWakeWord(result[0].transcript);
            }
            
            if (result.isFinal) {
                // Also check final result
                this.checkForWakeWord(result[0].transcript);
            }
        };

        this.recognition.onerror = (event) => {
            if (event.error === 'no-speech') {
                // Silent, just continue
                return;
            }
            
            if (event.error === 'aborted') {
                return;  // Normal when we stop it
            }
            
            console.error('Wake word recognition error:', event.error);
            
            // Auto-restart on error
            if (this.isActive) {
                setTimeout(() => {
                    if (this.isActive) this.recognition.start();
                }, 1000);
            }
        };

        this.recognition.onend = () => {
            // Auto-restart if still active
            if (this.isActive && !this.isListeningForCommand) {
                setTimeout(() => {
                    if (this.isActive) this.recognition.start();
                }, 100);
            }
        };

        this.recognition.start();
        this.isActive = true;
        this.showWakeWordIndicator(true);
        
        console.log('🎤 Wake word detection started');
        return true;
    }

    checkForWakeWord(transcript) {
        const text = transcript.toLowerCase().trim();
        
        // Check if any wake word variation is detected
        const detected = this.wakeWordVariations.some(word => {
            return text.includes(word) || text === word;
        });

        if (detected) {
            console.log('🔔 WAKE WORD DETECTED:', text);
            this.onWakeWordDetected();
        }
    }

    onWakeWordDetected() {
        // Prevent rapid repeated detections
        const now = Date.now();
        if (this.lastDetectionTime && (now - this.lastDetectionTime) < 2000) {
            console.log('⏸️ Too soon after last detection, ignoring');
            return;
        }
        
        this.lastDetectionTime = now;
        this.detectionCount++;
        
        // Stop any ongoing speech IMMEDIATELY
        this.interruptSpeech();
        
        // Visual feedback
        this.showActivationFeedback();
        
        // Play activation sound
        this.playActivationTone();
        
        // Stop wake word detection temporarily
        this.isListeningForCommand = true;
        this.recognition.stop();
        
        // Start command listening
        setTimeout(() => {
            this.startCommandListening();
        }, 500);
    }

    interruptSpeech() {
        console.log('🛑 Interrupting any ongoing speech...');
        
        // Stop backend TTS
        if (window.currentAudio) {
            window.currentAudio.pause();
            window.currentAudio = null;
        }
        
        // Stop browser TTS
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        
        // Remove speaking indicators
        const voiceBtn = document.getElementById('voice-output-btn');
        if (voiceBtn) voiceBtn.classList.remove('speaking');
        
        const stopBtn = document.getElementById('stop-speech-btn');
        if (stopBtn) stopBtn.style.display = 'none';
    }

    showActivationFeedback() {
        // Pulse the wake word button
        const wakeBtn = document.getElementById('wake-word-btn');
        if (wakeBtn) {
            wakeBtn.style.animation = 'none';
            setTimeout(() => {
                wakeBtn.style.animation = 'pulse 0.3s ease-in-out 3';
            }, 10);
        }

        // Show processing indicator
        const indicator = document.getElementById('processing-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }

        // Flash the screen border (subtle)
        document.body.style.boxShadow = 'inset 0 0 50px rgba(0, 217, 255, 0.5)';
        setTimeout(() => {
            document.body.style.boxShadow = '';
        }, 500);
    }

    playActivationTone() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Pleasant activation tone
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (e) {
            // Silent fail
        }
    }

    startCommandListening() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const commandRecognition = new SpeechRecognition();
        
        commandRecognition.lang = window.fridayState?.language || 'en-US';
        commandRecognition.continuous = false;
        commandRecognition.interimResults = false;
        commandRecognition.maxAlternatives = 1;

        console.log('🎤 Listening for command...');

        commandRecognition.onresult = async (event) => {
            const command = event.results[0][0].transcript.trim();
            const confidence = event.results[0][0].confidence;
            
            console.log(`🎤 Command: "${command}" (confidence: ${(confidence * 100).toFixed(1)}%)`);
            
            // Hide processing indicator
            const indicator = document.getElementById('processing-indicator');
            if (indicator) indicator.style.display = 'none';
            
            // Execute command
            if (command) {
                await this.executeVoiceCommand(command);
            }
            
            // Resume wake word detection
            this.isListeningForCommand = false;
            setTimeout(() => {
                if (this.isActive) this.recognition.start();
            }, 500);
        };

        commandRecognition.onerror = (event) => {
            console.error('Command recognition error:', event.error);
            
            const indicator = document.getElementById('processing-indicator');
            if (indicator) indicator.style.display = 'none';
            
            // Resume wake word detection
            this.isListeningForCommand = false;
            if (this.isActive) {
                setTimeout(() => this.recognition.start(), 500);
            }
        };

        commandRecognition.start();
    }

    async executeVoiceCommand(command) {
        const lowerCommand = command.toLowerCase();
        
        // ============================================
        // SYSTEM CONTROL COMMANDS (Direct execution)
        // ============================================
        
        // STOP - Stop speaking
        if (lowerCommand.includes('stop') || lowerCommand.includes('रोको') || lowerCommand.includes('रोक') || lowerCommand.includes('बन्द')) {
            console.log('🛑 Stop command detected');
            this.interruptSpeech();
            this.showCommandFeedback('Stopped', '🛑');
            return;
        }
        
        // SLEEP PC
        if (lowerCommand.includes('sleep') || lowerCommand.includes('सो जाओ') || lowerCommand.includes('निद्रा')) {
            console.log('😴 Sleep PC command');
            this.showCommandFeedback('Putting PC to sleep...', '😴');
            await this.executeSystemCommand('sleep_pc');
            return;
        }
        
        // LOCK PC
        if (lowerCommand.includes('lock') || lowerCommand.includes('लॉक करो') || lowerCommand.includes('बन्द गर्नुहोस्')) {
            console.log('🔒 Lock PC command');
            this.showCommandFeedback('Locking PC...', '🔒');
            await this.executeSystemCommand('lock_pc');
            return;
        }
        
        // SHUTDOWN PC (with confirmation)
        if (lowerCommand.includes('shutdown') || lowerCommand.includes('shut down') || lowerCommand.includes('बन्द करो') || lowerCommand.includes('बन्द गर')) {
            console.log('⚠️ Shutdown command - needs confirmation');
            if (confirm('Shutdown PC in 30 seconds? Click OK to confirm.')) {
                this.showCommandFeedback('Shutting down...', '⚡');
                await this.executeSystemCommand('shutdown_pc');
            }
            return;
        }
        
        // NEW CHAT
        if (lowerCommand.includes('new chat') || lowerCommand.includes('नयाँ च्याट') || lowerCommand.includes('नई चैट')) {
            console.log('🆕 New chat command');
            if (window.startNewChat) window.startNewChat();
            this.showCommandFeedback('Starting new chat', '🆕');
            return;
        }
        
        // REPEAT
        if (lowerCommand.includes('repeat') || lowerCommand.includes('दोहोराउनुहोस्') || lowerCommand.includes('दोहराओ')) {
            console.log('🔁 Repeat command');
            const messages = document.querySelectorAll('.jarvis-message.assistant');
            if (messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                const text = lastMessage.querySelector('.message-text')?.textContent;
                if (text && window.speakText) {
                    window.speakText(text);
                    this.showCommandFeedback('Repeating last response', '🔁');
                }
            }
            return;
        }
        
        // YouTube detection (multi-language)
        const isYouTubeCommand = 
            lowerCommand.includes('youtube') ||
            lowerCommand.includes('play') ||
            lowerCommand.includes('song') ||
            lowerCommand.includes('video') ||
            lowerCommand.includes('music') ||
            lowerCommand.includes('गाना') ||
            lowerCommand.includes('गीत') ||
            lowerCommand.includes('खेल्नुहोस्') ||
            lowerCommand.includes('चलाओ');
        
        if (isYouTubeCommand) {
            console.log('🎵 YouTube command detected:', command);
            // Let FRIDAY's AI handle it with the youtube_control tool
        }
        
        // Regular command - send to FRIDAY
        if (window.addMessage && window.streamChatResponse) {
            window.addMessage('user', command);
            await window.streamChatResponse(command);
        }
    }
    
    async executeSystemCommand(command) {
        try {
            const API_BASE_URL = 'http://localhost:8000';
            
            const commandMap = {
                'sleep_pc': { gesture: 'sleep_pc' },
                'lock_pc': { gesture: 'lock_pc' },
                'shutdown_pc': { gesture: 'shutdown_pc' }
            };
            
            const cmd = commandMap[command];
            if (!cmd) return;
            
            const response = await fetch(`${API_BASE_URL}/api/gesture/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cmd)
            });
            
            const result = await response.json();
            console.log('✅ System command executed:', result);
            
        } catch (error) {
            console.error('❌ System command failed:', error);
        }
    }
    
    showCommandFeedback(message, emoji) {
        // Create temporary notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1.1rem;
            z-index: 99999;
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.5);
            animation: slideInRight 0.3s ease;
        `;
        toast.innerHTML = `<span style="font-size: 1.5rem; margin-right: 0.5rem;">${emoji}</span>${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    stop() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.isActive = false;
        this.isListeningForCommand = false;
        this.showWakeWordIndicator(false);
        
        console.log('🛑 Wake word detection stopped');
    }

    showWakeWordIndicator(active) {
        const wakeBtn = document.getElementById('wake-word-btn');
        if (wakeBtn) {
            if (active) {
                wakeBtn.classList.add('active');
                wakeBtn.title = 'Wake Word Active - Say "FRIDAY" to activate';
            } else {
                wakeBtn.classList.remove('active');
                wakeBtn.title = 'Wake Word - Click to enable';
            }
        }
    }

    getStats() {
        return {
            active: this.isActive,
            detections: this.detectionCount,
            lastDetection: this.lastDetectionTime
        };
    }
}

// Global instance
window.enhancedWakeWord = new EnhancedWakeWordSystem();

// Expose fridayState for wake word system
window.fridayState = null;

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    // Connect to main.js state
    setTimeout(() => {
        if (window.state) {
            window.fridayState = window.state;
            console.log('✅ Wake word connected to FRIDAY state');
        }
    }, 1000);
});

console.log('✅ Enhanced Wake Word module loaded');

