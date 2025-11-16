// ============================================
// ENHANCED KEYBOARD SHORTCUTS FOR POWER USERS
// ============================================

class KeyboardShortcutManager {
    constructor() {
        this.shortcuts = {
            // Voice & Wake Word
            'ctrl+space': () => this.toggleVoiceInput(),
            'ctrl+shift+w': () => this.toggleWakeWord(),
            'ctrl+shift+v': () => this.toggleVoiceOutput(),
            'escape': () => this.stopAllAudio(),
            
            // Chat Management
            'ctrl+n': () => this.newChat(),
            'ctrl+shift+r': () => this.repeatLastResponse(),
            'ctrl+/': () => this.showShortcutsHelp(),
            
            // Send Message
            'enter': (e) => this.handleEnter(e),
            'shift+enter': () => this.insertNewLine(),
            
            // Navigation
            'ctrl+1': () => this.focusChat(),
            'ctrl+2': () => this.focusInput(),
            
            // Screenshots & Clipboard
            'ctrl+shift+s': () => this.captureScreen(),
            'ctrl+shift+c': () => this.toggleClipboardMonitor()
        };
        
        this.init();
        console.log('⌨️ Enhanced keyboard shortcuts loaded');
    }

    init() {
        document.addEventListener('keydown', (e) => {
            const key = this.getKeyCombo(e);
            
            if (this.shortcuts[key]) {
                // Special handling for Enter
                if (key === 'enter' || key === 'shift+enter') {
                    this.shortcuts[key](e);
                } else {
                    e.preventDefault();
                    this.shortcuts[key]();
                }
            }
        });
    }

    getKeyCombo(e) {
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.shiftKey) parts.push('shift');
        if (e.altKey) parts.push('alt');
        
        const key = e.key.toLowerCase();
        if (key !== 'control' && key !== 'shift' && key !== 'alt' && key !== 'meta') {
            parts.push(key);
        }
        
        return parts.join('+');
    }

    // ============================================
    // SHORTCUT ACTIONS
    // ============================================

    toggleVoiceInput() {
        if (window.streamingTTS) {
            window.streamingTTS.stopAll();
        }
        
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.click();
        }
        console.log('⌨️ Voice input toggled');
    }

    toggleWakeWord() {
        if (window.toggleWakeWord) {
            window.toggleWakeWord();
        }
        console.log('⌨️ Wake word toggled');
    }

    toggleVoiceOutput() {
        if (window.toggleVoiceOutput) {
            window.toggleVoiceOutput();
        }
        console.log('⌨️ Voice output toggled');
    }

    stopAllAudio() {
        // Stop streaming TTS
        if (window.streamingTTS) {
            window.streamingTTS.stopAll();
        }
        
        // Stop wake word listening
        if (window.advancedWakeWord && window.advancedWakeWord.isListeningForCommand) {
            window.advancedWakeWord.resetToWakeWord();
        }
        
        // Stop regular audio
        if (window.stopSpeaking) {
            window.stopSpeaking();
        }
        
        console.log('⌨️ All audio stopped');
        this.showToast('🛑 Stopped', 'All audio stopped');
    }

    newChat() {
        if (window.startNewChat) {
            window.startNewChat();
        }
        console.log('⌨️ New chat started');
    }

    repeatLastResponse() {
        const messages = document.querySelectorAll('.message.assistant');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            const text = lastMessage.querySelector('.message-text')?.textContent;
            if (text && window.speakText) {
                window.speakText(text);
                this.showToast('🔁 Repeating', 'Last response');
            }
        }
        console.log('⌨️ Repeat last response');
    }

    handleEnter(e) {
        const chatInput = document.getElementById('chat-input');
        
        // If not focused on input, ignore
        if (document.activeElement !== chatInput) {
            return;
        }
        
        // Shift+Enter = new line (handled by browser)
        if (e.shiftKey) {
            return;
        }
        
        // Enter = send message
        e.preventDefault();
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.click();
        }
    }

    insertNewLine() {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            const cursorPos = chatInput.selectionStart;
            const text = chatInput.value;
            chatInput.value = text.substring(0, cursorPos) + '\n' + text.substring(cursorPos);
            chatInput.selectionStart = chatInput.selectionEnd = cursorPos + 1;
        }
    }

    focusChat() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
            chatMessages.focus();
        }
        console.log('⌨️ Focused on chat');
    }

    focusInput() {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.focus();
        }
        console.log('⌨️ Focused on input');
    }

    captureScreen() {
        if (window.captureScreen) {
            window.captureScreen();
        }
        console.log('⌨️ Screenshot captured');
    }

    toggleClipboardMonitor() {
        if (window.toggleClipboardMonitor) {
            window.toggleClipboardMonitor();
        }
        console.log('⌨️ Clipboard monitor toggled');
    }

    showShortcutsHelp() {
        const helpText = `
⌨️ **KEYBOARD SHORTCUTS**

**Voice & Audio:**
• Ctrl+Space - Toggle voice input
• Ctrl+Shift+W - Toggle wake word
• Ctrl+Shift+V - Toggle voice output
• Escape - Stop all audio

**Chat:**
• Ctrl+N - New chat
• Ctrl+Shift+R - Repeat last response
• Enter - Send message
• Shift+Enter - New line

**Navigation:**
• Ctrl+1 - Focus chat
• Ctrl+2 - Focus input

**Tools:**
• Ctrl+Shift+S - Screenshot
• Ctrl+Shift+C - Clipboard monitor
• Ctrl+/ - This help

*Tip: Use Tab to navigate between elements*
        `.trim();
        
        this.showToast('⌨️ Keyboard Shortcuts', helpText, 8000);
    }

    showToast(title, message, duration = 3000) {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            font-size: 0.95rem;
            z-index: 99999;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 217, 255, 0.3);
            animation: slideInRight 0.3s ease;
            max-width: 400px;
            white-space: pre-line;
        `;
        
        toast.innerHTML = `
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">
                ${title}
            </div>
            <div style="opacity: 0.9; font-size: 0.9rem;">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Initialize keyboard shortcuts
window.addEventListener('DOMContentLoaded', () => {
    window.keyboardShortcuts = new KeyboardShortcutManager();
});

