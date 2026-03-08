class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
    }

    async startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
            this.audioChunks.push(event.data);
        };

        this.mediaRecorder.start();
        console.log("Gravação iniciada...");
    }

    async stopRecording() {
        return new Promise((resolve) => {
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');

                // Envia para o backend (ajuste a URL conforme seu servidor)
                const response = await fetch('http://localhost:5000/api/interview/process-voice', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                resolve(data.transcription); // Retorna o texto transcrito pela IA
            };
            this.mediaRecorder.stop();
        });
    }
}

export default AudioRecorder;