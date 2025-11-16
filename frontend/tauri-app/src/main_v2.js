/**
 * FRIDAY V2 - Stateless Architecture
 * Frontend manages full conversation state
 * Backend is stateless - just processes messages
 */

const API_BASE_URL = 'http://localhost:8000';

// SIMPLE STATE - Frontend keeps EVERYTHING
const fridayV2 = {
    conversationId: localStorage.getItem('conv_id') || null,
    messages: JSON.parse(localStorage.getItem('conv_messages') || '[]'),
    language: localStorage.getItem('language') || 'en-US'
};

console.log('FRIDAY V2 Initialized');
console.log('Conversation ID:', fridayV2.conversationId);
console.log('Messages in memory:', fridayV2.messages.length);

// Save state to localStorage
function saveState() {
    if (fridayV2.conversationId) {
        localStorage.setItem('conv_id', fridayV2.conversationId);
    }
    localStorage.setItem('conv_messages', JSON.stringify(fridayV2.messages));
    localStorage.setItem('language', fridayV2.language);
    
    console.log('💾 State saved to localStorage');
    console.log('   Messages:', fridayV2.messages.length);
}

// Send message
async function sendMessageV2(userMessage) {
    // Add user message to history
    fridayV2.messages.push({
        role: 'user',
        content: userMessage
    });
    
    console.log('📤 Sending to V2 API');
    console.log('   Total messages:', fridayV2.messages.length);
    console.log('   Conversation ID:', fridayV2.conversationId);
    
    // Display user message
    displayMessage('user', userMessage);
    
    // Send FULL history to backend
    const response = await fetch(`${API_BASE_URL}/api/chat/v2/stream`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            messages: fridayV2.messages,  // FULL HISTORY
            conversation_id: fridayV2.conversationId,
            language: fridayV2.language
        })
    });
    
    // Get conversation ID from header
    const convId = response.headers.get('X-Conversation-ID');
    if (convId && !fridayV2.conversationId) {
        fridayV2.conversationId = convId;
        console.log('✅ New conversation ID:', convId);
    }
    
    // Stream response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    
    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'token') {
                    fullResponse += data.content;
                    updateLastMessage(fullResponse);
                }
                else if (data.type === 'done') {
                    // Add assistant response to history
                    fridayV2.messages.push({
                        role: 'assistant',
                        content: fullResponse
                    });
                    
                    // Save state
                    saveState();
                    
                    console.log('✅ Response complete');
                    console.log('   Total messages now:', fridayV2.messages.length);
                }
            }
        }
    }
}

// Start new conversation
function newConversationV2() {
    fridayV2.conversationId = null;
    fridayV2.messages = [];
    localStorage.removeItem('conv_id');
    localStorage.removeItem('conv_messages');
    
    console.log('🆕 New conversation started');
    clearChat();
}

// Display message
function displayMessage(role, content) {
    const chatDiv = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    msgDiv.innerHTML = `
        <div class="avatar">${role === 'user' ? 'U' : 'F'}</div>
        <div class="content">${content}</div>
    `;
    chatDiv.appendChild(msgDiv);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

function updateLastMessage(content) {
    const messages = document.querySelectorAll('.message.assistant');
    if (messages.length > 0) {
        const last = messages[messages.length - 1];
        const contentDiv = last.querySelector('.content');
        if (contentDiv) {
            contentDiv.textContent = content;
        }
    } else {
        displayMessage('assistant', content);
    }
}

function clearChat() {
    document.getElementById('chat-messages').innerHTML = '';
}

// Expose globally
window.fridayV2 = {
    send: sendMessageV2,
    newChat: newConversationV2,
    state: fridayV2
};

console.log('✅ FRIDAY V2 loaded - Use window.fridayV2.send("your message")');

