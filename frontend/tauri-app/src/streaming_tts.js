// ============================================
// STREAMING TTS WITH PARALLEL PROCESSING
// ============================================
// Plays audio as fast as possible while text streams in

class StreamingTTSEngine {
    constructor() {
        this.audioQueue = [];
        this.isPlaying = false;
        this.currentAudio = null;
        this.pendingChunks = [];
        this.chunkCounter = 0;
        this.isStopped = false;
        
        console.log('🎵 Streaming TTS Engine initialized');
    }

    /**
     * Add text chunk for TTS processing
     * This is called as text streams in from the backend
     */
    async addChunk(text) {
        if (!text || text.trim() === '' || this.isStopped) return;
        
        // Split into sentences for more natural breaks
        const sentences = this.splitIntoSentences(text);
        
        for (const sentence of sentences) {
            if (sentence.trim().length < 3) continue; // Skip very short chunks
            
            this.chunkCounter++;
            const chunkId = this.chunkCounter;
            
            console.log(`📝 Queuing TTS chunk ${chunkId}:`, sentence.substring(0, 50) + '...');
            
            // Generate TTS in parallel (don't wait)
            this.generateAndQueueAudio(sentence, chunkId);
        }
    }

    /**
     * Split text into sentences for natural TTS
     */
    splitIntoSentences(text) {
        // Split on sentence boundaries
        const sentences = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [text];
        return sentences.map(s => s.trim()).filter(s => s.length > 0);
    }

    /**
     * Generate TTS and add to queue (parallel processing)
     */
    async generateAndQueueAudio(text, chunkId) {
        try {
            const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
            const language = window.fridayState?.language || 'en-US';
            
            console.log(`🎤 Generating TTS for chunk ${chunkId}...`);
            
            const response = await fetch(`${API_BASE_URL}/api/chat/tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    language: language
                })
            });
            
            if (!response.ok) {
                console.warn(`⚠️ TTS failed for chunk ${chunkId}, using fallback`);
                this.useBrowserTTS(text, chunkId);
                return;
            }
            
            const data = await response.json();
            
            if (data.success && data.audio) {
                console.log(`✅ TTS ready for chunk ${chunkId}`);
                
                // Add to queue with chunk ID for ordering
                this.audioQueue.push({
                    id: chunkId,
                    audio: data.audio,
                    text: text
                });
                
                // Sort queue by chunk ID to maintain order
                this.audioQueue.sort((a, b) => a.id - b.id);
                
                // Start playing if not already
                if (!this.isPlaying) {
                    this.playNextInQueue();
                }
            } else {
                this.useBrowserTTS(text, chunkId);
            }
            
        } catch (error) {
            console.error(`❌ TTS error for chunk ${chunkId}:`, error);
            this.useBrowserTTS(text, chunkId);
        }
    }

    /**
     * Fallback to browser TTS if backend fails
     */
    useBrowserTTS(text, chunkId) {
        this.audioQueue.push({
            id: chunkId,
            browserTTS: true,
            text: text
        });
        
        this.audioQueue.sort((a, b) => a.id - b.id);
        
        if (!this.isPlaying) {
            this.playNextInQueue();
        }
    }

    /**
     * Play audio queue in order
     */
    async playNextInQueue() {
        if (this.isStopped) {
            this.clearQueue();
            return;
        }
        
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            this.updateUI(false);
            console.log('✅ All TTS chunks played');
            return;
        }
        
        this.isPlaying = true;
        this.updateUI(true);
        
        const chunk = this.audioQueue.shift();
        console.log(`🔊 Playing chunk ${chunk.id}`);
        
        try {
            if (chunk.browserTTS) {
                await this.playBrowserTTS(chunk.text);
            } else {
                await this.playAudioChunk(chunk.audio);
            }
        } catch (error) {
            console.error('❌ Playback error:', error);
        }
        
        // Play next chunk
        this.playNextInQueue();
    }

    /**
     * Play audio chunk from backend TTS
     */
    playAudioChunk(audioData) {
        return new Promise((resolve, reject) => {
            if (this.isStopped) {
                resolve();
                return;
            }
            
            const audio = new Audio(audioData);
            this.currentAudio = audio;
            window.currentAudio = audio; // Global reference
            
            audio.onended = () => {
                this.currentAudio = null;
                resolve();
            };
            
            audio.onerror = (e) => {
                console.error('Audio playback error:', e);
                this.currentAudio = null;
                reject(e);
            };
            
            audio.play().catch(reject);
        });
    }

    /**
     * Play using browser TTS
     */
    playBrowserTTS(text) {
        return new Promise((resolve) => {
            if (this.isStopped || !window.speechSynthesis) {
                resolve();
                return;
            }
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = window.fridayState?.language || 'en-US';
            utterance.rate = 1.1;
            utterance.pitch = 1.0;
            
            utterance.onend = () => resolve();
            utterance.onerror = () => resolve();
            
            window.speechSynthesis.speak(utterance);
        });
    }

    /**
     * Stop all audio immediately
     */
    stopAll() {
        console.log('🛑 Stopping all TTS');
        
        this.isStopped = true;
        this.isPlaying = false;
        
        // Stop current audio
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        if (window.currentAudio) {
            window.currentAudio.pause();
            window.currentAudio = null;
        }
        
        // Stop browser TTS
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        
        // Clear queue
        this.clearQueue();
        
        this.updateUI(false);
    }

    /**
     * Clear audio queue
     */
    clearQueue() {
        this.audioQueue = [];
        this.pendingChunks = [];
        this.chunkCounter = 0;
    }

    /**
     * Reset for new response
     */
    reset() {
        this.stopAll();
        this.isStopped = false;
        console.log('🔄 TTS engine reset for new response');
    }

    /**
     * Update UI during playback
     */
    updateUI(isSpeaking) {
        const voiceBtn = document.getElementById('voice-output-btn');
        const stopBtn = document.getElementById('stop-speech-btn');
        
        if (isSpeaking) {
            if (voiceBtn) voiceBtn.classList.add('speaking');
            if (stopBtn) stopBtn.style.display = 'block';
        } else {
            if (voiceBtn) voiceBtn.classList.remove('speaking');
            if (stopBtn) stopBtn.style.display = 'none';
        }
    }

    /**
     * Finalize - signal that all text has been received
     */
    finalize() {
        console.log('✅ All text received, finalizing TTS');
        // All chunks have been added, just let them play out
    }
}

// Global instance
window.streamingTTS = new StreamingTTSEngine();

