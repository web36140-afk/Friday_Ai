// ============================================
// ADVANCED WAKE WORD SYSTEM - ALEXA/SIRI LEVEL
// ============================================
// Professional wake word with VAD, auto-submit, and smooth UX

class AdvancedWakeWordSystem {
    constructor() {
        this.isActive = false;
        this.wakeRecognition = null;
        this.commandRecognition = null;
        this.isListeningForCommand = false;
        this.silenceTimeout = null;
        this.commandStarted = false;
        this.currentCommand = '';
        this.isSubmitting = false; // Prevent duplicate submissions
        
        // Voice Activity Detection settings
        this.vadSettings = {
            silenceThreshold: 1200,  // 1.2 seconds of silence = auto-submit (faster response)
            minCommandLength: 2,      // Minimum 2 characters (more lenient)
            maxCommandDuration: 8000  // 8 seconds max (reasonable limit)
        };
        
        // Wake word variations
        this.wakeWords = [
            'friday', 'hey friday', 'ok friday', 'hi friday',
            'फ्राइडे', 'हे फ्राइडे',
            'फ्राइडे'
        ];
        
        console.log('🎯 Advanced Wake Word System initialized (Alexa/Siri level)');
    }

    start() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.error('❌ Speech recognition not supported');
            return false;
        }

        // ============================================
        // WAKE WORD LISTENER (Always On)
        // ============================================
        this.wakeRecognition = new SpeechRecognition();
        this.wakeRecognition.continuous = true;
        this.wakeRecognition.interimResults = true;
        this.wakeRecognition.lang = window.fridayState?.language || 'en-US';
        this.wakeRecognition.maxAlternatives = 3;

        this.wakeRecognition.onresult = (event) => {
            const last = event.results.length - 1;
            const result = event.results[last];
            const transcript = result[0].transcript.toLowerCase().trim();
            
            // Check for wake word (both interim and final)
            if (result[0].confidence > 0.6 || result.isFinal) {
                this.checkForWakeWord(transcript);
            }
        };

        this.wakeRecognition.onerror = (event) => {
            if (event.error !== 'no-speech' && event.error !== 'aborted') {
                console.error('Wake word error:', event.error);
                
                // Handle permission denied
                if (event.error === 'not-allowed') {
                    this.isActive = false;
                    this.showWakeIndicator(false);
                    
                    if (window.notificationSystem) {
                        window.notificationSystem.show(
                            '❌ Microphone access denied! Please allow microphone permissions in your browser settings, then try again.',
                            'error',
                            8000
                        );
                    }
                    return; // Don't auto-restart if permission denied
                }
            }
            
            // Auto-restart for other errors
            if (this.isActive && !this.isListeningForCommand && event.error !== 'not-allowed') {
                setTimeout(() => {
                    if (this.isActive) this.wakeRecognition.start();
                }, 1000);
            }
        };

        this.wakeRecognition.onend = () => {
            // Auto-restart if still active
            if (this.isActive && !this.isListeningForCommand) {
                setTimeout(() => {
                    if (this.isActive) this.wakeRecognition.start();
                }, 500);
            }
        };

        // Start listening
        this.wakeRecognition.start();
        this.isActive = true;
        this.showWakeIndicator(true);
        
        console.log('👂 Wake word listener active');
        return true;
    }

    checkForWakeWord(transcript) {
        if (this.isListeningForCommand) return; // Already listening for command
        
        const lowerTranscript = transcript.toLowerCase();
        
        // Check if any wake word variation is present
        const isWakeWord = this.wakeWords.some(word => 
            lowerTranscript.includes(word.toLowerCase())
        );
        
        if (isWakeWord) {
            console.log('🎯 WAKE WORD DETECTED:', transcript);
            this.onWakeWordDetected();
        }
    }

    onWakeWordDetected() {
        // STOP all current activities
        this.stopAllActivities();

        // Ensure TTS is interrupted cleanly (barge-in)
        if (window.streamingTTS && typeof window.streamingTTS.stopSpeaking === 'function') {
            window.streamingTTS.stopSpeaking();
        }
        
        // Show activation feedback
        this.showActivationFeedback();
        this.playActivationSound();
        
        // Stop wake word listener temporarily
        this.wakeRecognition.stop();
        
        // Start command listening after a brief delay
        setTimeout(() => {
            this.startCommandListening();
        }, 600);
    }

    stopAllActivities() {
        console.log('🛑 Stopping all activities for wake word');
        
        // Stop any playing audio/TTS
        if (window.streamingTTS) {
            window.streamingTTS.stopAll();
        }
        
        if (window.currentAudio) {
            window.currentAudio.pause();
            window.currentAudio = null;
        }
        
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        
        // Stop any ongoing voice input
        if (window.currentRecognition) {
            window.currentRecognition.stop();
        }
    }

    // ============================================
    // COMMAND LISTENING (With VAD)
    // ============================================
    startCommandListening() {
        const useLocalSTT = !!window.localSTT;
        const SpeechRecognition = (!useLocalSTT) && (window.SpeechRecognition || window.webkitSpeechRecognition);
        
        if (!useLocalSTT && !SpeechRecognition) {
            console.error('❌ Speech recognition not supported');
            return;
        }

        if (!useLocalSTT) {
            this.commandRecognition = new SpeechRecognition();
            this.commandRecognition.continuous = true;
            this.commandRecognition.interimResults = true;
            this.commandRecognition.lang = window.fridayState?.language || 'en-US';
            this.commandRecognition.maxAlternatives = 5;
        }
        
        this.isListeningForCommand = true;
        this.commandStarted = false;
        this.currentCommand = '';
        this.isSubmitting = false; // Reset submission flag
        
        // Show listening UI
        this.showListeningUI();
        
        console.log('👂 Listening for command...');
        console.log('🔧 VAD Settings:', this.vadSettings);

        if (useLocalSTT) {
            window.localSTT.start((text, isFinal) => {
                if (!text || text.trim().length === 0) return;
                this.commandStarted = true;
                this.currentCommand = text.trim();
                this.updateCommandPreview(this.currentCommand);
                this.resetSilenceTimer();
            });
        } else {
            this.commandRecognition.onresult = (event) => {
                const last = event.results.length - 1;
                const result = event.results[last];
                const transcript = result[0].transcript.trim();
                
                if (transcript.length > 0) {
                    this.commandStarted = true;
                    this.currentCommand = transcript;
                    
                    // Update UI with live transcript
                    this.updateCommandPreview(transcript);
                    
                    // Reset silence timer (user is still speaking)
                    this.resetSilenceTimer();
                    
                    // If final result, start silence detection
                    if (result.isFinal) {
                        console.log('📝 Final transcript:', transcript);
                        this.startSilenceDetection();
                    }
                }
            };
        }

        if (!useLocalSTT) {
            this.commandRecognition.onerror = (event) => {
                console.error('Command recognition error:', event.error);
                
                // If we have a command, submit it before resetting
                if (this.currentCommand.length >= this.vadSettings.minCommandLength) {
                    console.log('📝 Error occurred but we have command, submitting:', this.currentCommand);
                    this.submitCommand();
                } else {
                    console.log('❌ Error and no valid command, resetting');
                    this.resetToWakeWord();
                }
            };
        }

        this.commandRecognition.onend = () => {
            console.log('Command recognition ended');
            
            // CRITICAL FIX: If we have a command and haven't submitted yet, submit it now!
            if (this.isListeningForCommand && this.currentCommand.length >= this.vadSettings.minCommandLength) {
                console.log('⚡ Recognition ended with command, auto-submitting:', this.currentCommand);
                setTimeout(() => {
                    this.submitCommand();
                }, 300);
            } else if (this.isListeningForCommand) {
                console.log('Command recognition ended without valid command, resetting');
                this.resetToWakeWord();
            }
        };

        // Start command recognition
        if (!useLocalSTT) this.commandRecognition.start();
        
        // Safety timeout - auto-submit after max duration
        setTimeout(() => {
            if (this.isListeningForCommand && this.currentCommand.length > 0) {
                console.log('⏱️ Max duration reached, auto-submitting');
                this.submitCommand();
            }
        }, this.vadSettings.maxCommandDuration);
    }

    resetSilenceTimer() {
        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
            this.silenceTimeout = null;
        }
    }

    startSilenceDetection() {
        this.resetSilenceTimer();
        
        // After silence threshold, auto-submit
        this.silenceTimeout = setTimeout(() => {
            if (this.currentCommand.length >= this.vadSettings.minCommandLength) {
                console.log('🔇 Silence detected, auto-submitting command');
                this.submitCommand();
            } else {
                console.log('Command too short, waiting...');
            }
        }, this.vadSettings.silenceThreshold);
    }

    submitCommand() {
        // Prevent duplicate submissions
        if (this.isSubmitting) {
            console.log('⚠️ Already submitting, ignoring duplicate call');
            return;
        }
        
        const command = this.currentCommand.trim();
        
        if (command.length < this.vadSettings.minCommandLength) {
            console.log('❌ Command too short, ignoring');
            this.resetToWakeWord();
            return;
        }
        
        this.isSubmitting = true;
        console.log('✅ Submitting command:', command);
        
        // Clear UI
        this.hideListeningUI();
        
        // Stop command recognition
        if (this.commandRecognition) {
            this.commandRecognition.stop();
        }
        // Stop local STT if active
        if (window.localSTT && typeof window.localSTT.stop === 'function') {
            window.localSTT.stop();
        }
        
        this.isListeningForCommand = false;
        
        // Execute command
        this.executeCommand(command);
        
        // Reset to wake word listening
        setTimeout(() => {
            this.isSubmitting = false;
            this.resetToWakeWord();
        }, 1000);
    }

    async executeCommand(command) {
        const lowerCommand = command.toLowerCase();
        
        // ============================================
        // SPECIAL SYSTEM COMMANDS
        // ============================================
        
        // STOP
        if (lowerCommand.includes('stop') || lowerCommand.includes('रोको') || lowerCommand.includes('रोक') || lowerCommand.includes('बन्द')) {
            this.showCommandFeedback('Stopped', '🛑');
            this.stopAllActivities();
            return;
        }
        
        // SLEEP PC
        if (lowerCommand.includes('sleep') || lowerCommand.includes('सो जाओ') || lowerCommand.includes('निद्रा')) {
            this.showCommandFeedback('Putting PC to sleep...', '😴');
            await this.executeSystemCommand('sleep_pc');
            return;
        }
        
        // LOCK PC
        if (lowerCommand.includes('lock') || lowerCommand.includes('लॉक करो') || lowerCommand.includes('बन्द गर्नुहोस्')) {
            this.showCommandFeedback('Locking PC...', '🔒');
            await this.executeSystemCommand('lock_pc');
            return;
        }
        
        // SHUTDOWN PC
        if (lowerCommand.includes('shutdown') || lowerCommand.includes('shut down') || lowerCommand.includes('बन्द करो') || lowerCommand.includes('बन्द गर')) {
            if (confirm('Shutdown PC in 30 seconds? Click OK to confirm.')) {
                this.showCommandFeedback('Shutting down...', '⚡');
                await this.executeSystemCommand('shutdown_pc');
            }
            return;
        }
        
        // NEW CHAT
        if (lowerCommand.includes('new chat') || lowerCommand.includes('नयाँ च्याट') || lowerCommand.includes('नई चैट')) {
            this.showCommandFeedback('Starting new chat', '🆕');
            if (window.startNewChat) window.startNewChat();
            return;
        }
        
        // REPEAT
        if (lowerCommand.includes('repeat') || lowerCommand.includes('दोहोराउनुहोस्') || lowerCommand.includes('दोहराओ')) {
            this.showCommandFeedback('Repeating...', '🔁');
            const messages = document.querySelectorAll('.message.assistant');
            if (messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                const text = lastMessage.querySelector('.message-text')?.textContent;
                if (text && window.speakText) {
                    window.speakText(text);
                }
            }
            return;
        }
        
        // ============================================
        // SMART ROUTING: Alexa -> System Command -> AI Chat
        // ============================================
        
        // Try Alexa features first (timers, lists, routines)
        let wasAlexaCommand = false;
        if (window.alexaVoiceCommands) {
            wasAlexaCommand = await window.alexaVoiceCommands.processCommand(command);
        }
        
        if (wasAlexaCommand) {
            return; // Alexa handled it
        }
        
        // Try system command (opens apps, files, websites)
        const wasSystemCommand = await this.tryExecuteVoiceCommand(command);
        
        if (!wasSystemCommand) {
            // Send to FRIDAY AI for conversations/complex queries
            console.log('💬 Sending to FRIDAY AI:', command);
            
            if (window.addMessage && window.streamChatResponse) {
                window.addMessage('user', command);
                await window.streamChatResponse(command);
            }
        }
    }
    
    async tryExecuteVoiceCommand(command) {
        /**
         * Try to execute as direct system command (open apps, websites, files, etc.)
         * Returns true if handled, false if should go to AI chat
         */
        
        const commandLower = command.toLowerCase();
        
        // Keywords that indicate system command
        const systemKeywords = [
            'open', 'launch', 'start', 'run',
            'go to', 'visit', 'browse',
            'show me', 'access', 'open up',
            'shutdown', 'restart', 'sleep', 'lock',
            'maximize', 'minimize', 'close',
            'desktop', 'file explorer', 'folder'
        ];
        
        const isSystemCommand = systemKeywords.some(keyword => commandLower.includes(keyword));
        
        if (!isSystemCommand) {
            return false; // Not a system command, let AI chat handle it
        }
        
        try {
            console.log('🎙️ Executing voice command:', command);
            
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_BASE_URL}/api/voice/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: command,
                    language: window.fridayState?.language || 'en-US'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Voice command executed:', result);
                
                // Show success notification with details
                if (window.notificationSystem) {
                    let message = '✅ Done!';
                    
                    if (result.result?.action === 'open_app') {
                        message = `✅ Opened ${result.result.app}`;
                    } else if (result.result?.action === 'open_website') {
                        message = `✅ Opening ${result.result.site}`;
                    } else if (result.result?.action === 'open_browser_website') {
                        message = `✅ Opening ${result.result.website} in ${result.result.browser}`;
                    } else if (result.result?.action === 'chained_commands') {
                        message = `✅ Executed ${result.result.steps} commands`;
                    } else if (result.result?.action === 'open_file') {
                        const type = result.result.type === 'folder' ? 'folder' : 'file';
                        message = `✅ Opened ${type}`;
                    }
                    
                    window.notificationSystem.show(message, 'success', 2500);
                }
                
                return true; // Handled successfully
            } else {
                console.warn('⚠️ Voice command failed, routing to AI chat');
                return false; // Let AI chat try
            }
            
        } catch (error) {
            console.error('❌ Voice command error:', error);
            return false; // Let AI chat try
        }
    }

    async executeSystemCommand(command) {
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            
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

    resetToWakeWord() {
        this.isListeningForCommand = false;
        this.commandStarted = false;
        this.currentCommand = '';
        this.resetSilenceTimer();
        // Stop local STT if active
        if (window.localSTT && typeof window.localSTT.stop === 'function') {
            window.localSTT.stop();
        }
        
        // Restart wake word listening
        if (this.isActive) {
            setTimeout(() => {
                this.wakeRecognition.start();
                console.log('👂 Wake word listener reactivated');
            }, 500);
        }
    }

    // ============================================
    // UI FEEDBACK
    // ============================================
    
    showActivationFeedback() {
        // Flash screen
        const flash = document.createElement('div');
        flash.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle, rgba(0,217,255,0.3) 0%, transparent 70%);
            z-index: 99998;
            pointer-events: none;
            animation: flashPulse 0.5s ease;
        `;
        document.body.appendChild(flash);
        setTimeout(() => flash.remove(), 500);
        
        // Pulse wake button
        const wakeBtn = document.getElementById('wake-word-btn');
        if (wakeBtn) {
            wakeBtn.style.animation = 'none';
            setTimeout(() => {
                wakeBtn.style.animation = 'wakeWordPulse 0.6s ease';
            }, 10);
        }
    }

    playActivationSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Two-tone chime (like Alexa)
            const playTone = (freq, startTime, duration) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = freq;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.15, startTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
                
                oscillator.start(startTime);
                oscillator.stop(startTime + duration);
            };
            
            const now = audioContext.currentTime;
            playTone(800, now, 0.1);
            playTone(1000, now + 0.1, 0.15);
            
        } catch (e) {
            console.log('Audio context not available');
        }
    }

    showListeningUI() {
        // Create listening overlay
        const overlay = document.createElement('div');
        overlay.id = 'friday-listening-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
            color: white;
            padding: 1.5rem 2.5rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 1.2rem;
            z-index: 99999;
            box-shadow: 0 8px 32px rgba(0, 217, 255, 0.6);
            animation: slideDown 0.3s ease;
            display: flex;
            align-items: center;
            gap: 1rem;
        `;
        
        overlay.innerHTML = `
            <div style="width: 12px; height: 12px; background: #ff3366; border-radius: 50%; animation: pulse 1s infinite;"></div>
            <div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Listening...</div>
                <div id="friday-command-preview" style="font-size: 1rem; margin-top: 0.3rem; font-weight: 700;"></div>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }

    hideListeningUI() {
        const overlay = document.getElementById('friday-listening-overlay');
        if (overlay) {
            overlay.style.animation = 'slideUp 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        }
    }

    updateCommandPreview(text) {
        const preview = document.getElementById('friday-command-preview');
        if (preview) {
            preview.textContent = text;
        }
    }

    showCommandFeedback(message, emoji) {
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

    showWakeIndicator(active) {
        const wakeBtn = document.getElementById('wake-word-btn');
        if (wakeBtn) {
            if (active) {
                wakeBtn.classList.add('active');
                wakeBtn.innerHTML = '<i class="fas fa-microphone"></i> Wake Word Active';
            } else {
                wakeBtn.classList.remove('active');
                wakeBtn.innerHTML = '<i class="fas fa-microphone-slash"></i> Wake Word Inactive';
            }
        }
    }

    stop() {
        if (this.wakeRecognition) {
            this.wakeRecognition.stop();
        }
        
        if (this.commandRecognition) {
            this.commandRecognition.stop();
        }
        
        this.isActive = false;
        this.isListeningForCommand = false;
        this.resetSilenceTimer();
        this.hideListeningUI();
        this.showWakeIndicator(false);
        
        console.log('🛑 Wake word system stopped');
    }
}

// Add required animations
const style = document.createElement('style');
style.textContent = `
    @keyframes flashPulse {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    
    @keyframes wakeWordPulse {
        0%, 100% { transform: scale(1); box-shadow: 0 2px 8px rgba(0, 217, 255, 0.3); }
        50% { transform: scale(1.1); box-shadow: 0 4px 20px rgba(0, 217, 255, 0.8); }
    }
    
    @keyframes slideDown {
        from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
    }
    
    @keyframes slideUp {
        from { transform: translateX(-50%) translateY(0); opacity: 1; }
        to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
`;
document.head.appendChild(style);

// Global instance
window.advancedWakeWord = new AdvancedWakeWordSystem();

