/**
 * ALEXA-LIKE VISUAL FEEDBACK
 * Echo Show-inspired visual display for timers, lists, and notifications
 */

class AlexaVisualFeedback {
    constructor() {
        this.createStyles();
        this.createContainer();
        console.log('🎨 Alexa Visual Feedback initialized');
    }

    createStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .alexa-display-container {
                position: fixed;
                top: 80px;
                right: 20px;
                width: 320px;
                z-index: 10000;
                pointer-events: none;
            }

            .alexa-card {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid rgba(0, 217, 255, 0.3);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                animation: slideInRight 0.3s ease;
                pointer-events: auto;
                backdrop-filter: blur(10px);
            }

            .alexa-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
            }

            .alexa-card-title {
                font-size: 1rem;
                font-weight: 700;
                color: #00d9ff;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .alexa-card-close {
                background: none;
                border: none;
                color: #888;
                cursor: pointer;
                font-size: 1.2rem;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.2s;
            }

            .alexa-card-close:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
            }

            .alexa-card-content {
                color: #e0e0e0;
                font-size: 0.9rem;
                line-height: 1.6;
            }

            .alexa-timer-display {
                font-size: 2.5rem;
                font-weight: 700;
                color: #00d9ff;
                text-align: center;
                font-family: 'Courier New', monospace;
                margin: 12px 0;
                text-shadow: 0 2px 8px rgba(0, 217, 255, 0.4);
            }

            .alexa-list-item {
                padding: 8px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .alexa-list-item:last-child {
                border-bottom: none;
            }

            .alexa-list-checkbox {
                width: 20px;
                height: 20px;
                border: 2px solid #00d9ff;
                border-radius: 50%;
                flex-shrink: 0;
            }

            .alexa-list-checkbox.checked {
                background: #00d9ff;
                position: relative;
            }

            .alexa-list-checkbox.checked::after {
                content: '✓';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #1a1a2e;
                font-weight: 700;
                font-size: 14px;
            }

            .alexa-list-text {
                flex: 1;
            }

            .alexa-routine-step {
                padding: 10px 12px;
                background: rgba(0, 217, 255, 0.1);
                border-left: 3px solid #00d9ff;
                margin: 8px 0;
                border-radius: 4px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .alexa-routine-step-icon {
                font-size: 1.5rem;
            }

            .alexa-routine-step-text {
                flex: 1;
                font-size: 0.9rem;
            }

            .alexa-progress-bar {
                height: 4px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
                overflow: hidden;
                margin-top: 12px;
            }

            .alexa-progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #00d9ff 0%, #0099cc 100%);
                transition: width 0.3s ease;
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            .alexa-card.closing {
                animation: slideOutRight 0.3s ease forwards;
            }
        `;
        document.head.appendChild(style);
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.className = 'alexa-display-container';
        document.body.appendChild(this.container);
    }

    // ============================================
    // TIMER DISPLAY
    // ============================================

    showTimer(timerId, duration, endTime) {
        const card = this.createCard(timerId, '⏱️ Timer', `
            <div class="alexa-timer-display" id="timer-${timerId}">--:--</div>
            <div class="alexa-progress-bar">
                <div class="alexa-progress-fill" id="timer-progress-${timerId}" style="width: 100%;"></div>
            </div>
        `);

        // Update timer every second
        const interval = setInterval(() => {
            const remaining = Math.max(0, endTime - Date.now() / 1000);
            const minutes = Math.floor(remaining / 60);
            const seconds = Math.floor(remaining % 60);
            
            const display = document.getElementById(`timer-${timerId}`);
            const progress = document.getElementById(`timer-progress-${timerId}`);
            
            if (display) {
                display.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }
            
            if (progress) {
                const percent = (remaining / duration) * 100;
                progress.style.width = `${percent}%`;
            }
            
            if (remaining <= 0) {
                clearInterval(interval);
                this.showTimerFinished(timerId);
            }
        }, 1000);

        // Store interval for cleanup
        card.dataset.interval = interval;
    }

    showTimerFinished(timerId) {
        const card = document.getElementById(`alexa-card-${timerId}`);
        if (card) {
            card.querySelector('.alexa-card-content').innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 3rem;">⏰</div>
                    <div style="font-size: 1.2rem; margin-top: 10px; color: #00d9ff;">Time's Up!</div>
                </div>
            `;
            
            // Play sound
            this.playAlertSound();
            
            // Auto-close after 10 seconds
            setTimeout(() => this.closeCard(timerId), 10000);
        }
    }

    // ============================================
    // TO-DO LIST DISPLAY
    // ============================================

    showTodoList(todos) {
        const listHtml = todos.map(todo => `
            <div class="alexa-list-item">
                <div class="alexa-list-checkbox ${todo.completed ? 'checked' : ''}"></div>
                <div class="alexa-list-text">${todo.text}</div>
            </div>
        `).join('');

        this.createCard('todo-list', '✅ To-Do List', listHtml || '<p style="text-align: center; color: #888;">No tasks!</p>');
    }

    // ============================================
    // SHOPPING LIST DISPLAY
    // ============================================

    showShoppingList(items) {
        const listHtml = items.map(item => `
            <div class="alexa-list-item">
                <div class="alexa-list-checkbox ${item.purchased ? 'checked' : ''}"></div>
                <div class="alexa-list-text">${item.quantity} ${item.item}</div>
            </div>
        `).join('');

        this.createCard('shopping-list', '🛒 Shopping List', listHtml || '<p style="text-align: center; color: #888;">List is empty!</p>');
    }

    // ============================================
    // ROUTINE DISPLAY
    // ============================================

    showRoutine(routineName, steps) {
        const stepsHtml = steps.map((step, index) => `
            <div class="alexa-routine-step" id="routine-step-${index}">
                <div class="alexa-routine-step-icon">${step.icon || '▶️'}</div>
                <div class="alexa-routine-step-text">${step.text}</div>
            </div>
        `).join('');

        this.createCard(`routine-${routineName}`, `🎯 ${routineName} Routine`, stepsHtml);
    }

    // ============================================
    // CARD MANAGEMENT
    // ============================================

    createCard(id, title, content) {
        // Remove existing card with same ID
        this.closeCard(id);

        const card = document.createElement('div');
        card.id = `alexa-card-${id}`;
        card.className = 'alexa-card';
        card.innerHTML = `
            <div class="alexa-card-header">
                <div class="alexa-card-title">${title}</div>
                <button class="alexa-card-close" onclick="window.alexaVisualFeedback.closeCard('${id}')">×</button>
            </div>
            <div class="alexa-card-content">${content}</div>
        `;

        this.container.appendChild(card);
        return card;
    }

    closeCard(id) {
        const card = document.getElementById(`alexa-card-${id}`);
        if (card) {
            // Clear any intervals
            if (card.dataset.interval) {
                clearInterval(parseInt(card.dataset.interval));
            }

            card.classList.add('closing');
            setTimeout(() => card.remove(), 300);
        }
    }

    clearAllCards() {
        this.container.innerHTML = '';
    }

    // ============================================
    // AUDIO FEEDBACK
    // ============================================

    playAlertSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Three-tone alert
            const playTone = (freq, startTime, duration) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = freq;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.2, startTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
                
                oscillator.start(startTime);
                oscillator.stop(startTime + duration);
            };
            
            const now = audioContext.currentTime;
            playTone(800, now, 0.15);
            playTone(1000, now + 0.2, 0.15);
            playTone(800, now + 0.4, 0.15);
        } catch (e) {
            console.log('Audio context not available');
        }
    }
}

// Global instance
window.alexaVisualFeedback = new AlexaVisualFeedback();

