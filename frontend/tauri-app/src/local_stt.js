class LocalSTTClient {
    constructor() {
        this.mediaRecorder = null;
        this.chunks = [];
        this.isActive = false;
        this.onResult = null;  // callback(text, isFinal)
    }

    async start(onResult) {
        this.onResult = onResult;
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        this.chunks = [];
        this.isActive = true;

        // Collect small chunks and send periodically
        this.mediaRecorder.ondataavailable = async (e) => {
            if (!this.isActive) return;
            if (e.data && e.data.size > 0) {
                try {
                    const blob = e.data;
                    const form = new FormData();
                    form.append('file', blob, 'audio.webm');
                    // Non-streaming small-chunk transcription
                    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                    const resp = await fetch(`${API_BASE_URL}/api/stt/transcribe`, {
                        method: 'POST',
                        body: form
                    });
                    const data = await resp.json();
                    if (data?.success && data.text && this.onResult) {
                        this.onResult(data.text, false);
                    }
                } catch (err) {
                    console.error('Local STT chunk error:', err);
                }
            }
        };

        this.mediaRecorder.start(750); // timeslice (ms)
    }

    stop() {
        this.isActive = false;
        try {
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
            }
        } catch {}
        this.mediaRecorder = null;
    }
}

window.localSTT = new LocalSTTClient();


