// frontend/js/api.js
const API_BASE_URL = 'http://localhost:5000/api';

const API = {
    async post(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    async uploadAudio(formData) {
        const response = await fetch(`${API_BASE_URL}/interview/process-voice`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }
};

export default API;