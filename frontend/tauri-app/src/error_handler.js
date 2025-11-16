// ============================================
// ADVANCED ERROR HANDLER WITH AUTO-RECONNECTION
// ============================================

class ErrorHandler {
    constructor() {
        this.maxRetries = 3;
        this.retryDelay = 2000;
        this.backendUrl = import.meta.env?.VITE_API_URL || 'http://localhost:8000';
        this.isBackendOnline = true;
        this.reconnectionAttempts = 0;
        
        this.init();
        console.log('🛡️ Error handler initialized');
    }

    init() {
        // Handle global errors
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event);
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handlePromiseRejection(event);
        });

        // Monitor backend health
        this.startHealthCheck();
    }

    // ============================================
    // ERROR HANDLERS
    // ============================================

    handleGlobalError(event) {
        console.error('❌ Global error:', event.error);
        
        // Don't show notification for script loading errors (they're handled elsewhere)
        if (event.message && event.message.includes('script')) {
            return;
        }
        
        // Show user-friendly error
        if (window.notificationSystem) {
            window.notificationSystem.show(
                `An error occurred: ${event.message || 'Unknown error'}`,
                'error'
            );
        }
    }

    handlePromiseRejection(event) {
        console.error('❌ Unhandled promise rejection:', event.reason);
        
        // Check if it's a network error
        if (event.reason && event.reason.message && event.reason.message.includes('fetch')) {
            this.handleNetworkError();
        }
    }

    // ============================================
    // NETWORK ERROR HANDLING
    // ============================================

    handleNetworkError() {
        if (this.isBackendOnline) {
            this.isBackendOnline = false;
            
            if (window.notificationSystem) {
                window.notificationSystem.show(
                    'Backend connection lost. Attempting to reconnect...',
                    'warning',
                    5000
                );
            }
            
            this.attemptReconnection();
        }
    }

    async attemptReconnection() {
        this.reconnectionAttempts++;
        
        console.log(`🔄 Reconnection attempt ${this.reconnectionAttempts}...`);
        
        try {
            const response = await fetch(`${this.backendUrl}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                this.isBackendOnline = true;
                this.reconnectionAttempts = 0;
                
                if (window.notificationSystem) {
                    window.notificationSystem.show(
                        '✅ Backend reconnected successfully!',
                        'success'
                    );
                }
                
                console.log('✅ Backend reconnected');
                return true;
            }
        } catch (error) {
            console.log('❌ Reconnection failed');
        }
        
        // Retry with exponential backoff
        if (this.reconnectionAttempts < this.maxRetries) {
            const delay = this.retryDelay * Math.pow(2, this.reconnectionAttempts - 1);
            setTimeout(() => {
                this.attemptReconnection();
            }, delay);
        } else {
            // Max retries reached
            if (window.notificationSystem) {
                window.notificationSystem.show(
                    'Unable to connect to backend. Please check if the server is running.',
                    'error',
                    0  // Persistent notification
                );
            }
        }
        
        return false;
    }

    // ============================================
    // HEALTH CHECK
    // ============================================

    startHealthCheck() {
        // Check backend health every 30 seconds
        setInterval(async () => {
            try {
                const response = await fetch(`${this.backendUrl}/health`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(3000)
                });
                
                if (!response.ok && this.isBackendOnline) {
                    this.handleNetworkError();
                } else if (response.ok && !this.isBackendOnline) {
                    // Backend came back online
                    this.isBackendOnline = true;
                    this.reconnectionAttempts = 0;
                    
                    if (window.notificationSystem) {
                        window.notificationSystem.show(
                            '✅ Backend connection restored',
                            'success'
                        );
                    }
                }
            } catch (error) {
                if (this.isBackendOnline) {
                    this.handleNetworkError();
                }
            }
        }, 30000);
    }

    // ============================================
    // API CALL WRAPPER WITH RETRY
    // ============================================

    async fetchWithRetry(url, options = {}, retries = 3) {
        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    signal: AbortSignal.timeout(options.timeout || 30000)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return response;
                
            } catch (error) {
                console.log(`Attempt ${i + 1}/${retries} failed:`, error.message);
                
                if (i === retries - 1) {
                    // Last retry failed
                    throw error;
                }
                
                // Wait before retrying (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
            }
        }
    }

    // ============================================
    // SPECIFIC ERROR HANDLERS
    // ============================================

    handleTTSError(error) {
        console.error('TTS Error:', error);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(
                'Voice synthesis failed. Trying alternative...',
                'warning'
            );
        }
    }

    handleStreamingError(error) {
        console.error('Streaming Error:', error);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(
                'Response streaming interrupted. Please try again.',
                'error'
            );
        }
    }

    handleWakeWordError(error) {
        console.error('Wake Word Error:', error);
        
        // Only show notification for critical errors
        if (error.name !== 'no-speech' && error.name !== 'aborted') {
            if (window.notificationSystem) {
                window.notificationSystem.show(
                    'Voice recognition error. Restarting...',
                    'warning'
                );
            }
        }
    }
}

// Global instance
window.errorHandler = new ErrorHandler();

// Export for use in other modules
window.handleError = {
    tts: (error) => window.errorHandler.handleTTSError(error),
    streaming: (error) => window.errorHandler.handleStreamingError(error),
    wakeWord: (error) => window.errorHandler.handleWakeWordError(error),
    network: () => window.errorHandler.handleNetworkError()
};

