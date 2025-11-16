/**
 * ALEXA-LIKE VOICE COMMAND PROCESSOR
 * Handles timers, lists, routines, and smart queries
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class AlexaVoiceCommands {
    constructor() {
        this.activeTimers = [];
        this.timerCheckInterval = null;
        console.log('🎯 Alexa Voice Commands initialized');
    }

    /**
     * Process voice command and route to appropriate Alexa feature
     * Returns true if handled, false if should go to AI chat
     */
    async processCommand(command) {
        const lowerCommand = command.toLowerCase();
        
        // ============================================
        // TIMERS
        // ============================================
        
        // Set timer
        if (lowerCommand.includes('set') && (lowerCommand.includes('timer') || lowerCommand.includes('alarm'))) {
            return await this.handleSetTimer(command);
        }
        
        // Check timers
        if (lowerCommand.includes('timer') && (lowerCommand.includes('how') || lowerCommand.includes('check') || lowerCommand.includes('status'))) {
            return await this.handleCheckTimers();
        }
        
        // Cancel timer
        if ((lowerCommand.includes('cancel') || lowerCommand.includes('stop')) && lowerCommand.includes('timer')) {
            return await this.handleCancelTimer();
        }
        
        // ============================================
        // TO-DO LISTS
        // ============================================
        
        // Add to-do
        if ((lowerCommand.includes('add') || lowerCommand.includes('create')) && (lowerCommand.includes('todo') || lowerCommand.includes('task') || lowerCommand.includes('reminder'))) {
            return await this.handleAddTodo(command);
        }
        
        // Get to-do list
        if ((lowerCommand.includes('what') || lowerCommand.includes('read') || lowerCommand.includes('show')) && (lowerCommand.includes('todo') || lowerCommand.includes('task'))) {
            return await this.handleGetTodos();
        }
        
        // Complete todo
        if ((lowerCommand.includes('complete') || lowerCommand.includes('done') || lowerCommand.includes('finish')) && (lowerCommand.includes('todo') || lowerCommand.includes('task'))) {
            return await this.handleCompleteTodo(command);
        }
        
        // ============================================
        // SHOPPING LIST
        // ============================================
        
        // Add to shopping list
        if ((lowerCommand.includes('add') || lowerCommand.includes('put')) && (lowerCommand.includes('shopping') || lowerCommand.includes('grocery'))) {
            return await this.handleAddShopping(command);
        }
        
        // Get shopping list
        if ((lowerCommand.includes('what') || lowerCommand.includes('read') || lowerCommand.includes('show')) && (lowerCommand.includes('shopping') || lowerCommand.includes('grocery'))) {
            return await this.handleGetShopping();
        }
        
        // ============================================
        // ROUTINES
        // ============================================
        
        // Run routine
        if (lowerCommand.includes('good morning') || (lowerCommand.includes('run') && lowerCommand.includes('morning'))) {
            return await this.handleRunRoutine('morning');
        }
        
        if (lowerCommand.includes('good night') || (lowerCommand.includes('run') && lowerCommand.includes('night'))) {
            return await this.handleRunRoutine('night');
        }
        
        if ((lowerCommand.includes('work mode') || lowerCommand.includes('start work')) && lowerCommand.includes('routine')) {
            return await this.handleRunRoutine('work');
        }
        
        if (lowerCommand.includes('focus mode') || (lowerCommand.includes('focus') && lowerCommand.includes('time'))) {
            return await this.handleRunRoutine('focus');
        }
        
        // ============================================
        // QUICK FACTS
        // ============================================
        
        // Time
        if (lowerCommand.includes('what time') || lowerCommand.includes('current time')) {
            const time = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
            this.speak(`It's ${time}`);
            return true;
        }
        
        // Date
        if (lowerCommand.includes('what date') || lowerCommand.includes('today\'s date') || lowerCommand.includes('what day')) {
            const date = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
            this.speak(`Today is ${date}`);
            return true;
        }
        
        // Weather (if available)
        if (lowerCommand.includes('weather')) {
            // Let AI handle it with weather tool
            return false;
        }
        
        // Not an Alexa command, let AI handle it
        return false;
    }

    // ============================================
    // TIMER HANDLERS
    // ============================================

    async handleSetTimer(command) {
        try {
            // Extract duration from command
            const duration = this.extractDuration(command);
            
            if (!duration) {
                this.speak("I couldn't understand the timer duration. Try saying 'set timer for 5 minutes'");
                return true;
            }

            const response = await fetch(`${API_BASE_URL}/api/alexa/timer/set`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration, name: 'Timer' })
            });

            const result = await response.json();
            
            if (result.success) {
                this.speak(result.message);
                this.showNotification('⏱️ Timer Set', result.message);
                
                // Show visual timer display
                if (window.alexaVisualFeedback) {
                    const endTime = Date.now() / 1000 + duration;
                    window.alexaVisualFeedback.showTimer(result.timer_id, duration, endTime);
                }
                
                this.startTimerChecking();
            } else {
                this.speak("Sorry, I couldn't set the timer");
            }

            return true;
        } catch (error) {
            console.error('Timer error:', error);
            return false;
        }
    }

    async handleCheckTimers() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/alexa/timers`);
            const result = await response.json();

            if (result.count === 0) {
                this.speak("You don't have any active timers");
            } else if (result.count === 1) {
                const timer = result.timers[0];
                this.speak(`You have 1 timer with ${timer.remaining_text} remaining`);
            } else {
                this.speak(`You have ${result.count} active timers`);
            }

            return true;
        } catch (error) {
            console.error('Check timers error:', error);
            return false;
        }
    }

    async handleCancelTimer() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/alexa/timer/cancel`, {
                method: 'POST'
            });

            const result = await response.json();
            this.speak(result.message);
            return true;
        } catch (error) {
            console.error('Cancel timer error:', error);
            return false;
        }
    }

    // ============================================
    // TO-DO LIST HANDLERS
    // ============================================

    async handleAddTodo(command) {
        try {
            // Extract task from command
            const task = this.extractTaskFromCommand(command);
            
            if (!task) {
                this.speak("What would you like to add to your to-do list?");
                return true;
            }

            const response = await fetch(`${API_BASE_URL}/api/alexa/todo/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item: task, list_name: 'default' })
            });

            const result = await response.json();
            
            if (result.success) {
                this.speak(result.message);
                this.showNotification('✅ To-Do Added', task);
            }

            return true;
        } catch (error) {
            console.error('Add todo error:', error);
            return false;
        }
    }

    async handleGetTodos() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/alexa/todos?list_name=default`);
            const result = await response.json();

            if (result.count === 0) {
                this.speak("Your to-do list is empty. Great job!");
            } else {
                const tasks = result.items.map(item => item.text).slice(0, 5); // First 5 tasks
                const message = `You have ${result.count} tasks. ${tasks.join('. ')}`;
                this.speak(message);
                
                // Show visual list
                if (window.alexaVisualFeedback) {
                    window.alexaVisualFeedback.showTodoList(result.items.slice(0, 10)); // Show up to 10
                }
            }

            return true;
        } catch (error) {
            console.error('Get todos error:', error);
            return false;
        }
    }

    async handleCompleteTodo(command) {
        try {
            const task = this.extractTaskFromCommand(command);
            
            const response = await fetch(`${API_BASE_URL}/api/alexa/todo/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_text: task, list_name: 'default' })
            });

            const result = await response.json();
            this.speak(result.message);
            return true;
        } catch (error) {
            console.error('Complete todo error:', error);
            return false;
        }
    }

    // ============================================
    // SHOPPING LIST HANDLERS
    // ============================================

    async handleAddShopping(command) {
        try {
            const item = this.extractShoppingItem(command);
            
            if (!item) {
                this.speak("What would you like to add to your shopping list?");
                return true;
            }

            const response = await fetch(`${API_BASE_URL}/api/alexa/shopping/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item, quantity: '1' })
            });

            const result = await response.json();
            
            if (result.success) {
                this.speak(result.message);
                this.showNotification('🛒 Shopping List', `Added ${item}`);
            }

            return true;
        } catch (error) {
            console.error('Add shopping error:', error);
            return false;
        }
    }

    async handleGetShopping() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/alexa/shopping`);
            const result = await response.json();

            if (result.count === 0) {
                this.speak("Your shopping list is empty");
            } else {
                const items = result.items.map(item => item.item).slice(0, 5);
                const message = `You have ${result.count} items on your shopping list. ${items.join(', ')}`;
                this.speak(message);
                
                // Show visual list
                if (window.alexaVisualFeedback) {
                    window.alexaVisualFeedback.showShoppingList(result.items.slice(0, 10)); // Show up to 10
                }
            }

            return true;
        } catch (error) {
            console.error('Get shopping error:', error);
            return false;
        }
    }

    // ============================================
    // ROUTINE HANDLERS
    // ============================================

    async handleRunRoutine(routineName) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/alexa/routine/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ routine_name: routineName })
            });

            const result = await response.json();
            
            if (result.success) {
                this.speak(`Running ${routineName} routine`);
                this.showNotification('🎯 Routine', `${routineName} routine activated`);
                
                // Execute routine actions
                for (const action of result.results) {
                    if (action.type === 'speak' && action.text) {
                        this.speak(action.text);
                        await this.delay(2000);
                    }
                }
            }

            return true;
        } catch (error) {
            console.error('Run routine error:', error);
            return false;
        }
    }

    // ============================================
    // TIMER MONITORING
    // ============================================

    startTimerChecking() {
        if (this.timerCheckInterval) return;

        this.timerCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/alexa/timers`);
                const result = await response.json();
                
                // Store current timers
                this.activeTimers = result.timers || [];
                
                // Check for expired timers (handled by backend, but we can notify)
                
            } catch (error) {
                console.error('Timer check error:', error);
            }
        }, 5000); // Check every 5 seconds
    }

    // ============================================
    // UTILITIES
    // ============================================

    extractDuration(command) {
        // Extract duration in seconds from command
        const lowerCommand = command.toLowerCase();
        
        // Check for hours
        const hoursMatch = lowerCommand.match(/(\d+)\s*(hour|hr)/);
        if (hoursMatch) {
            return parseInt(hoursMatch[1]) * 3600;
        }
        
        // Check for minutes
        const minutesMatch = lowerCommand.match(/(\d+)\s*(minute|min)/);
        if (minutesMatch) {
            return parseInt(minutesMatch[1]) * 60;
        }
        
        // Check for seconds
        const secondsMatch = lowerCommand.match(/(\d+)\s*(second|sec)/);
        if (secondsMatch) {
            return parseInt(secondsMatch[1]);
        }
        
        return null;
    }

    extractTaskFromCommand(command) {
        // Remove command keywords to get the task
        let task = command
            .toLowerCase()
            .replace(/add|create|to|my|todo|task|list|reminder/gi, '')
            .replace(/complete|done|finish/gi, '')
            .trim();
        
        return task || null;
    }

    extractShoppingItem(command) {
        // Remove command keywords to get the item
        let item = command
            .toLowerCase()
            .replace(/add|put|to|my|shopping|grocery|list/gi, '')
            .trim();
        
        return item || null;
    }

    speak(text) {
        if (window.streamingTTS) {
            window.streamingTTS.stopAll();
            window.streamingTTS.addChunk(text);
            window.streamingTTS.finalize();
        } else if (window.speakText) {
            window.speakText(text);
        }
    }

    showNotification(title, message) {
        if (window.notificationSystem) {
            window.notificationSystem.show(`${title}: ${message}`, 'success', 3000);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global instance
window.alexaVoiceCommands = new AlexaVoiceCommands();

