// session_monitor.js

// Função para redirecionar o usuário para a página de login
function redirectToLogin() {
    alert('Sua sessão expirou. Você será redirecionado para a página de login.');
    window.location.href = '/static/login.html';
}

// Função para verificar a sessão
function checkSession() {
    fetch('/check-session', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        if (response.status === 401) {
            redirectToLogin();
        }
    })
    .catch(error => {
        console.error('Erro ao verificar a sessão:', error);
        redirectToLogin();
    });
}

setInterval(checkSession, 60000);
