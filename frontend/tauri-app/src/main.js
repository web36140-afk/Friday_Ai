/**
 * JARVIS AI Assistant - Main UI Controller
 * Handles all frontend interactions and API communication
 */

// Backend API Configuration
// Use environment variable if available, otherwise fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// State Management
// ============================================
// V2 ARCHITECTURE - Frontend manages ALL state
// ============================================

// LOAD full conversation from localStorage
const savedConvId = localStorage.getItem('friday_conv_id');
const savedMessages = JSON.parse(localStorage.getItem('friday_messages') || '[]');

const state = {
    // V2: Full conversation state in frontend
    currentConversationId: savedConvId,
    conversationMessages: savedMessages,  // FULL MESSAGE HISTORY
    
    currentProjectId: null,
    provider: 'auto',  // Auto-select based on language
    model: null,  // Auto-select based on provider
    temperature: 0.7,
    language: 'en-US',
    outputLanguage: 'English',
    isStreaming: false,
    conversations: [],
    projects: [],
    conversationAddedToSidebar: false,
    isCurrentlySpeaking: false,
    lastSpokenSentence: null
};

// Save state to localStorage
function saveConversationState() {
    if (state.currentConversationId) {
        localStorage.setItem('friday_conv_id', state.currentConversationId);
    }
    localStorage.setItem('friday_messages', JSON.stringify(state.conversationMessages));
    
    console.log('💾 Saved to localStorage:', state.conversationMessages.length, 'messages');
}

// Log on startup
console.log('🚀 FRIDAY V2 ARCHITECTURE LOADED');
console.log('   Conversation ID:', state.currentConversationId || 'None');
console.log('   Messages restored:', state.conversationMessages.length);

// Language configurations - English, Nepali, Hindi only
const LANGUAGES = {
    'en-US': { name: 'English', code: 'en-US', voice: 'en-US', flag: '🇺🇸' },
    'ne-NP': { name: 'Nepali (नेपाली)', code: 'ne-NP', voice: 'ne-NP', flag: '🇳🇵' },
    'hi-IN': { name: 'Hindi (हिन्दी)', code: 'hi-IN', voice: 'hi-IN', flag: '🇮🇳' }
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 JARVIS initializing...');
    
    // Initialize UI components
    initializeEventListeners();
    loadConversations();
    loadProjects();
    checkBackendStatus();
    startSystemMonitoring();
    
    // Configure marked for markdown rendering
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });
    
    console.log('✅ JARVIS online');
});

// ============================================
// Event Listeners
// ============================================

function initializeEventListeners() {
    // Send message
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    
    sendBtn.addEventListener('click', handleSendMessage);
    
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
    });
    
    // Provider is always Groq (no selection needed)
    
    // New chat button
    const newChatBtn = document.querySelector('.new-chat-btn');
    newChatBtn.addEventListener('click', startNewChat);
    
    // System info button
    const systemInfoBtn = document.querySelector('.system-info-btn');
    const infoPanel = document.getElementById('info-panel');
    const closePanelBtn = document.getElementById('close-panel-btn');
    
    systemInfoBtn.addEventListener('click', () => {
        infoPanel.classList.toggle('hidden');
    });
    
    closePanelBtn.addEventListener('click', () => {
        infoPanel.classList.add('hidden');
    });
    
    // Quick actions
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.getAttribute('data-action');
            handleQuickAction(action);
        });
    });
    
    // Settings button
    const settingsBtn = document.querySelector('.settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettings);
    }
    
    // New project button
    const newProjectBtn = document.querySelector('.new-project-btn');
    if (newProjectBtn) {
        newProjectBtn.addEventListener('click', createNewProject);
    }
    
    // Attach file button
    const attachBtn = document.querySelector('.attach-btn');
    if (attachBtn) {
        attachBtn.addEventListener('click', handleAttachFile);
    }
    
    // Voice input button
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', toggleVoiceInput);
    }
    
    // Voice output toggle
    const voiceOutputBtn = document.getElementById('voice-output-btn');
    if (voiceOutputBtn) {
        voiceOutputBtn.addEventListener('click', toggleVoiceOutput);
    }
    
    // Stop speech button
    const stopSpeechBtn = document.getElementById('stop-speech-btn');
    if (stopSpeechBtn) {
        stopSpeechBtn.addEventListener('click', stopSpeaking);
    }
    
    // Wake word button
    const wakeWordBtn = document.getElementById('wake-word-btn');
    if (wakeWordBtn) {
        wakeWordBtn.addEventListener('click', toggleWakeWord);
    }
    
    // Language selection
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            state.language = e.target.value;
            state.outputLanguage = LANGUAGES[e.target.value].name.split(' ')[0];
            
            // Update voice recognition language
            if (recognition) {
                recognition.lang = state.language;
            }
            
            showNotification(`${LANGUAGES[state.language].flag} Language: ${LANGUAGES[state.language].name} - FRIDAY will respond in this language`, 'success');
            console.log('🌍 Language changed to:', state.language, '|', state.outputLanguage);
            console.log('📢 Next message will be answered in:', state.outputLanguage);
        });
    }
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Initialize context menu
    initializeContextMenu();
    
    // Load saved preferences
    loadUserPreferences();
    
    // Ensure voice output button state is correct
    updateVoiceOutputButton();
    
    // Delete all chats button
    const deleteAllBtn = document.getElementById('delete-all-chats-btn');
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', deleteAllChats);
    }
    
    // Update clipboard monitor button state if enabled
    if (clipboardMonitorEnabled) {
        const clipboardBtn = document.getElementById('clipboard-monitor-btn');
        if (clipboardBtn) {
            clipboardBtn.style.background = 'rgba(0, 217, 255, 0.2)';
            clipboardBtn.style.borderColor = 'var(--jarvis-primary)';
        }
    }
    
    // Mobile menu handling
    initializeMobileMenu();
    
    console.log('🎉 FRIDAY initialized (Female AI Assistant)');
    console.log('🎙️ Voice System: Microsoft Edge Neural TTS (Female voices)');
    console.log('🔊 Voice output:', voiceOutputEnabled ? 'ON' : 'OFF', '| Language:', state.language);
    console.log('📋 All buttons connected and ready!');
    console.log('📱 Mobile support enabled!');
}

function initializeMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.jarvis-sidebar');
    const overlay = document.getElementById('mobile-overlay');
    
    // Show menu toggle on mobile
    function checkMobile() {
        if (window.innerWidth <= 768) {
            menuToggle.style.display = 'block';
        } else {
            menuToggle.style.display = 'none';
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }
    }
    
    // Toggle sidebar
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    });
    
    // Close sidebar when clicking overlay
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    });
    
    // Close sidebar when clicking on a conversation (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && e.target.closest('.conversation-item')) {
            setTimeout(() => {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
            }, 300);
        }
    });
    
    // Check on load and resize
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    // Prevent zoom on double tap (iOS)
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (e) => {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // Add viewport meta if not present
    if (!document.querySelector('meta[name="viewport"]')) {
        const viewport = document.createElement('meta');
        viewport.name = 'viewport';
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        document.head.appendChild(viewport);
    }
}

function initializeContextMenu() {
    // Add context menu for selected text
    document.addEventListener('contextmenu', (e) => {
        const selection = window.getSelection().toString().trim();
        
        if (selection && selection.length > 0) {
            e.preventDefault();
            showContextMenu(e.clientX, e.clientY, selection);
        }
    });
    
    // Close context menu on click elsewhere
    document.addEventListener('click', () => {
        const contextMenu = document.getElementById('context-menu');
        if (contextMenu) {
            contextMenu.remove();
        }
    });
}

function loadUserPreferences() {
    // Load from localStorage
    const savedPrefs = localStorage.getItem('jarvis_preferences');
    if (savedPrefs) {
        try {
            const prefs = JSON.parse(savedPrefs);
            if (prefs.language) {
                state.language = prefs.language;
                state.outputLanguage = prefs.outputLanguage || LANGUAGES[prefs.language].name.split(' ')[0];
                const langSelect = document.getElementById('language-select');
                if (langSelect) {
                    langSelect.value = prefs.language;
                }
            }
            if (prefs.voiceOutputEnabled !== undefined) {
                voiceOutputEnabled = prefs.voiceOutputEnabled;
                updateVoiceOutputButton();
                console.log('🔊 Voice output restored from preferences:', voiceOutputEnabled);
            } else {
                // Default to enabled on first run
                voiceOutputEnabled = true;
                updateVoiceOutputButton();
                console.log('🔊 Voice output defaulted to: ENABLED');
            }
            if (prefs.voiceRate) {
                state.voiceRate = prefs.voiceRate;
            }
            if (prefs.clipboardMonitorEnabled) {
                clipboardMonitorEnabled = prefs.clipboardMonitorEnabled;
                if (clipboardMonitorEnabled) {
                    startClipboardMonitoring();
                    const clipboardBtn = document.getElementById('clipboard-monitor-btn');
                    if (clipboardBtn) {
                        clipboardBtn.style.background = 'rgba(0, 217, 255, 0.2)';
                        clipboardBtn.style.borderColor = 'var(--jarvis-primary)';
                    }
                }
            }
            if (prefs.wakeWordEnabled) {
                wakeWordEnabled = prefs.wakeWordEnabled;
                if (wakeWordEnabled) {
                    const wakeWordBtn = document.getElementById('wake-word-btn');
                    if (wakeWordBtn) {
                        wakeWordBtn.style.background = 'rgba(0, 217, 255, 0.2)';
                        wakeWordBtn.style.borderColor = 'var(--jarvis-primary)';
                        wakeWordBtn.classList.add('active');
                    }
                    // Don't auto-start wake word on load - user can enable manually
                }
            }
            if (prefs.model) {
                state.model = prefs.model;
            }
            if (prefs.temperature) {
                state.temperature = prefs.temperature;
            }
            console.log('✅ Loaded user preferences:', prefs);
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }
}

function saveUserPreferences() {
    const prefs = {
        language: state.language,
        outputLanguage: state.outputLanguage,
        voiceOutputEnabled: voiceOutputEnabled,
        voiceRate: state.voiceRate,
        clipboardMonitorEnabled: clipboardMonitorEnabled,
        wakeWordEnabled: wakeWordEnabled,
        model: state.model,
        temperature: state.temperature
    };
    localStorage.setItem('jarvis_preferences', JSON.stringify(prefs));
    console.log('Saved preferences:', prefs);
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + N: New chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            startNewChat();
        }
        
        // Ctrl/Cmd + K: Focus search (quick action)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('chat-input').focus();
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal-overlay');
            if (modal) {
                modal.remove();
            }
        }
    });
}

// ============================================
// Message Handling
// ============================================

async function handleSendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message || state.isStreaming) return;
    
    // CRITICAL DEBUGGING
    console.log('═══════════════════════════════════════════════════════');
    console.log('🚀 HANDLE SEND MESSAGE CALLED');
    console.log('   Current conversation ID IN STATE:', state.currentConversationId);
    console.log('   Sidebar flag:', state.conversationAddedToSidebar);
    console.log('   Message:', message);
    console.log('═══════════════════════════════════════════════════════');
    
    // STOP any ongoing speech immediately when new message is sent
    console.log('🛑 Stopping any previous speech output...');
    if (window.currentAudio) {
        window.currentAudio.pause();
        window.currentAudio = null;
    }
    if (synthesis && synthesis.speaking) {
        synthesis.cancel();
    }
    
    // Log conversation status
    if (state.currentConversationId) {
        console.log(`✅ CONTINUING EXISTING CONVERSATION: ${state.currentConversationId}`);
        console.log('   → This message will be ADDED to existing conversation');
        console.log('   → Backend will receive conversation_id and ADD to it');
    } else {
        console.log('🆕 NO ACTIVE CONVERSATION - WILL CREATE NEW ONE');
        console.log('   → Backend will receive NULL conversation_id');
        console.log('   → Backend will CREATE new conversation');
    }
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Hide welcome message
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    // Add user message to chat
    addMessage('user', message);
    
    // FINAL CHECK before streaming
    console.log('📤 ABOUT TO CALL streamChatResponse');
    console.log('   state.currentConversationId RIGHT NOW:', state.currentConversationId);
    
    // Start streaming response
    await streamChatResponse(message);
    
    // VERIFY after streaming
    console.log('✅ streamChatResponse COMPLETED');
    console.log('   state.currentConversationId AFTER:', state.currentConversationId);
}

function addMessage(role, content, isStreaming = false) {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'F';  // F for FRIDAY
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    if (isStreaming) {
        textDiv.textContent = '';
        textDiv.dataset.messageId = Date.now();
    } else {
        // Render markdown
        textDiv.innerHTML = marked.parse(content);
        
        // Highlight code blocks and add copy buttons
        textDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
            addCopyButton(block.parentElement);
        });
    }
    
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return textDiv;
}

async function streamChatResponse(message) {
    state.isStreaming = true;
    
    // ============================================
    // RESET STREAMING TTS FOR NEW RESPONSE
    // ============================================
    if (window.streamingTTS) {
        window.streamingTTS.reset();
    }
    
    // V2: Add user message to conversation history
    state.conversationMessages.push({
        role: 'user',
        content: message
    });
    
    // Add assistant message container
    const responseElement = addMessage('assistant', '', true);
    let fullResponse = '';
    let conversationIdFromResponse = null;
    
    try {
        // Prepare language-specific system prompt
        let languagePrompt = null;
        if (state.language === 'hi-IN') {
            // PERFECT Hindi - natural, conversational, grammatically correct  
            languagePrompt = `आप FRIDAY हैं - एक महिला AI सहायक। आपको शुद्ध हिंदी में, प्राकृतिक संवादात्मक शैली में जवाब देना है। अपने बारे में बात करते समय महिला सर्वनाम का प्रयोग करें।

व्याकरण (STRICT):
✓ आप + हैं, करते हैं, कर सकते हैं (सही)
✗ आप + है, करता है (गलत!)
✓ देवनागरी लिपि में लिखें
✗ Roman/English बिल्कुल नहीं

प्राकृतिक शैली:
• स्पष्ट और संक्षिप्त जवाब दें
• प्राकृतिक हिंदी में बात करें
• सही व्याकरण और विराम चिह्नों का प्रयोग करें

जवाब की स्मार्ट लंबाई:
• छोटा सवाल = छोटा जवाब (उदा: "बैंगलोर में CSE?" → "Atria Institute of Technology")
• सामान्य सवाल = संक्षिप्त जवाब (2-3 वाक्य)
• विस्तृत सवाल = विस्तृत जवाब

संदर्भ याद रखें (MEMORY):
• यूज़र की सारी जानकारी याद रखें
• पिछले सवालों का संदर्भ दें

याद रखें: शुद्ध हिंदी, सही व्याकरण, स्मार्ट लंबाई, पूर्ण याददाश्त।`;
            console.log(`🌍 Hindi Mode: Smart concise answers + Full memory`);
        } else if (state.language === 'ne-NP') {
            // PERFECT Nepali - natural, conversational, grammatically correct
            languagePrompt = `तपाईं FRIDAY हुनुहुन्छ - एक महिला AI सहायक। तपाईंले शुद्ध नेपालीमा, प्राकृतिक संवादात्मक शैलीमा जवाफ दिनुपर्छ। आफ्नो बारेमा कुरा गर्दा महिला सर्वनाम को प्रयोग गर्नुहोस्।

व्याकरण (STRICT):
✓ छ, छन्, हुन्छ, हुनुहुन्छ (नेपाली)
✗ है, हैं (हिन्दी - कहिल्यै नगर्नुहोस्!)
✓ तपाईं + हुनुहुन्छ, गर्नुहुन्छ
✗ तपाईं + है, करते हैं
✓ देवनागरी लिपिमा लेख्नुहोस्
✗ Roman/English होइन

नेपाली ≠ हिन्दी (CRITICAL):
नेपाली शब्द: छ, छन्, हुन्छ, हुनुहुन्छ, गर्छ, गर्नुहुन्छ, थियो, हुनेछ
हिन्दी शब्द (FORBIDDEN): है, हैं, करता है, करते हैं, था, होगा

प्राकृतिक शैली:
• स्पष्ट र संक्षिप्त जवाफ दिनुहोस्
• प्राकृतिक नेपालीमा कुरा गर्नुहोस्
• सही व्याकरण र विराम चिन्हको प्रयोग गर्नुहोस्

जवाफको स्मार्ट लम्बाइ:
• छोटो प्रश्न = छोटो जवाफ (उदा: "बैंगलोरमा CSE?" → "Atria Institute of Technology")
• सामान्य प्रश्न = संक्षिप्त जवाफ (2-3 वाक्य)
• विस्तृत प्रश्न = विस्तृत जवाफ

सन्दर्भ सम्झनुहोस् (MEMORY):
• प्रयोगकर्ताको सबै जानकारी सम्झनुहोस्
• अघिल्लो प्रश्नहरूको सन्दर्भ दिनुहोस्

याद राख्नुहोस्: शुद्ध नेपाली, सही व्याकरण, स्मार्ट लम्बाइ, पूर्ण सम्झना।`;
            console.log(`🌍 Nepali Mode: Smart concise answers + Full memory`);
        } else {
            console.log(`🌍 Language mode: English (default)`);
        }
        
        // CRITICAL: Get conversation ID from state OR localStorage
        const conversationIdToSend = state.currentConversationId || localStorage.getItem('active_conversation_id');
        
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('📤 V2: SENDING TO BACKEND');
        console.log('   Conversation ID:', state.currentConversationId || 'will create new');
        console.log('   Total messages to send:', state.conversationMessages.length);
        console.log('   Message history:');
        state.conversationMessages.forEach((msg, i) => {
            console.log(`      ${i+1}. [${msg.role}]: ${msg.content.substring(0, 40)}`);
        });
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        
        // V2: Send FULL conversation history - Backend auto-selects provider
        const response = await fetch(`${API_BASE_URL}/api/chat/v2/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: state.conversationMessages,  // FULL HISTORY
                conversation_id: state.currentConversationId,
                language: state.language,
                temperature: state.temperature
                // provider auto-selected by backend based on language
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Extract conversation_id from headers and MAINTAIN it
        const conversationId = response.headers.get('X-Conversation-ID');
        if (conversationId) {
            conversationIdFromResponse = conversationId;  // Store for later use
            
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('📨 RECEIVED CONVERSATION ID FROM BACKEND:', conversationId);
            console.log('   Current state ID:', state.currentConversationId);
            
            if (!state.currentConversationId) {
                // This is a NEW conversation (first message)
                state.currentConversationId = conversationId;
                
                console.log('✅ V2: NEW CONVERSATION CREATED');
                console.log('   → ID:', conversationId);
                
                // Save state
                saveConversationState();
            } else if (state.currentConversationId === conversationId) {
                // Continuing SAME conversation (subsequent message)
                console.log('✅ CONTINUING SAME CONVERSATION');
                console.log('   → ID matches! Message added to existing conversation');
                console.log('   → NO new sidebar entry will be created');
                console.log('═══════════════════════════════════════════');
            } else {
                // Unexpected - different conversation ID returned
                console.error('❌ CONVERSATION ID MISMATCH!');
                console.error('   State has:', state.currentConversationId);
                console.error('   Backend returned:', conversationId);
                console.error('   → Keeping state ID, NOT updating');
                // DON'T update state - keep existing conversation ID
            }
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'token') {
                        fullResponse += data.content;
                        responseElement.innerHTML = marked.parse(fullResponse);
                        
                        // Highlight code blocks and add copy buttons
                        responseElement.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightElement(block);
                            addCopyButton(block.parentElement);
                        });
                        
                        // ============================================
                        // STREAMING TTS - Play audio as text streams
                        // ============================================
                        if (voiceOutputEnabled && window.streamingTTS && data.content) {
                            // Add chunk to TTS queue (parallel processing)
                            window.streamingTTS.addChunk(data.content);
                        }
                        
                        // Scroll to bottom
                        const chatMessages = document.getElementById('chat-messages');
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                    else if (data.type === 'tool_call') {
                        console.log('Tool called:', data.data);
                        addToolCallIndicator(data.data);
                    }
                    else if (data.type === 'tool_result') {
                        console.log('Tool result:', data.data);
                        // Display tool result indicator (Perplexity-style)
                        if (data.data && data.data.reason) {
                            const toolIndicator = document.createElement('div');
                            toolIndicator.className = 'tool-result-badge';
                            toolIndicator.innerHTML = `
                                <div style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.6rem; background: rgba(0, 217, 255, 0.15); border: 1px solid rgba(0, 217, 255, 0.3); border-radius: 12px; font-size: 0.75rem; margin: 0.3rem 0;">
                                    🔍 ${data.data.reason}
                                </div>
                            `;
                            const chatMessages = document.getElementById('chat-messages');
                            chatMessages.appendChild(toolIndicator);
                        }
                    }
                    else if (data.type === 'followups') {
                        console.log('💡 Follow-up suggestions:', data.data);
                        if (data.data && data.data.suggestions) {
                            displayFollowupSuggestions(data.data.suggestions);
                        }
                    }
                    else if (data.type === 'error') {
                        console.error('Stream error:', data.content);
                        fullResponse += `\n\n❌ Error: ${data.content}`;
                        responseElement.innerHTML = marked.parse(fullResponse);
                    }
                    else if (data.type === 'done') {
                        console.log('Stream complete. Full response length:', fullResponse.length);
                        
                        // V2: Add assistant response to conversation history
                        if (fullResponse) {
                            state.conversationMessages.push({
                                role: 'assistant',
                                content: fullResponse
                            });
                            
                            // Save to localStorage
                            saveConversationState();
                            
                            console.log('✅ V2: Response added to history');
                            console.log('   Total messages:', state.conversationMessages.length);
                        }
                        
                        // ============================================
                        // FINALIZE STREAMING TTS
                        // ============================================
                        if (voiceOutputEnabled && window.streamingTTS) {
                            console.log('✅ Finalizing streaming TTS');
                            window.streamingTTS.finalize();
                        }
                        
                        break;
                    }
                }
            }
        }
        
        // CRITICAL: Conversation sidebar management
        // RULE: Only update sidebar ONCE when conversation is FIRST created
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('🔍 CONVERSATION SIDEBAR CHECK:');
        console.log('   Current conversation ID:', state.currentConversationId);
        console.log('   Response conversation ID:', conversationIdFromResponse);
        console.log('   Already in sidebar:', state.conversationAddedToSidebar);
        console.log('   Conversations in memory:', state.conversations.length);
        
        if (state.currentConversationId && conversationIdFromResponse) {
            // Check if this conversation exists in sidebar
            const existingConv = state.conversations.find(c => c.id === state.currentConversationId);
            console.log('   Found in sidebar:', !!existingConv);
            
            // Only load sidebar ONCE when conversation is first created
            if (!existingConv && !state.conversationAddedToSidebar) {
                // FIRST message in NEW conversation - add to sidebar ONCE
                console.log('   ✅ ACTION: Adding to sidebar (ONCE)');
                state.conversationAddedToSidebar = true;  // Prevent duplicate loading
                
                // Load conversations and auto-generate name
                await loadConversations();
                
                // Auto-generate name WITHOUT reloading conversations again
                console.log('   📝 Auto-generating conversation name...');
                try {
                    const nameResponse = await fetch(`${API_BASE_URL}/api/chat/conversations/${state.currentConversationId}/generate-name`, {
                        method: 'POST'
                    });
                    
                    if (nameResponse.ok) {
                        const nameData = await nameResponse.json();
                        console.log('   ✅ Name generated:', nameData.name);
                        
                        // Update local state WITHOUT reloading
                        const conv = state.conversations.find(c => c.id === state.currentConversationId);
                        if (conv) {
                            conv.name = nameData.name;
                            // Re-render sidebar with updated name (lightweight)
                            renderConversations();
                        }
                    }
                } catch (error) {
                    console.error('   ⚠️ Name generation failed:', error);
                }
            } else {
                // EXISTING conversation OR already added to sidebar - no reload
                console.log('   ✅ ACTION: Skipping sidebar update (already exists)');
            }
        }
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        
    } catch (error) {
        console.error('Error streaming response:', error);
        responseElement.innerHTML = `<span style="color: var(--jarvis-error);">Error: ${error.message}</span>`;
    } finally {
        state.isStreaming = false;
    }
}

function addToolCallIndicator(toolData) {
    const chatMessages = document.getElementById('chat-messages');
    
    const indicator = document.createElement('div');
    indicator.className = 'tool-indicator';
    indicator.innerHTML = `
        <div style="padding: 0.5rem; background: rgba(0, 217, 255, 0.1); border-left: 3px solid var(--jarvis-primary); margin: 0.5rem 0; border-radius: 3px;">
            🔧 Executing: <strong>${toolData.name}</strong>
        </div>
    `;
    
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function displayFollowupSuggestions(suggestions) {
    /**
     * Display ChatGPT-style follow-up question suggestions
     */
    if (!suggestions || suggestions.length === 0) return;
    
    // Remove any existing follow-up container
    const existing = document.querySelector('.followup-suggestions');
    if (existing) {
        existing.remove();
    }
    
    const chatMessages = document.getElementById('chat-messages');
    
    const container = document.createElement('div');
    container.className = 'followup-suggestions';
    container.innerHTML = `
        <div style="margin: 1rem 0; padding: 1rem; background: rgba(0, 217, 255, 0.05); border: 1px solid rgba(0, 217, 255, 0.2); border-radius: 8px;">
            <div style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-bottom: 0.5rem; font-weight: 500;">
                💡 Continue the conversation:
            </div>
            <div class="followup-buttons">
                ${suggestions.map(suggestion => `
                    <button class="followup-btn" onclick="handleFollowupClick('${suggestion.replace(/'/g, "\\'")}')">
                        ${suggestion}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    chatMessages.appendChild(container);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

window.handleFollowupClick = function(suggestion) {
    /**
     * Handle click on follow-up suggestion
     */
    const chatInput = document.getElementById('chat-input');
    chatInput.value = suggestion;
    
    // Remove suggestions after click
    const container = document.querySelector('.followup-suggestions');
    if (container) {
        container.remove();
    }
    
    // Auto-send the message
    setTimeout(() => {
        handleSendMessage();
    }, 300);
};

// ============================================
// Quick Actions
// ============================================

function handleQuickAction(action) {
    const chatInput = document.getElementById('chat-input');
    
    if (action === 'screenshot') {
        captureScreen();
        return;
    }
    
    if (action === 'summarize') {
        if (state.currentConversationId) {
            summarizeConversation(state.currentConversationId);
        } else {
            showNotification('Start a conversation first to summarize', 'info');
        }
        return;
    }
    
    const actionMessages = {
        'analyze': 'Analyze the files in my current directory and provide insights.',
        'search': 'Search the web for the latest developments in AI technology.',
        'monitor': 'Show me my current system status including CPU, RAM, and disk usage.'
    };
    
    chatInput.value = actionMessages[action] || '';
    chatInput.focus();
}

// ============================================
// Conversations & Projects
// ============================================

async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/conversations`);
        const conversations = await response.json();
        
        state.conversations = conversations;
        renderConversations();
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

function renderConversations() {
    const conversationsList = document.getElementById('conversations-list');
    conversationsList.innerHTML = '';
    
    if (state.conversations.length === 0) {
        conversationsList.innerHTML = '<div style="padding: 1rem; color: var(--jarvis-text-dim); text-align: center;">No conversations yet</div>';
        return;
    }
    
    // Sort by updated date (most recent first)
    const sortedConvs = [...state.conversations].sort((a, b) => 
        new Date(b.updated_at) - new Date(a.updated_at)
    );
    
    sortedConvs.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        if (conv.id === state.currentConversationId) {
            item.classList.add('active');
        }
        
        const textSpan = document.createElement('span');
        textSpan.className = 'conversation-text';
        // Show the smart auto-generated name from content
        const displayName = conv.name || 'New Chat';
        textSpan.textContent = displayName;
        textSpan.title = displayName;
        textSpan.addEventListener('click', () => loadConversation(conv.id));
        
        // Double-click to rename
        textSpan.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            renameConversation(conv.id, conv.name || '');
        });
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'conversation-delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete conversation';
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });
        
        item.appendChild(textSpan);
        item.appendChild(deleteBtn);
        conversationsList.appendChild(item);
    });
}

async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/projects/`);
        const projects = await response.json();
        
        state.projects = projects;
        renderProjects();
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

function renderProjects() {
    const projectsList = document.getElementById('projects-list');
    projectsList.innerHTML = '';
    
    if (state.projects.length === 0) {
        projectsList.innerHTML = '<div style="padding: 1rem; color: var(--jarvis-text-dim); text-align: center;">No projects yet</div>';
        return;
    }
    
    state.projects.forEach(project => {
        const item = document.createElement('div');
        item.className = 'project-item';
        item.textContent = project.name;
        item.addEventListener('click', () => loadProject(project.id));
        projectsList.appendChild(item);
    });
}

function startNewChat() {
    // STOP any ongoing speech when starting new chat
    if (window.currentAudio) {
        window.currentAudio.pause();
        window.currentAudio = null;
    }
    if (synthesis && synthesis.speaking) {
        synthesis.cancel();
    }
    
    // V2: Reset EVERYTHING
    const previousConvId = state.currentConversationId;
    state.currentConversationId = null;
    state.conversationMessages = [];  // Clear message history
    state.currentProjectId = null;
    state.conversationAddedToSidebar = false;
    
    // CLEAR localStorage
    localStorage.removeItem('friday_conv_id');
    localStorage.removeItem('friday_messages');
    console.log('🗑️ V2: Cleared all state - fresh start');
    
    console.log('═══════════════════════════════════════════');
    console.log('🆕 STARTING NEW CONVERSATION');
    console.log('   Previous conversation:', previousConvId || 'None');
    console.log('   → Next message will CREATE a new conversation');
    console.log('   → This will add a NEW entry in sidebar');
    console.log('═══════════════════════════════════════════');
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
        <div class="welcome-logo">
            <div class="logo-arc-large"></div>
            <div class="logo-center-large">F</div>
        </div>
        <h2>Hello! I'm FRIDAY.</h2>
        <p>Your intelligent female AI assistant.</p>
        <p class="developer-credit">Developed by Dipesh</p>
            
            <div class="suggestions-container">
                <button class="suggestion-btn" onclick="useSuggestion('What can you help me with?')">
                    <span class="suggestion-icon">❓</span>
                    <span>What can you help me with?</span>
                </button>
                <button class="suggestion-btn" onclick="captureScreen()">
                    <span class="suggestion-icon">📸</span>
                    <span>Take a screenshot and analyze</span>
                </button>
                <button class="suggestion-btn" onclick="useSuggestion('What\\'s my system status?')">
                    <span class="suggestion-icon">💻</span>
                    <span>What's my system status?</span>
                </button>
                <button class="suggestion-btn" onclick="useSuggestion('Search the web for latest AI news')">
                    <span class="suggestion-icon">🔍</span>
                    <span>Search the web</span>
                </button>
            </div>
        </div>
    `;
    
    console.log('Started new chat');
}

async function loadConversation(conversationId) {
    try {
        // STOP any ongoing speech when switching conversations
        if (window.currentAudio) {
            window.currentAudio.pause();
            window.currentAudio = null;
        }
        if (synthesis && synthesis.speaking) {
            synthesis.cancel();
        }
        
        const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}`);
        const conversation = await response.json();
        
        // V2: Set as active and load messages into state
        state.currentConversationId = conversationId;
        state.conversationAddedToSidebar = true;
        
        // Load messages into conversationMessages array
        if (conversation.messages) {
            state.conversationMessages = conversation.messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
        }
        
        // Save to localStorage
        saveConversationState();
        
        console.log('═══════════════════════════════════════════');
        console.log('📂 LOADED EXISTING CONVERSATION');
        console.log('   ID:', conversationId);
        console.log('   Name:', conversation.name || 'Unnamed');
        console.log('   Messages:', conversation.messages.length);
        console.log('   → New messages will be ADDED to this conversation');
        console.log('═══════════════════════════════════════════');
        
        // Clear chat and load all messages
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        
        // Load ALL messages in this conversation
        conversation.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
        });
        
        console.log(`✅ Loaded ${conversation.messages.length} messages from conversation`);
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

async function deleteConversation(conversationId) {
    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete conversation');
        }
        
        // If we're viewing the deleted conversation, start a new chat
        if (state.currentConversationId === conversationId) {
            console.log('🗑️ Deleted current conversation - starting fresh');
            startNewChat();
        }
        
        // Reload conversations list
        await loadConversations();
        
        showNotification('Conversation deleted', 'success');
        console.log('Deleted conversation:', conversationId);
    } catch (error) {
        console.error('Error deleting conversation:', error);
        showNotification('Failed to delete conversation', 'error');
    }
}

async function deleteAllChats() {
    const count = state.conversations.length;
    
    if (count === 0) {
        showNotification('No chats to delete', 'info');
        return;
    }
    
    if (!confirm(`⚠️ Are you sure you want to delete ALL ${count} conversations? This cannot be undone!`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/conversations`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete all conversations');
        }
        
        const result = await response.json();
        
        // V2: Start fresh
        console.log('🗑️ V2: All conversations deleted - fresh start');
        state.currentConversationId = null;
        state.conversationMessages = [];  // Clear messages
        state.conversations = [];
        
        // CLEAR localStorage
        localStorage.removeItem('friday_conv_id');
        localStorage.removeItem('friday_messages');
        
        // Clear UI and start new chat
        startNewChat();
        
        // Reload conversations list (should be empty)
        await loadConversations();
        
        showNotification(`✅ Deleted ${result.count} conversations`, 'success');
        console.log('Deleted all conversations:', result);
    } catch (error) {
        console.error('Error deleting all conversations:', error);
        showNotification('Failed to delete all conversations', 'error');
    }
}

async function renameConversation(conversationId, currentName) {
    const newName = prompt('Enter new conversation name:', currentName);
    
    if (!newName || newName.trim() === '' || newName === currentName) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/name?name=${encodeURIComponent(newName.trim())}`, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            throw new Error('Failed to rename conversation');
        }
        
        // Reload conversations list
        await loadConversations();
        
        showNotification('Conversation renamed', 'success');
        console.log('Renamed conversation:', conversationId, 'to:', newName);
    } catch (error) {
        console.error('Error renaming conversation:', error);
        showNotification('Failed to rename conversation', 'error');
    }
}

async function autoGenerateConversationName(conversationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/generate-name`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            return;
        }
        
        const data = await response.json();
        console.log('✅ Auto-generated smart name from content:', data.name);
        
        // Update local state immediately
        const conv = state.conversations.find(c => c.id === conversationId);
        if (conv) {
            conv.name = data.name;
        }
        
        // Reload conversations to show new name
        await loadConversations();
    } catch (error) {
        console.error('Error auto-generating name:', error);
    }
}

async function loadProject(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}`);
        const project = await response.json();
        
        state.currentProjectId = projectId;
        console.log('Loaded project:', project.name);
        
        // Show notification
        showNotification(`Project loaded: ${project.name}`);
    } catch (error) {
        console.error('Error loading project:', error);
    }
}

// ============================================
// System Monitoring
// ============================================

async function updateSystemStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/system/info`);
        const info = await response.json();
        
        // Update CPU
        const cpuPercent = info.cpu_percent || info.data?.cpu?.usage_percent || 0;
        document.getElementById('cpu-stat').textContent = `${cpuPercent.toFixed(1)}%`;
        document.getElementById('cpu-bar').style.width = `${cpuPercent}%`;
        
        // Update Memory
        const memoryPercent = info.memory_percent || info.data?.memory?.virtual?.percent || 0;
        document.getElementById('memory-stat').textContent = `${memoryPercent.toFixed(1)}%`;
        document.getElementById('memory-bar').style.width = `${memoryPercent}%`;
        
        // Update Disk
        const diskPercent = info.disk_percent || (info.data?.disk?.partitions?.[0]?.percent) || 0;
        document.getElementById('disk-stat').textContent = `${diskPercent.toFixed(1)}%`;
        document.getElementById('disk-bar').style.width = `${diskPercent}%`;
        
        // Update Network
        const networkSent = info.network_sent || (info.data?.network?.total?.sent_mb) || 0;
        const networkRecv = info.network_recv || (info.data?.network?.total?.recv_mb) || 0;
        document.getElementById('network-stat').textContent = `↑ ${networkSent.toFixed(1)} MB / ↓ ${networkRecv.toFixed(1)} MB`;
        
    } catch (error) {
        console.error('Error fetching system stats:', error);
    }
}

function startSystemMonitoring() {
    // Update immediately
    updateSystemStats();
    
    // Update every 5 seconds
    setInterval(updateSystemStats, 5000);
}

// ============================================
// Backend Status Check
// ============================================

async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        console.log('Backend status:', data.status);
        
        // Update status indicator
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (data.status === 'healthy') {
            statusDot.classList.add('online');
            statusText.textContent = 'ONLINE';
        }
    } catch (error) {
        console.error('Backend connection error:', error);
        
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        statusDot.classList.remove('online');
        statusDot.style.background = 'var(--jarvis-error)';
        statusText.textContent = 'OFFLINE';
        statusText.style.color = 'var(--jarvis-error)';
        
        showNotification('Backend server is offline. Please start the backend.', 'error');
    }
}

// ============================================
// Utilities
// ============================================

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = {
        'success': '✓',
        'error': '✗',
        'info': 'ℹ',
        'warning': '⚠'
    }[type] || 'ℹ';
    
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function addCopyButton(preElement) {
    // Check if copy button already exists
    if (preElement.querySelector('.copy-code-btn')) {
        return;
    }
    
    const button = document.createElement('button');
    button.className = 'copy-code-btn';
    button.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4 2a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V2z"/>
            <path d="M2 6a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2v-1H8a3 3 0 01-3-3V6H2z"/>
        </svg>
        <span>Copy</span>
    `;
    button.title = 'Copy code';
    
    button.addEventListener('click', async () => {
        const code = preElement.querySelector('code').textContent;
        
        try {
            await navigator.clipboard.writeText(code);
            button.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/>
                </svg>
                <span>Copied!</span>
            `;
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M4 2a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V2z"/>
                        <path d="M2 6a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2v-1H8a3 3 0 01-3-3V6H2z"/>
                    </svg>
                    <span>Copy</span>
                `;
                button.classList.remove('copied');
            }, 2000);
        } catch (error) {
            console.error('Failed to copy:', error);
            showNotification('Failed to copy code', 'error');
        }
    });
    
    preElement.style.position = 'relative';
    preElement.appendChild(button);
}

function addImageDownloadButton(imgElement, filename) {
    const container = imgElement.parentElement;
    
    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'image-download-btn';
    downloadBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 12l-4-4h3V4h2v4h3l-4 4z"/>
            <path d="M14 14H2v-2h12v2z"/>
        </svg>
        Download
    `;
    downloadBtn.title = `Download ${filename}`;
    
    downloadBtn.addEventListener('click', () => {
        const link = document.createElement('a');
        link.href = imgElement.src;
        link.download = filename || 'image.png';
        link.click();
        showNotification('Image downloaded', 'success');
    });
    
    container.appendChild(downloadBtn);
}

// ============================================
// Settings & Configuration
// ============================================

function openSettings() {
    const settingsHTML = `
        <div class="modal-overlay" id="settings-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>⚙️ Settings</h2>
                    <button class="modal-close" onclick="closeSettings()">×</button>
                </div>
                <div class="modal-body">
                    <div class="settings-section">
                        <h3>Model Selection</h3>
                        <select id="model-select" class="jarvis-select" style="width: 100%; margin-top: 0.5rem;">
                            <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Most Capable)</option>
                            <option value="llama-3.1-8b-instant">Llama 3.1 8B (Fastest)</option>
                            <option value="llama-3.2-90b-text-preview">Llama 3.2 90B (Powerful)</option>
                            <option value="gemma2-9b-it">Gemma 2 9B (Efficient)</option>
                            <option value="mixtral-8x7b-32768">Mixtral 8x7B (Large Context)</option>
                        </select>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Temperature</h3>
                        <input type="range" id="temperature-slider" min="0" max="2" step="0.1" value="0.7" 
                               style="width: 100%; margin-top: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-top: 0.25rem; font-size: 0.85rem; color: var(--jarvis-text-dim);">
                            <span>Precise (0.0)</span>
                            <span id="temperature-value">0.7</span>
                            <span>Creative (2.0)</span>
                        </div>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Voice & Audio</h3>
                        <label style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; cursor: pointer;">
                            <input type="checkbox" id="voice-output-toggle" ${voiceOutputEnabled ? 'checked' : ''}>
                            <span>Enable voice output (FRIDAY speaks)</span>
                        </label>
                        
                        <div style="margin-top: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--jarvis-text-dim); font-size: 0.9rem;">
                                Speech Rate (Naturalness)
                            </label>
                            <input type="range" id="voice-rate-slider" min="0.7" max="1.3" step="0.05" value="${state.voiceRate || languageRates[state.language.split('-')[0]] || 0.95}" style="width: 100%;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--jarvis-text-dim); margin-top: 0.25rem;">
                                <span>Slower</span>
                                <span id="voice-rate-value">${state.voiceRate || languageRates[state.language.split('-')[0]] || 0.95}</span>
                                <span>Faster</span>
                            </div>
                        </div>
                        
                        <button class="friday-btn-secondary" onclick="window.testVoice()" style="width: 100%; margin-top: 1rem;">
                            🔊 Test Voice
                        </button>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Advanced Features</h3>
                        <label style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; cursor: pointer;">
                            <input type="checkbox" id="clipboard-monitor-toggle" ${clipboardMonitorEnabled ? 'checked' : ''}>
                            <span>Enable clipboard monitoring</span>
                        </label>
                        <p style="font-size: 0.85rem; color: var(--jarvis-text-dim); margin-top: 0.25rem; margin-left: 2rem;">
                            Automatically detect and offer to analyze copied text
                        </p>
                    </div>
                    
                    <div class="settings-section">
                        <h3>Keyboard Shortcuts</h3>
                        <div style="color: var(--jarvis-text-dim); font-size: 0.9rem; line-height: 1.8;">
                            <div><kbd>Ctrl+N</kbd> New chat</div>
                            <div><kbd>Ctrl+K</kbd> Focus input</div>
                            <div><kbd>Esc</kbd> Close modals</div>
                            <div><kbd>Enter</kbd> Send message</div>
                            <div><kbd>Shift+Enter</kbd> New line</div>
                        </div>
                    </div>
                    
                    <div class="settings-section">
                        <h3>About</h3>
                        <p style="color: var(--jarvis-text-dim); line-height: 1.6;">
                            <strong style="color: var(--jarvis-primary);">FRIDAY</strong> - Female Replacement Intelligent Digital Assistant Youth<br>
                            Version 2.0.0 • Female AI Assistant<br>
                            <strong style="color: var(--jarvis-primary);">Developed by Dipesh</strong><br>
                            Powered by Groq AI & Google Gemini
                        </p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="friday-btn" onclick="window.saveSettings()">Save Settings</button>
                    <button class="friday-btn-secondary" onclick="window.closeSettings()">Cancel</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', settingsHTML);
    
    // Set current model if exists
    const modelSelect = document.getElementById('model-select');
    if (state.model) {
        modelSelect.value = state.model;
    }
    
    // Temperature slider update
    const tempSlider = document.getElementById('temperature-slider');
    const tempValue = document.getElementById('temperature-value');
    tempSlider.addEventListener('input', (e) => {
        tempValue.textContent = e.target.value;
    });
    
    // Voice rate slider update
    const voiceRateSlider = document.getElementById('voice-rate-slider');
    const voiceRateValue = document.getElementById('voice-rate-value');
    if (voiceRateSlider && voiceRateValue) {
        voiceRateSlider.addEventListener('input', (e) => {
            voiceRateValue.textContent = e.target.value;
        });
    }
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.remove();
    }
}

function saveSettings() {
    const modelSelect = document.getElementById('model-select');
    const tempSlider = document.getElementById('temperature-slider');
    const voiceOutputToggle = document.getElementById('voice-output-toggle');
    const clipboardMonitorToggle = document.getElementById('clipboard-monitor-toggle');
    const voiceRateSlider = document.getElementById('voice-rate-slider');
    
    state.model = modelSelect.value;
    state.temperature = parseFloat(tempSlider.value);
    
    // Save voice rate if available
    if (voiceRateSlider) {
        state.voiceRate = parseFloat(voiceRateSlider.value);
        console.log(`🎤 Voice rate updated to: ${state.voiceRate}`);
    }
    
    // Update voice output
    const newVoiceState = voiceOutputToggle.checked;
    if (newVoiceState !== voiceOutputEnabled) {
        voiceOutputEnabled = newVoiceState;
        const voiceBtn = document.getElementById('voice-output-btn');
        if (voiceOutputEnabled) {
            voiceBtn.style.background = 'rgba(0, 217, 255, 0.2)';
            voiceBtn.style.borderColor = 'var(--jarvis-primary)';
        } else {
            voiceBtn.style.background = '';
            voiceBtn.style.borderColor = '';
            synthesis.cancel();
        }
    }
    
    // Update clipboard monitoring
    const newClipboardState = clipboardMonitorToggle.checked;
    if (newClipboardState !== clipboardMonitorEnabled) {
        clipboardMonitorEnabled = newClipboardState;
        const clipboardBtn = document.getElementById('clipboard-monitor-btn');
        if (clipboardMonitorEnabled) {
            clipboardBtn.style.background = 'rgba(0, 217, 255, 0.2)';
            clipboardBtn.style.borderColor = 'var(--jarvis-primary)';
            startClipboardMonitoring();
        } else {
            clipboardBtn.style.background = '';
            clipboardBtn.style.borderColor = '';
        }
    }
    
    // Save preferences to localStorage
    saveUserPreferences();
    
    showNotification(`✅ Settings saved! Speech rate: ${state.voiceRate ? state.voiceRate.toFixed(2) : 'default'}`, 'success');
    console.log('Settings saved:', { 
        model: state.model, 
        temperature: state.temperature,
        voiceOutput: voiceOutputEnabled,
        voiceRate: state.voiceRate,
        clipboardMonitor: clipboardMonitorEnabled,
        language: state.language
    });
    
    closeSettings();
}

// ============================================
// Project Management
// ============================================

function createNewProject() {
    const projectName = prompt('Enter project name:');
    
    if (!projectName || !projectName.trim()) {
        return;
    }
    
    fetch(`${API_BASE_URL}/api/projects/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: projectName.trim(),
            description: ''
        })
    })
    .then(response => response.json())
    .then(project => {
        state.currentProjectId = project.id;
        loadProjects();
        showNotification(`Project created: ${project.name}`, 'success');
        console.log('Project created:', project);
    })
    .catch(error => {
        console.error('Error creating project:', error);
        showNotification('Failed to create project', 'error');
    });
}

// ============================================
// File Attachment & Upload
// ============================================

function handleAttachFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,.md,.py,.js,.json,.csv,.html,.css,.pdf,.docx,.doc,.png,.jpg,.jpeg,.gif,.bmp,.webp';
    
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        try {
            const fileExt = file.name.split('.').pop().toLowerCase();
            const isDocument = ['pdf', 'docx', 'doc'].includes(fileExt);
            const isImage = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(fileExt);
            const isText = ['txt', 'md', 'py', 'js', 'json', 'csv', 'html', 'css'].includes(fileExt);
            
            // Show uploading notification
            showNotification(`Uploading ${file.name}...`, 'info');
            
            // Upload to backend
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            const chatInput = document.getElementById('chat-input');
            
            // Handle different file types
            if (isImage) {
                // For images, show inline
                const imageData = result.processed_data?.data?.base64 || '';
                const prompt = `I've uploaded an image: ${file.name}\n\n`;
                chatInput.value = prompt;
                
                // Add image preview to chat
                if (imageData) {
                    addImagePreview(imageData, file.name);
                }
            } else if (isDocument) {
                // For PDFs and Word docs, include extracted text
                const content = result.processed_data?.data?.content || '';
                const truncated = content.length > 2000 ? content.substring(0, 2000) + '...' : content;
                const prompt = `I've uploaded a ${fileExt.toUpperCase()} document: ${file.name}\n\nExtracted content:\n\`\`\`\n${truncated}\n\`\`\`\n\nPlease analyze this document.`;
                chatInput.value = prompt;
            } else if (isText) {
                // For text files, include full content
                const content = result.processed_data?.data?.content || '';
                const prompt = `I've uploaded a file: ${file.name}\n\nContent:\n\`\`\`\n${content}\n\`\`\`\n\nPlease analyze this file.`;
                chatInput.value = prompt;
            }
            
            showNotification(`File processed: ${file.name}`, 'success');
            console.log('File upload result:', result);
            
        } catch (error) {
            console.error('Error uploading file:', error);
            showNotification(`Failed to upload file: ${error.message}`, 'error');
        }
    };
    
    input.click();
}

function addImagePreview(base64Data, filename) {
    const chatMessages = document.getElementById('chat-messages');
    
    const previewDiv = document.createElement('div');
    previewDiv.className = 'image-preview';
    previewDiv.innerHTML = `
        <div class="image-container" style="margin: 1rem 0; padding: 1rem; background: rgba(0, 217, 255, 0.05); border: 1px solid var(--jarvis-border); border-radius: 8px; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <p style="color: var(--jarvis-primary); margin: 0; font-size: 0.9rem;">📷 ${filename}</p>
                <button class="image-download-btn" onclick="downloadImage('${base64Data}', '${filename}')" title="Download image">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 12l-4-4h3V4h2v4h3l-4 4z"/>
                        <path d="M14 14H2v-2h12v2z"/>
                    </svg>
                    Download
                </button>
            </div>
            <img src="${base64Data}" style="max-width: 100%; max-height: 400px; border-radius: 5px; border: 1px solid var(--jarvis-border); cursor: zoom-in;" alt="${filename}" onclick="openImageModal(this.src, '${filename}')">
        </div>
    `;
    
    chatMessages.appendChild(previewDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function downloadImage(base64Data, filename) {
    const link = document.createElement('a');
    link.href = base64Data;
    link.download = filename || 'image.png';
    link.click();
    showNotification('Image downloaded', 'success');
}

function openImageModal(src, filename) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <div class="modal-header">
                <h3>${filename}</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="image-modal-body">
                <img src="${src}" style="max-width: 90vw; max-height: 80vh; object-fit: contain;" alt="${filename}">
            </div>
            <div class="modal-footer">
                <button class="jarvis-btn" onclick="downloadImage('${src}', '${filename}')">Download</button>
                <button class="jarvis-btn-secondary" onclick="this.closest('.modal-overlay').remove()">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// ============================================
// Voice Input/Output & Wake Word
// ============================================

let recognition = null;
let wakeWordRecognition = null;
let wakeWordEnabled = false;
let synthesis = window.speechSynthesis;
let voiceOutputEnabled = true;
let availableVoices = [];
let voicesLoaded = false;
let currentUtterance = null; // Track current speech

// Language-specific speech rates for natural pronunciation
const languageRates = {
    'en': 1.0,   // English - natural pace
    'ne': 0.85,  // Nepali - slower for clarity
    'hi': 0.85   // Hindi - slower for clarity
};

// Enhanced voice loading with multiple attempts
function loadVoices() {
    availableVoices = synthesis.getVoices();
    if (availableVoices.length > 0) {
        voicesLoaded = true;
        console.log(`✅ Loaded ${availableVoices.length} voices`);
        
        // Log available languages with counts
        const languageGroups = {};
        availableVoices.forEach(v => {
            const lang = v.lang.split('-')[0];
            languageGroups[lang] = (languageGroups[lang] || 0) + 1;
        });
        console.log('Available languages:', Object.entries(languageGroups).map(([lang, count]) => `${lang}(${count})`).join(', '));
        
        // Log quality voices
        const qualityVoices = availableVoices.filter(v => 
            v.name.toLowerCase().includes('natural') || 
            v.name.toLowerCase().includes('neural') ||
            v.name.toLowerCase().includes('premium')
        );
        if (qualityVoices.length > 0) {
            console.log(`🎙️ High-quality voices available: ${qualityVoices.length}`);
        }
    }
    return availableVoices;
}

// Load voices with retry mechanism
function ensureVoicesLoaded() {
    return new Promise((resolve) => {
        const voices = synthesis.getVoices();
        if (voices.length > 0) {
            availableVoices = voices;
            voicesLoaded = true;
            resolve(voices);
        } else {
            synthesis.onvoiceschanged = () => {
                availableVoices = synthesis.getVoices();
                voicesLoaded = true;
                resolve(availableVoices);
            };
            // Fallback timeout
            setTimeout(() => {
                if (!voicesLoaded) {
                    availableVoices = synthesis.getVoices();
                    voicesLoaded = availableVoices.length > 0;
                    resolve(availableVoices);
                }
            }, 2000);
        }
    });
}

// Load voices on initialization
synthesis.onvoiceschanged = loadVoices;

// Multiple load attempts at different intervals
setTimeout(loadVoices, 100);
setTimeout(loadVoices, 500);
setTimeout(loadVoices, 1000);
setTimeout(loadVoices, 2000);

function getBestVoiceForLanguage(languageCode) {
    // Refresh voices if empty
    if (availableVoices.length === 0) {
        availableVoices = synthesis.getVoices();
    }
    
    const langCode = languageCode.split('-')[0]; // e.g., 'en' from 'en-US'
    
    // Score voices based on quality indicators
    const scoreVoice = (voice) => {
        let score = 0;
        
        // Exact language match (highest priority)
        if (voice.lang === languageCode) score += 100;
        // Language family match
        else if (voice.lang.startsWith(langCode)) score += 50;
        
        // Prefer local/native voices (better quality)
        if (voice.localService) score += 30;
        
        // Prefer natural sounding voices
        if (voice.name.toLowerCase().includes('natural')) score += 20;
        if (voice.name.toLowerCase().includes('neural')) score += 20;
        if (voice.name.toLowerCase().includes('premium')) score += 15;
        if (voice.name.toLowerCase().includes('enhanced')) score += 15;
        
        // Specific high-quality voice names
        if (voice.name.includes('Google')) score += 10;
        if (voice.name.includes('Microsoft')) score += 8;
        
        // Gender preference (neutral/female tend to be clearer)
        if (voice.name.toLowerCase().includes('female')) score += 5;
        
        return score;
    };
    
    // Find all voices for this language and score them
    const matchingVoices = availableVoices
        .filter(voice => voice.lang.startsWith(langCode))
        .map(voice => ({ voice, score: scoreVoice(voice) }))
        .sort((a, b) => b.score - a.score);
    
    if (matchingVoices.length > 0) {
        console.log(`📊 Best voice for ${languageCode}:`, matchingVoices[0].voice.name, `(Score: ${matchingVoices[0].score})`);
        return matchingVoices[0].voice;
    }
    
    // Fallback: return first available voice
    return availableVoices[0] || null;
}

function toggleVoiceInput() {
    const voiceBtn = document.getElementById('voice-btn');
    
    if (!recognition) {
        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            showNotification('Speech recognition not supported in this browser', 'error');
            return;
        }
        
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = state.language;
        
        recognition.onstart = () => {
            voiceBtn.classList.add('listening');
            voiceBtn.style.background = 'rgba(255, 51, 102, 0.2)';
            voiceBtn.style.borderColor = 'var(--jarvis-error)';
            showNotification('Listening...', 'info');
        };
        
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            
            document.getElementById('chat-input').value = transcript;
        };
        
        recognition.onend = () => {
            voiceBtn.classList.remove('listening');
            voiceBtn.style.background = '';
            voiceBtn.style.borderColor = '';
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            voiceBtn.classList.remove('listening');
            voiceBtn.style.background = '';
            voiceBtn.style.borderColor = '';
            
            // User-friendly error messages
            if (event.error === 'not-allowed') {
                showNotification('❌ Microphone access denied! Please allow microphone permissions in your browser settings.', 'error', 5000);
            } else if (event.error === 'no-speech') {
                showNotification('No speech detected. Try again!', 'warning');
            } else if (event.error !== 'aborted') {
                showNotification(`Voice error: ${event.error}`, 'error');
            }
        };
    }
    
    // Toggle recognition
    if (voiceBtn.classList.contains('listening')) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function toggleVoiceOutput() {
    const voiceOutputBtn = document.getElementById('voice-output-btn');
    voiceOutputEnabled = !voiceOutputEnabled;
    
    if (voiceOutputEnabled) {
        // Add active class for visual feedback
        voiceOutputBtn.classList.add('active');
        voiceOutputBtn.title = '🔊 Voice Output: ON (Click to disable)';
        showNotification('✅ Voice output ON - FRIDAY will speak responses', 'success');
        
        // Test voice immediately
        const testMsg = 'Voice output is now enabled.';
        speakText(testMsg);
    } else {
        // Remove active class
        voiceOutputBtn.classList.remove('active');
        voiceOutputBtn.title = '🔇 Voice Output: OFF (Click to enable)';
        synthesis.cancel();
        showNotification('🔇 Voice output OFF', 'info');
    }
    
    console.log('Voice output is now:', voiceOutputEnabled ? 'ENABLED' : 'DISABLED');
    
    // Save preference
    saveUserPreferences();
}

function toggleWakeWord() {
    /**
     * Enable/disable ADVANCED wake word detection (Alexa/Siri level)
     * When enabled, saying "FRIDAY" activates voice listening with VAD
     */
    wakeWordEnabled = !wakeWordEnabled;
    const wakeWordBtn = document.getElementById('wake-word-btn');
    
    if (wakeWordEnabled) {
        // Add active class for visual feedback
        wakeWordBtn.classList.add('active');
        wakeWordBtn.title = '🎤 Wake Word: ACTIVE (Say "Hey FRIDAY")';
        
        // ============================================
        // USE ADVANCED WAKE WORD SYSTEM
        // ============================================
        if (window.advancedWakeWord) {
            window.advancedWakeWord.start();
            showNotification('🎤 Wake word ON - Say "Hey FRIDAY" to activate (with VAD)', 'success');
            console.log('✅ Advanced wake word detection started (Alexa/Siri level)');
        } else {
            // Fallback to old system if advanced not loaded
            startWakeWordDetection();
            showNotification('🎤 Wake word ON - Say "FRIDAY" to activate', 'success');
            console.log('✅ Wake word detection started');
        }
    } else {
        // Remove active class
        wakeWordBtn.classList.remove('active');
        wakeWordBtn.title = '🎤 Wake Word: OFF (Click to enable)';
        
        // Stop advanced or old system
        if (window.advancedWakeWord) {
            window.advancedWakeWord.stop();
        } else {
            stopWakeWordDetection();
        }
        
        showNotification('🎤 Wake word OFF', 'info');
        console.log('⏸️ Wake word detection stopped');
    }
    
    saveUserPreferences();
}

function startWakeWordDetection() {
    /**
     * Continuously listen for the wake word "FRIDAY"
     * When detected, activate voice input
     */
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        showNotification('Speech recognition not supported', 'error');
        wakeWordEnabled = false;
        return;
    }
    
    if (!wakeWordRecognition) {
        wakeWordRecognition = new SpeechRecognition();
        wakeWordRecognition.continuous = true;
        wakeWordRecognition.interimResults = false;
        wakeWordRecognition.lang = state.language;
        
        wakeWordRecognition.onresult = (event) => {
            const last = event.results.length - 1;
            const text = event.results[last][0].transcript.toLowerCase();
            
            console.log('🎤 Heard:', text);
            
            // Check for wake word in different languages
            const wakeWords = ['friday', 'फ्राइडे', 'फ्राइडे'];
            const detected = wakeWords.some(word => text.includes(word));
            
            if (detected) {
                console.log('🔔 WAKE WORD DETECTED! Activating voice input...');
                
                // IMMEDIATELY stop any ongoing speech (interrupt FRIDAY)
                const wasSpeaking = window.currentAudio !== null || (synthesis && synthesis.speaking);
                
                if (wasSpeaking) {
                    console.log('🛑 INTERRUPTING FRIDAY - Stopping current speech for new command');
                }
                
                if (window.currentAudio) {
                    window.currentAudio.pause();
                    window.currentAudio = null;
                }
                if (synthesis && synthesis.speaking) {
                    synthesis.cancel();
                }
                
                // Remove speaking indicator
                const voiceBtn = document.getElementById('voice-output-btn');
                if (voiceBtn) {
                    voiceBtn.classList.remove('speaking');
                }
                
                // Hide stop speech button
                const stopBtn = document.getElementById('stop-speech-btn');
                if (stopBtn) {
                    stopBtn.style.display = 'none';
                }
                
                // Visual feedback
                const wakeWordBtn = document.getElementById('wake-word-btn');
                wakeWordBtn.style.animation = 'pulse 0.5s ease-in-out 3';
                
                // Play activation sound
                playActivationSound();
                
                // Stop wake word detection temporarily
                wakeWordRecognition.stop();
                
                // Start listening for NEW command
                setTimeout(() => {
                    startVoiceCommand();
                }, 500);
            }
        };
        
        wakeWordRecognition.onerror = (event) => {
            if (event.error !== 'no-speech' && event.error !== 'aborted') {
                console.error('Wake word error:', event.error);
            }
            // Restart if it stops
            if (wakeWordEnabled && event.error !== 'aborted') {
                setTimeout(() => {
                    if (wakeWordEnabled) wakeWordRecognition.start();
                }, 1000);
            }
        };
        
        wakeWordRecognition.onend = () => {
            // Auto-restart if still enabled
            if (wakeWordEnabled) {
                setTimeout(() => {
                    wakeWordRecognition.start();
                }, 100);
            }
        };
    }
    
    wakeWordRecognition.start();
    console.log('👂 Listening for wake word "FRIDAY"...');
}

function stopWakeWordDetection() {
    if (wakeWordRecognition) {
        wakeWordRecognition.stop();
        wakeWordRecognition = null;
    }
}

function startVoiceCommand() {
    /**
     * After wake word detected, listen for the actual command
     * If FRIDAY was speaking, she's been interrupted and will now listen
     * ALL ACTIONS can be done via wake word!
     */
    
    // ============================================
    // STOP ALL AUDIO/TTS WHEN VOICE COMMAND STARTS
    // ============================================
    console.log('🎤 Voice command starting - stopping all audio');
    
    // Stop streaming TTS
    if (window.streamingTTS) {
        window.streamingTTS.stopAll();
    }
    
    // Stop any ongoing speech
    if (window.currentUtterance) {
        window.speechSynthesis.cancel();
        window.currentUtterance = null;
    }
    
    if (window.currentAudio) {
        window.currentAudio.pause();
        window.currentAudio = null;
    }
    
    // Stop browser TTS
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const commandRecognition = new SpeechRecognition();
    
    commandRecognition.continuous = false;
    commandRecognition.interimResults = true;
    commandRecognition.lang = state.language;
    commandRecognition.maxAlternatives = 1;
    
    const voiceBtn = document.getElementById('voice-btn');
    const processingIndicator = document.getElementById('processing-indicator');
    
    if (voiceBtn) {
        voiceBtn.classList.add('listening');
        voiceBtn.style.background = 'rgba(0, 217, 255, 0.3)';
        voiceBtn.style.borderColor = 'var(--jarvis-primary)';
    }
    
    // Show processing indicator
    if (processingIndicator) {
        processingIndicator.style.display = 'flex';
    }
    
    // Show listening notification with language-specific message
    const listeningMessages = {
        'en-US': '🎤 I\'m listening... What can I help with?',
        'hi-IN': '🎤 मैं सुन रही हूं... कैसे मदद करूं?',
        'ne-NP': '🎤 म सुन्दैछु... कसरी मद्दत गर्न सक्छु?'
    };
    showNotification(listeningMessages[state.language] || listeningMessages['en-US'], 'info');
    
    commandRecognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');
        
        document.getElementById('chat-input').value = transcript;
        
        // If final result, check for special commands or send message
        if (event.results[event.results.length - 1].isFinal) {
            console.log('✅ Command received via wake word:', transcript);
            
            // Handle special control commands (immediate actions)
            const lowerTranscript = transcript.toLowerCase().trim();
            
            // STOP/PAUSE commands - stop speech immediately
            if (lowerTranscript.match(/^(stop|pause|quiet|silence|shut up|be quiet|cancel)/i)) {
                console.log('🛑 STOP command detected - stopping speech');
                stopSpeaking();
                showNotification('🛑 Stopped', 'info');
                document.getElementById('chat-input').value = '';
                return;
            }
            
            // NEW CHAT command
            if (lowerTranscript.match(/^(new chat|start new|clear chat|reset)/i)) {
                console.log('🆕 NEW CHAT command detected');
                startNewChat();
                showNotification('🆕 Started new chat', 'success');
                document.getElementById('chat-input').value = '';
                return;
            }
            
            // REPEAT command - repeat last response
            if (lowerTranscript.match(/^(repeat|say again|what did you say)/i)) {
                console.log('🔁 REPEAT command detected');
                const messages = document.querySelectorAll('.message.assistant');
                if (messages.length > 0) {
                    const lastMessage = messages[messages.length - 1];
                    const lastText = lastMessage.querySelector('.message-content')?.textContent || '';
                    if (lastText) {
                        speakText(lastText, state.language);
                        showNotification('🔁 Repeating last response', 'info');
                    }
                }
                document.getElementById('chat-input').value = '';
                return;
            }
            
            // VOLUME commands
            if (lowerTranscript.match(/^(volume|sound)/i)) {
                if (lowerTranscript.includes('up') || lowerTranscript.includes('increase') || lowerTranscript.includes('louder')) {
                    document.getElementById('chat-input').value = 'Increase system volume by 20%';
                } else if (lowerTranscript.includes('down') || lowerTranscript.includes('decrease') || lowerTranscript.includes('lower') || lowerTranscript.includes('quieter')) {
                    document.getElementById('chat-input').value = 'Decrease system volume by 20%';
                } else if (lowerTranscript.includes('mute')) {
                    document.getElementById('chat-input').value = 'Mute system volume';
                }
            }
            
            // If it's a regular question/command, proceed normally
            console.log('📤 Auto-submitting question...');
            
            // Ensure voice output is ON for wake word interaction
            if (!voiceOutputEnabled) {
                console.log('🔊 Auto-enabling voice output for wake word interaction');
                voiceOutputEnabled = true;
                updateVoiceOutputButton();
            }
            
            // Send the message automatically
            setTimeout(() => {
                handleSendMessage();
            }, 500);
        }
    };
    
    commandRecognition.onend = () => {
        if (voiceBtn) {
            voiceBtn.classList.remove('listening');
            voiceBtn.style.background = '';
            voiceBtn.style.borderColor = '';
        }
        
        // Restart wake word detection
        if (wakeWordEnabled) {
            setTimeout(() => {
                startWakeWordDetection();
            }, 1000);
        }
    };
    
    commandRecognition.onerror = (event) => {
        console.error('Command recognition error:', event.error);
        if (voiceBtn) {
            voiceBtn.classList.remove('listening');
            voiceBtn.style.background = '';
            voiceBtn.style.borderColor = '';
        }
        
        // Restart wake word detection
        if (wakeWordEnabled) {
            setTimeout(() => {
                startWakeWordDetection();
            }, 1000);
        }
    };
    
    commandRecognition.start();
}

function playActivationSound() {
    /**
     * Play a subtle activation sound when wake word detected
     */
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
        // Silent fail if audio context not available
    }
}

function stopSpeaking() {
    /**
     * Manually stop any ongoing speech
     * User can click this button to interrupt FRIDAY speaking
     */
    console.log('🛑 User manually stopped speech');
    
    // ============================================
    // STOP STREAMING TTS
    // ============================================
    if (window.streamingTTS) {
        window.streamingTTS.stopAll();
    }
    
    // Stop backend TTS audio
    if (window.currentAudio) {
        window.currentAudio.pause();
        window.currentAudio = null;
    }
    
    // Stop browser TTS
    if (synthesis && synthesis.speaking) {
        synthesis.cancel();
    }
    
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
    
    // Clear current utterance
    if (window.currentUtterance) {
        window.currentUtterance = null;
    }
    
    // Hide stop button
    const stopBtn = document.getElementById('stop-speech-btn');
    if (stopBtn) {
        stopBtn.style.display = 'none';
    }
    
    // Remove speaking indicator
    const voiceBtn = document.getElementById('voice-output-btn');
    if (voiceBtn) {
        voiceBtn.classList.remove('speaking');
    }
    
    showNotification('🔇 Speech stopped', 'info');
}

function toggleClipboardMonitor() {
    clipboardMonitorEnabled = !clipboardMonitorEnabled;
    const clipboardBtn = document.getElementById('clipboard-monitor-btn');
    
    if (clipboardMonitorEnabled) {
        // Add active class for visual feedback
        clipboardBtn.classList.add('active');
        clipboardBtn.title = '📋 Clipboard Monitor: ON (Auto-analyzes copied text)';
        startClipboardMonitoring();
        showNotification('📋 Clipboard monitoring ON - Copy text to analyze', 'success');
        console.log('✅ Clipboard monitor started');
    } else {
        // Remove active class
        clipboardBtn.classList.remove('active');
        clipboardBtn.title = '📋 Clipboard Monitor: OFF (Click to enable)';
        showNotification('📋 Clipboard monitoring OFF', 'info');
        console.log('⏸️ Clipboard monitor stopped');
    }
    
    // Save preference
    saveUserPreferences();
}

async function speakWithBackendTTS(text) {
    /**
     * Use Microsoft Edge Neural TTS for ultra-natural human-like voices
     * Same quality as Perplexity - works for ALL languages (English, Hindi, Nepali)
     */
    try {
        console.log(`🎙️ Using Edge Neural TTS for ${LANGUAGES[state.language].name}...`);
        
        // Clean text for natural speech
        let cleanText = text
            .replace(/```[\s\S]*?```/g, '. Code block omitted. ')
            .replace(/`([^`]+)`/g, '$1')
            .replace(/[*_~]/g, '')
            .replace(/#{1,6}\s/g, '')
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
            .replace(/https?:\/\/[^\s]+/g, 'link')
            .replace(/\s+/g, ' ')
            .trim();
        
        // DON'T truncate - read the FULL response!
        // Let the user hear the complete answer
        console.log(`📝 Preparing to speak FULL response: ${cleanText.length} characters`);
        
        console.log(`📤 Sending TTS request: ${cleanText.length} chars`);
        
        // Call backend TTS API
        const response = await fetch(`${API_BASE_URL}/api/tts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: cleanText,
                language_code: state.language,
                slow: false
            })
        });
        
        if (!response.ok) {
            throw new Error('TTS API request failed');
        }
        
        const data = await response.json();
        
        if (data.success && data.audio) {
            console.log('✅ Received ultra-natural neural voice audio');
            
            // STOP any previous audio that might be playing
            if (window.currentAudio) {
                window.currentAudio.pause();
                window.currentAudio = null;
                console.log('🛑 Stopped previous audio');
            }
            
            // Create and play audio element
            const audio = new Audio(data.audio);
            
            // Store reference globally so we can stop it if needed
            window.currentAudio = audio;
            
            // Update UI during playback
            const voiceBtn = document.getElementById('voice-output-btn');
            
            audio.onplay = () => {
                if (voiceBtn) voiceBtn.classList.add('speaking');
                
                // SHOW stop button when speaking starts
                const stopBtn = document.getElementById('stop-speech-btn');
                if (stopBtn) {
                    stopBtn.style.display = 'block';
                    stopBtn.style.background = 'rgba(255, 51, 102, 0.2)';
                    stopBtn.style.borderColor = 'var(--jarvis-error)';
                }
                
                console.log('🔊 Playing FULL response with Edge Neural TTS');
            };
            
            audio.onended = () => {
                if (voiceBtn) voiceBtn.classList.remove('speaking');
                window.currentAudio = null;
                
                // HIDE stop button when finished
                const stopBtn = document.getElementById('stop-speech-btn');
                if (stopBtn) {
                    stopBtn.style.display = 'none';
                    stopBtn.style.background = '';
                    stopBtn.style.borderColor = '';
                }
                
                console.log('✅ Finished playing FULL audio');
            };
            
            audio.onerror = (e) => {
                if (voiceBtn) voiceBtn.classList.remove('speaking');
                window.currentAudio = null;
                
                // HIDE stop button on error
                const stopBtn = document.getElementById('stop-speech-btn');
                if (stopBtn) {
                    stopBtn.style.display = 'none';
                }
                
                console.error('❌ Audio playback error:', e);
                showNotification('Voice playback failed', 'error');
            };
            
            // Play audio
            await audio.play();
            
        } else {
            throw new Error(data.error || 'TTS generation failed');
        }
        
    } catch (error) {
        console.error('❌ Backend TTS error:', error);
        showNotification('Voice synthesis failed: ' + error.message, 'error');
        
        // Fallback to browser TTS
        console.log('Falling back to browser TTS...');
        // Continue with normal browser TTS code below
    }
}

async function speakText(text) {
    if (!voiceOutputEnabled || !text) {
        console.log('Voice output disabled or no text');
        return;
    }
    
    console.log('🎤 Attempting to speak text...');
    
    // Cancel any ongoing speech
    if (currentUtterance) {
        synthesis.cancel();
        currentUtterance = null;
    }
    
    // Use Edge Neural TTS for ALL languages (ultra-natural female voices)
    if (state.language === 'hi-IN' || state.language === 'ne-NP' || state.language === 'en-US') {
        await speakWithBackendTTS(text);
        return;
    }
    
    // Fallback to browser TTS (should rarely be used)
    
    // Ensure voices are loaded
    if (!voicesLoaded || availableVoices.length === 0) {
        console.log('⏳ Loading voices...');
        await ensureVoicesLoaded();
        
        if (availableVoices.length === 0) {
            console.error('❌ No voices available');
            showNotification('No voices available. Please check browser settings.', 'error');
            return;
        }
    }
    
    // Clean text for natural speech
    let cleanText = text
        // Remove code blocks with description
        .replace(/```[\s\S]*?```/g, '. Code block omitted. ')
        // Remove inline code
        .replace(/`([^`]+)`/g, '$1')
        // Remove markdown formatting
        .replace(/[*_~]/g, '')
        .replace(/#{1,6}\s/g, '')
        // Convert links to just text
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
        // Remove URLs
        .replace(/https?:\/\/[^\s]+/g, 'link')
        // Clean up multiple spaces
        .replace(/\s+/g, ' ')
        // Add natural pauses for readability
        .replace(/\.\s+/g, '. ')
        .replace(/\?\s+/g, '? ')
        .replace(/!\s+/g, '! ')
        .trim();
    
    // DON'T truncate - read FULL response!
    console.log(`📝 Speaking FULL response: ${cleanText.length} characters`);
    
    if (!cleanText) {
        console.log('No clean text to speak');
        return;
    }
    
    console.log(`🗣️ Speaking: "${cleanText.substring(0, 100)}..."`);
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    currentUtterance = utterance;
    
    // Set language
    utterance.lang = state.language;
    console.log(`🌍 Language set to: ${state.language}`);
    
    // Use custom rate if set in settings, otherwise use language-specific default
    const langCode = state.language.split('-')[0];
    const customRate = state.voiceRate || languageRates[langCode] || 0.95;
    utterance.rate = customRate;     // Apply user's speech rate preference
    utterance.pitch = 1.0;           // Normal, human pitch
    utterance.volume = 1.0;          // Full volume for clarity
    
    console.log(`🎤 Speech rate applied: ${customRate.toFixed(2)} (${state.voiceRate ? 'custom' : 'default'})`);
    
    // Add slight pauses for natural speech
    utterance.onboundary = (event) => {
        if (event.name === 'sentence') {
            // Natural pause between sentences
        }
    };
    
    // Find the best voice for the language
    const selectedVoice = getBestVoiceForLanguage(state.language);
    
    if (selectedVoice) {
        utterance.voice = selectedVoice;
        console.log(`🎤 Using voice: ${selectedVoice.name} (${selectedVoice.lang}) - Local: ${selectedVoice.localService}`);
    } else {
        console.warn(`⚠️ No voice available for ${state.language} (${LANGUAGES[state.language].name})`);
        console.warn('💡 Available languages:', [...new Set(availableVoices.map(v => v.lang))].join(', '));
        
        // Show notification only once per session
        if (!window.voiceWarningShown) {
            showNotification(`No ${LANGUAGES[state.language].name} voice found. Install language pack or using default voice.`, 'warning');
            window.voiceWarningShown = true;
        }
        
        // Try to use English as fallback
        const englishVoice = availableVoices.find(v => v.lang.startsWith('en'));
        if (englishVoice) {
            utterance.voice = englishVoice;
            console.log('🔄 Fallback to English voice:', englishVoice.name);
        }
    }
    
    // Add event listeners for better control
    utterance.onstart = () => {
        const voiceBtn = document.getElementById('voice-output-btn');
        if (voiceBtn) {
            voiceBtn.classList.add('speaking');
        }
        
        // SHOW stop button
        const stopBtn = document.getElementById('stop-speech-btn');
        if (stopBtn) {
            stopBtn.style.display = 'block';
            stopBtn.style.background = 'rgba(255, 51, 102, 0.2)';
            stopBtn.style.borderColor = 'var(--jarvis-error)';
        }
        
        console.log('✅ Started speaking FULL response');
    };
    
    utterance.onend = () => {
        const voiceBtn = document.getElementById('voice-output-btn');
        if (voiceBtn) {
            voiceBtn.classList.remove('speaking');
        }
        
        // HIDE stop button
        const stopBtn = document.getElementById('stop-speech-btn');
        if (stopBtn) {
            stopBtn.style.display = 'none';
            stopBtn.style.background = '';
            stopBtn.style.borderColor = '';
        }
        
        console.log('✅ Finished speaking FULL response');
    };
    
    utterance.onerror = (event) => {
        const voiceBtn = document.getElementById('voice-output-btn');
        if (voiceBtn) {
            voiceBtn.classList.remove('speaking');
        }
        
        // HIDE stop button
        const stopBtn = document.getElementById('stop-speech-btn');
        if (stopBtn) {
            stopBtn.style.display = 'none';
        }
        console.error('❌ Speech error:', event.error, event);
        
        if (event.error === 'not-allowed') {
            showNotification('Speech blocked. Please allow audio in browser settings.', 'error');
        } else if (event.error === 'network') {
            showNotification('Network error. Trying local voice...', 'warning');
        } else if (event.error === 'synthesis-unavailable') {
            showNotification('Speech synthesis not available.', 'error');
        } else {
            showNotification(`Voice error: ${event.error}`, 'error');
        }
    };
    
    // Speak the text
    try {
        console.log(`🔊 Calling synthesis.speak() with ${cleanText.length} characters`);
        
        // Use a small delay to ensure browser is ready
        await new Promise(resolve => setTimeout(resolve, 50));
        
        synthesis.speak(utterance);
        
        // Wait a bit and verify speech started
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (synthesis.speaking || synthesis.pending) {
            console.log('✅ Speech started successfully');
        } else {
            console.warn('⚠️ Speech may not have started - retrying...');
            // Retry once
            synthesis.speak(utterance);
        }
    } catch (error) {
        console.error('❌ Failed to speak:', error);
        showNotification('Voice output failed: ' + error.message, 'error');
        currentUtterance = null;
    }
}

function updateVoiceOutputButton() {
    const voiceOutputBtn = document.getElementById('voice-output-btn');
    if (!voiceOutputBtn) return;
    
    if (voiceOutputEnabled) {
        voiceOutputBtn.style.background = 'rgba(0, 217, 255, 0.2)';
        voiceOutputBtn.style.borderColor = 'var(--jarvis-primary)';
        voiceOutputBtn.classList.add('active');
    } else {
        voiceOutputBtn.style.background = '';
        voiceOutputBtn.style.borderColor = '';
        voiceOutputBtn.classList.remove('active');
    }
}

function testVoice() {
    console.log('🔊 Testing voice for language:', state.language);
    
    const testMessages = {
        'en-US': 'Hello! I am FRIDAY, your female AI assistant. How can I help you today?',
        'ne-NP': 'नमस्ते! म FRIDAY हुँ, तपाईंको महिला AI सहायक। म तपाईंलाई कसरी मद्दत गर्न सक्छु?',
        'hi-IN': 'नमस्ते! मैं FRIDAY हूं, आपकी महिला AI सहायक। मैं आपकी कैसे मदद कर सकती हूं?'
    };
    
    const testMessage = testMessages[state.language] || testMessages['en-US'];
    
    // Temporarily enable voice output for test
    const wasEnabled = voiceOutputEnabled;
    voiceOutputEnabled = true;
    
    showNotification(`Testing ${LANGUAGES[state.language].name} voice...`, 'info');
    speakText(testMessage);
    
    // Restore previous state
    if (!wasEnabled) {
        setTimeout(() => {
            voiceOutputEnabled = wasEnabled;
        }, 100);
    }
}

// ============================================
// Message Editing
// ============================================

function addMessageActions(messageDiv, role, content, messageIndex) {
    if (role !== 'user' && role !== 'assistant') return;
    
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'message-actions';
    
    if (role === 'user') {
        const editBtn = document.createElement('button');
        editBtn.className = 'message-action-btn';
        editBtn.title = 'Edit message';
        editBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M11 0a3 3 0 013 3v8a3 3 0 01-3 3H3a3 3 0 01-3-3V3a3 3 0 013-3h8zm-1 7.5a.5.5 0 00-.5-.5h-5a.5.5 0 000 1h5a.5.5 0 00.5-.5z"/>
            </svg>
        `;
        editBtn.onclick = () => editMessage(messageIndex, content);
        actionsDiv.appendChild(editBtn);
    } else {
        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
        copyBtn.title = 'Copy message';
        copyBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M3 1a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2V1z"/>
                <path d="M1 5a2 2 0 00-2 2v5a2 2 0 002 2h5a2 2 0 002-2v-1H6a2 2 0 01-2-2V5H1z"/>
            </svg>
        `;
        copyBtn.onclick = () => copyMessageToClipboard(content);
        
        // Speak button
        const speakBtn = document.createElement('button');
        speakBtn.className = 'message-action-btn';
        speakBtn.title = 'Speak message';
        speakBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M6.383 1.076A1 1 0 017 2v10a1 1 0 01-1.707.707L2.586 10H1a1 1 0 01-1-1V5a1 1 0 011-1h1.586l2.707-2.707a1 1 0 011.09-.217z"/>
                <path d="M10 4a1 1 0 011.707-.707A5 5 0 0113 7a5 5 0 01-1.293 3.707A1 1 0 1110 9.586 3 3 0 0011 7a3 3 0 00-.707-1.914A1 1 0 0110 4z"/>
            </svg>
        `;
        speakBtn.onclick = () => speakText(content);
        
        // Regenerate button
        const regenBtn = document.createElement('button');
        regenBtn.className = 'message-action-btn';
        regenBtn.title = 'Regenerate response';
        regenBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M8 3a.5.5 0 01.5.5v2a.5.5 0 01-.5.5H6a.5.5 0 010-1h1.5V3.5A.5.5 0 018 3zm-3.5 9a.5.5 0 01-.5-.5v-2a.5.5 0 01.5-.5H7a.5.5 0 010 1H5.5v1.5a.5.5 0 01-.5.5z"/>
                <path d="M7 1a7 7 0 105.192 11.5.5.5 0 11.738.677A8 8 0 1113 3.5V1h-1v2.5a.5.5 0 001 0V1h1a1 1 0 011 1v1.5a.5.5 0 01-1 0V2h-.268A7 7 0 017 1z"/>
            </svg>
        `;
        regenBtn.onclick = () => regenerateResponse(messageIndex);
        
        actionsDiv.appendChild(copyBtn);
        actionsDiv.appendChild(speakBtn);
        actionsDiv.appendChild(regenBtn);
    }
    
    messageDiv.appendChild(actionsDiv);
}

function copyMessageToClipboard(content) {
    navigator.clipboard.writeText(content).then(() => {
        showNotification('Message copied', 'success');
    }).catch(err => {
        showNotification('Failed to copy', 'error');
    });
}

async function editMessage(messageIndex, originalContent) {
    const newContent = prompt('Edit message:', originalContent);
    
    if (!newContent || newContent.trim() === '' || newContent === originalContent) {
        return;
    }
    
    try {
        // Simply resend the edited message
        document.getElementById('chat-input').value = newContent;
        await handleSendMessage();
        showNotification('Message edited and resent', 'success');
    } catch (error) {
        console.error('Error editing message:', error);
        showNotification('Failed to edit message', 'error');
    }
}

async function regenerateResponse(messageIndex) {
    try {
        showNotification('Regenerating response...', 'info');
        
        // Get the last user message and resend it
        const chatMessages = document.getElementById('chat-messages');
        const messages = chatMessages.querySelectorAll('.message');
        
        // Find the last user message
        let lastUserMessage = null;
        for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i].classList.contains('user-message')) {
                const contentEl = messages[i].querySelector('.message-content');
                if (contentEl) {
                    lastUserMessage = contentEl.textContent.trim();
                    break;
                }
            }
        }
        
        if (lastUserMessage) {
            document.getElementById('chat-input').value = lastUserMessage;
            await handleSendMessage();
        } else {
            showNotification('No message to regenerate', 'error');
        }
    } catch (error) {
        console.error('Error regenerating:', error);
        showNotification('Failed to regenerate', 'error');
    }
}

// ============================================
// Screen Capture (requires Tauri permissions)
// ============================================

async function captureScreen() {
    try {
        console.log('📸 Starting screen capture...');
        showNotification('Select the screen/window to capture', 'info');
        
        // Using browser's screen capture API
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                mediaSource: 'screen',
                cursor: 'always'
            }
        });
        
        const video = document.createElement('video');
        video.srcObject = stream;
        video.play();
        
        // Wait for video to be ready
        await new Promise(resolve => {
            video.onloadedmetadata = resolve;
        });
        
        // Wait a bit for video to stabilize
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Create canvas and capture frame
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        // Stop stream
        stream.getTracks().forEach(track => track.stop());
        
        // Convert to base64
        const screenshot = canvas.toDataURL('image/png');
        
        // Add to chat
        addImagePreview(screenshot, `screenshot-${Date.now()}.png`);
        const chatInput = document.getElementById('chat-input');
        chatInput.value = 'Please analyze this screenshot and tell me what you see.';
        chatInput.focus();
        
        showNotification('✅ Screenshot captured! Click Send to analyze', 'success');
        console.log('✅ Screenshot captured successfully');
        
    } catch (error) {
        if (error.name === 'NotAllowedError') {
            console.log('Screen capture cancelled by user');
            showNotification('Screen capture cancelled', 'info');
        } else {
            console.error('Screen capture error:', error);
            showNotification('Screen capture failed: ' + error.message, 'error');
        }
    }
}

// ============================================
// Clipboard Monitor
// ============================================

let clipboardMonitorEnabled = false;
let lastClipboard = '';

function startClipboardMonitoring() {
    if (!clipboardMonitorEnabled) return;
    
    setInterval(async () => {
        if (!clipboardMonitorEnabled) return;
        
        try {
            const text = await navigator.clipboard.readText();
            
            if (text && text !== lastClipboard && text.length > 10) {
                lastClipboard = text;
                
                // Show subtle notification
                const shouldAnalyze = confirm(`Clipboard changed. Analyze this text?\n\n${text.substring(0, 100)}...`);
                
                if (shouldAnalyze) {
                    document.getElementById('chat-input').value = `Please analyze this text:\n\n${text}`;
                }
            }
        } catch (error) {
            // Clipboard access denied or not focused
        }
    }, 3000);
}

// ============================================
// Conversation Summarization
// ============================================

async function summarizeConversation(conversationId) {
    try {
        showNotification('Generating summary...', 'info');
        
        const chatInput = document.getElementById('chat-input');
        chatInput.value = 'Please summarize our conversation so far, highlighting the key points and conclusions.';
        
        await handleSendMessage();
        
    } catch (error) {
        console.error('Summarization error:', error);
        showNotification('Failed to summarize', 'error');
    }
}

// ============================================
// Context Menu
// ============================================

function showContextMenu(x, y, selectedText) {
    // Remove existing context menu
    const existing = document.getElementById('context-menu');
    if (existing) existing.remove();
    
    const menu = document.createElement('div');
    menu.id = 'context-menu';
    menu.className = 'context-menu';
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    
    // Store selected text for use in handlers
    const escapedText = selectedText.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
    
    // Create menu items with proper event handlers
    const menuItems = [
        { icon: '❓', text: 'Explain this', action: 'explain' },
        { icon: '🌐', text: 'Translate this', action: 'translate' },
        { icon: '📝', text: 'Summarize this', action: 'summarize' },
        { icon: '✨', text: 'Fix/Improve this', action: 'fix' }
    ];
    
    menuItems.forEach(item => {
        const menuItem = document.createElement('div');
        menuItem.className = 'context-menu-item';
        menuItem.innerHTML = `<span style="font-size: 1.1rem; margin-right: 0.5rem;">${item.icon}</span> ${item.text}`;
        
        menuItem.addEventListener('click', (e) => {
            e.stopPropagation();
            askAboutSelection(selectedText, item.action);
        });
        
        menu.appendChild(menuItem);
    });
    
    document.body.appendChild(menu);
}

function askAboutSelection(text, action) {
    const chatInput = document.getElementById('chat-input');
    
    const actionPrompts = {
        'explain': `Explain this: "${text}"`,
        'translate': `Translate this to ${state.outputLanguage}: "${text}"`,
        'summarize': `Summarize this: "${text}"`,
        'fix': `Fix and improve this text: "${text}"`
    };
    
    chatInput.value = actionPrompts[action] || text;
    chatInput.focus();
    
    // Remove context menu
    const contextMenu = document.getElementById('context-menu');
    if (contextMenu) contextMenu.remove();
}

// ============================================
// Smart Suggestions
// ============================================

function showSmartSuggestions() {
    const suggestions = [
        { text: "What can you help me with?", icon: "❓" },
        { text: "Analyze my clipboard", icon: "📋" },
        { text: "Take a screenshot and analyze", icon: "📸" },
        { text: "Summarize this conversation", icon: "📝" },
        { text: "What's my system status?", icon: "💻" },
        { text: "Search the web", icon: "🔍" }
    ];
    
    const suggestionsHTML = suggestions.map(s => `
        <button class="suggestion-btn" onclick="useSuggestion('${s.text}')">
            <span class="suggestion-icon">${s.icon}</span>
            <span>${s.text}</span>
        </button>
    `).join('');
    
    return suggestionsHTML;
}

function useSuggestion(text) {
    document.getElementById('chat-input').value = text;
    document.getElementById('chat-input').focus();
}

// Helper function to show available voices
function showAvailableVoices() {
    const voices = speechSynthesis.getVoices();
    console.log(`\n📢 Available Voices (${voices.length} total):\n`);
    
    const grouped = {};
    voices.forEach(voice => {
        const lang = voice.lang.split('-')[0];
        if (!grouped[lang]) grouped[lang] = [];
        grouped[lang].push(voice);
    });
    
    Object.keys(grouped).sort().forEach(lang => {
        console.log(`\n${lang.toUpperCase()}:`);
        grouped[lang].forEach(v => {
            console.log(`  - ${v.name} (${v.lang}) ${v.localService ? '[Local]' : '[Remote]'}`);
        });
    });
    
    console.log('\n💡 To test a voice, run: jarvis.speakText("Hello world")');
    console.log('💡 Current language:', state.language);
    console.log('💡 Voice output enabled:', voiceOutputEnabled);
}

// Export for use in other modules and inline event handlers
window.jarvis = {
    state,
    sendMessage: handleSendMessage,
    loadConversation,
    loadProject,
    startNewChat,
    deleteAllChats,
    closeSettings,
    saveSettings,
    downloadImage,
    openImageModal,
    captureScreen,
    toggleClipboardMonitor,
    summarizeConversation,
    speakText,
    testVoice,
    askAboutSelection,
    useSuggestion,
    showAvailableVoices,
    // Debugging helpers
    debug: {
        voiceEnabled: () => voiceOutputEnabled,
        toggleVoice: toggleVoiceOutput,
        testVoice: testVoice,
        showVoices: showAvailableVoices,
        currentLang: () => state.language
    }
};

// Make functions globally available for inline onclick handlers AND wake word system
window.captureScreen = captureScreen;
window.toggleClipboardMonitor = toggleClipboardMonitor;
window.toggleWakeWord = toggleWakeWord;
window.useSuggestion = useSuggestion;
window.downloadImage = downloadImage;
window.openImageModal = openImageModal;
window.copyMessageToClipboard = copyMessageToClipboard;
window.speakText = speakText;
window.stopSpeaking = stopSpeaking;
window.askAboutSelection = askAboutSelection;

// Settings functions
window.testVoice = testVoice;
window.saveSettings = saveSettings;
window.closeSettings = closeSettings;

// ============================================
// EXPOSE CORE FUNCTIONS FOR WAKE WORD SYSTEM
// ============================================
window.addMessage = addMessage;
window.streamChatResponse = streamChatResponse;
window.startNewChat = startNewChat;
window.fridayState = state;  // Expose state for language detection

console.log('✅ Core functions exposed to window for wake word integration');

// ============================================
// HAND TRACKING GESTURE EVENT LISTENERS
// ============================================

// Wake gesture - trigger wake word detection
window.addEventListener('gesture-wake', () => {
    console.log('🖐️ Gesture: Open Palm detected - Waking FRIDAY');
    
    // Stop any ongoing speech
    stopSpeaking();
    
    // Start command listening
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const commandRecognition = new SpeechRecognition();
        
        commandRecognition.lang = state.language;
        commandRecognition.continuous = false;
        commandRecognition.interimResults = false;
        
        // Show processing indicator
        const processingIndicator = document.getElementById('processing-indicator');
        if (processingIndicator) {
            processingIndicator.style.display = 'flex';
        }
        
        commandRecognition.onresult = async (event) => {
            const command = event.results[0][0].transcript.trim();
            console.log('🎤 Hand gesture voice command:', command);
            
            // Hide processing indicator
            if (processingIndicator) {
                processingIndicator.style.display = 'none';
            }
            
            // Send command to FRIDAY
            if (command) {
                addMessage('user', command);
                await streamChatResponse(command);
            }
        };
        
        commandRecognition.onerror = (event) => {
            console.error('Voice command error:', event.error);
            if (processingIndicator) {
                processingIndicator.style.display = 'none';
            }
        };
        
        commandRecognition.start();
        console.log('🎤 Listening for command after hand gesture...');
    }
});

// Stop gesture - stop speaking
window.addEventListener('gesture-stop', () => {
    console.log('🖐️ Gesture: Fist detected - Stopping');
    stopSpeaking();
});

// New chat gesture
window.addEventListener('gesture-new-chat', () => {
    console.log('🖐️ Gesture: Thumbs Up - Starting new chat');
    startNewChat();
});

// Repeat gesture - repeat last response
window.addEventListener('gesture-repeat', () => {
    console.log('🖐️ Gesture: Peace Sign - Repeating last response');
    
    // Find last assistant message
    const messages = document.querySelectorAll('.jarvis-message.assistant');
    if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        const text = lastMessage.querySelector('.message-text')?.textContent;
        
        if (text) {
            speakText(text);
        }
    }
});

console.log('✅ Hand tracking gesture listeners registered');

// ============================================
// AUTO PROVIDER SELECTION BASED ON LANGUAGE
// ============================================
// Provider is now automatically selected by backend based on language:
// - English (en-US) → Groq (fast)
// - Hindi (hi-IN) → Gemini (multilingual)
// - Nepali (ne-NP) → Gemini (multilingual)
console.log('✅ Auto provider selection enabled (based on language)');

