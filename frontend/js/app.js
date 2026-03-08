// frontend/js/app.js
import API from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("Interview Trainer AI Initialized.");
    
    // Verificação simples de sessão
    const user = localStorage.getItem('user');
    if (!user && window.location.pathname !== '/login.html') {
        // window.location.href = '/login.html'; // Descomente para forçar login
    }
});

// Exemplo de como usar o API.js para login
async function handleLogin(email, password) {
    const result = await API.post('/auth/login', { email, password });
    if (result.user) {
        localStorage.setItem('user', JSON.stringify(result.user));
        alert("Bem-vindo!");
    }
}

// Exemplo de como capturar o registro no app.js
const registerForm = document.getElementById('register-form');

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        // Chamada para o backend (usando o api.js que criamos)
        const result = await API.post('/auth/register', { name, email, password });
        
        if (result) {
            alert("Conta criada com sucesso! Redirecionando...");
            window.location.href = 'login.html';
        }
    });
}