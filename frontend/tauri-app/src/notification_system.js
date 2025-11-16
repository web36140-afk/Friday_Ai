// ============================================
// ADVANCED NOTIFICATION SYSTEM WITH QUEUE
// ============================================

class NotificationSystem {
    constructor() {
        this.queue = [];
        this.isShowing = false;
        this.currentNotification = null;
        
        console.log('🔔 Notification system initialized');
    }

    /**
     * Show notification with type: success, error, info, warning
     */
    show(message, type = 'info', duration = 3000) {
        this.queue.push({ message, type, duration });
        
        if (!this.isShowing) {
            this.processQueue();
        }
    }

    async processQueue() {
        if (this.queue.length === 0) {
            this.isShowing = false;
            return;
        }
        
        this.isShowing = true;
        const notification = this.queue.shift();
        
        await this.display(notification);
        
        // Process next notification
        setTimeout(() => {
            this.processQueue();
        }, 300);
    }

    display(notification) {
        return new Promise((resolve) => {
            const { message, type, duration } = notification;
            
            // Create notification element
            const notif = document.createElement('div');
            notif.className = `notification notification-${type}`;
            notif.style.cssText = this.getStyles(type);
            
            // Icon based on type
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            
            notif.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="font-size: 1.5rem;">${icons[type]}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${message}</div>
                    </div>
                    <button 
                        onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer; opacity: 0.7; padding: 0 0.5rem;"
                        title="Dismiss"
                    >✕</button>
                </div>
            `;
            
            // Add progress bar
            if (duration > 0) {
                const progressBar = document.createElement('div');
                progressBar.style.cssText = `
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: rgba(255, 255, 255, 0.5);
                    width: 100%;
                    animation: progressShrink ${duration}ms linear;
                `;
                notif.appendChild(progressBar);
            }
            
            document.body.appendChild(notif);
            this.currentNotification = notif;
            
            // Auto-remove
            if (duration > 0) {
                setTimeout(() => {
                    notif.style.animation = 'slideOutRight 0.3s ease';
                    setTimeout(() => {
                        notif.remove();
                        resolve();
                    }, 300);
                }, duration);
            } else {
                resolve();
            }
        });
    }

    getStyles(type) {
        const colors = {
            success: 'linear-gradient(135deg, #00b894 0%, #00cec9 100%)',
            error: 'linear-gradient(135deg, #d63031 0%, #ff7675 100%)',
            warning: 'linear-gradient(135deg, #fdcb6e 0%, #e17055 100%)',
            info: 'linear-gradient(135deg, #0984e3 0%, #74b9ff 100%)'
        };
        
        return `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-size: 0.95rem;
            z-index: 99999;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            animation: slideInRight 0.3s ease;
            min-width: 300px;
            max-width: 400px;
            position: relative;
            overflow: hidden;
        `;
    }

    /**
     * Show loading notification
     */
    showLoading(message) {
        const loadingId = Date.now();
        
        const notif = document.createElement('div');
        notif.id = `loading-${loadingId}`;
        notif.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 1.25rem 1.5rem;
            border-radius: 12px;
            font-size: 0.95rem;
            z-index: 99999;
            box-shadow: 0 8px 32px rgba(0, 217, 255, 0.4);
            animation: slideInRight 0.3s ease;
            border: 1px solid rgba(0, 217, 255, 0.3);
        `;
        
        notif.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div class="loading-spinner" style="
                    width: 20px;
                    height: 20px;
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    border-top-color: #00d9ff;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                "></div>
                <div style="font-weight: 600;">${message}</div>
            </div>
        `;
        
        document.body.appendChild(notif);
        
        return loadingId;
    }

    /**
     * Hide loading notification
     */
    hideLoading(loadingId) {
        const notif = document.getElementById(`loading-${loadingId}`);
        if (notif) {
            notif.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notif.remove(), 300);
        }
    }

    /**
     * Show persistent notification (stays until dismissed)
     */
    showPersistent(message, type = 'info') {
        this.show(message, type, 0);
    }
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes progressShrink {
        from { width: 100%; }
        to { width: 0%; }
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Global instance
window.notificationSystem = new NotificationSystem();

// Override default showNotification to use new system
window.showNotification = (message, type = 'info', duration = 3000) => {
    window.notificationSystem.show(message, type, duration);
};

