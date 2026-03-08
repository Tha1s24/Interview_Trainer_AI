import AudioRecorder from './recorder.js';

const recorder = new AudioRecorder();
const chatContainer = document.getElementById('chat-container');
const btnAction = document.getElementById('btn-action');

let interviewHistory = []; // Mantém o contexto para o GPT

// Função para renderizar mensagens no chat
function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.innerText = text;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Lógica de envio ao Backend
async function sendToAI(userText) {
    interviewHistory.push({ role: "user", content: userText });

    const response = await fetch('http://localhost:5000/api/interview/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: interviewHistory })
    });

    const data = await response.json();
    interviewHistory.push({ role: "assistant", content: data.question });
    addMessage('ai', data.question);
}

// Evento de Click
btnAction.addEventListener('click', async () => {
    if (btnAction.dataset.status !== 'recording') {
        // Iniciar
        await recorder.startRecording();
        btnAction.dataset.status = 'recording';
        btnAction.innerText = "🛑 Parar e Responder";
    } else {
        // Finalizar e Processar
        btnAction.dataset.status = 'idle';
        btnAction.innerText = "🎙️ Falar";
        
        const transcription = await recorder.stopRecording();
        addMessage('user', transcription);
        await sendToAI(transcription);
    }
});