// ============================================
// MICROPHONE PERMISSION HANDLER
// ============================================

class PermissionHandler {
    constructor() {
        this.micPermissionGranted = false;
        console.log('🎤 Permission handler initialized');
    }

    /**
     * Request microphone permission with user-friendly flow
     */
    async requestMicrophonePermission() {
        try {
            console.log('🎤 Requesting microphone permission...');
            
            // Try to get user media (this triggers permission prompt)
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Permission granted! Stop the stream immediately
            stream.getTracks().forEach(track => track.stop());
            
            this.micPermissionGranted = true;
            console.log('✅ Microphone permission granted');
            
            if (window.notificationSystem) {
                window.notificationSystem.show(
                    '✅ Microphone access granted! You can now use voice features.',
                    'success'
                );
            }
            
            return true;
            
        } catch (error) {
            console.error('❌ Microphone permission denied:', error);
            
            this.micPermissionGranted = false;
            
            // Show helpful instructions
            this.showPermissionInstructions();
            
            return false;
        }
    }

    /**
     * Check if microphone permission is already granted
     */
    async checkMicrophonePermission() {
        try {
            const result = await navigator.permissions.query({ name: 'microphone' });
            
            this.micPermissionGranted = (result.state === 'granted');
            
            console.log(`🎤 Microphone permission: ${result.state}`);
            
            // Listen for permission changes
            result.addEventListener('change', () => {
                this.micPermissionGranted = (result.state === 'granted');
                console.log(`🎤 Microphone permission changed: ${result.state}`);
            });
            
            return this.micPermissionGranted;
            
        } catch (error) {
            // Permissions API not supported, try requesting directly
            console.log('⚠️ Permissions API not supported, will request on first use');
            return null;
        }
    }

    /**
     * Show instructions on how to enable microphone
     */
    showPermissionInstructions() {
        const instructions = `
            <div style="text-align: left; line-height: 1.8;">
                <h3 style="color: var(--jarvis-error); margin-bottom: 1rem;">🎤 Microphone Access Required</h3>
                <p><strong>To use voice features, you need to allow microphone access:</strong></p>
                <ol style="margin: 1rem 0; padding-left: 1.5rem;">
                    <li>Look for the 🎤 icon in your browser's address bar</li>
                    <li>Click on it and select "Allow"</li>
                    <li>Refresh the page (F5 or Ctrl+R)</li>
                    <li>Try the wake word again</li>
                </ol>
                <p style="color: var(--jarvis-text-dim); font-size: 0.9rem; margin-top: 1rem;">
                    <strong>Browser-specific:</strong><br>
                    • Chrome: Click 🎤 icon → Allow<br>
                    • Firefox: Click 🔒 icon → Permissions → Microphone → Allow<br>
                    • Edge: Click 🔒 icon → Permissions for this site → Microphone → Allow
                </p>
            </div>
        `;
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.cssText = 'z-index: 100000;';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h2>🎤 Microphone Permission</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    ${instructions}
                </div>
                <div class="modal-footer">
                    <button class="friday-btn" onclick="window.permissionHandler.requestMicrophonePermission(); this.closest('.modal-overlay').remove();">
                        🎤 Request Permission Again
                    </button>
                    <button class="friday-btn-secondary" onclick="this.closest('.modal-overlay').remove();">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    /**
     * Request permission before enabling wake word
     */
    async requestBeforeWakeWord() {
        const hasPermission = await this.checkMicrophonePermission();
        
        if (hasPermission === false) {
            // Permission explicitly denied
            this.showPermissionInstructions();
            return false;
        }
        
        if (hasPermission === null || hasPermission === true) {
            // Try to enable wake word
            return true;
        }
        
        return false;
    }
}

// Global instance
window.permissionHandler = new PermissionHandler();

// Check permissions on load
window.addEventListener('DOMContentLoaded', () => {
    window.permissionHandler.checkMicrophonePermission();
});

