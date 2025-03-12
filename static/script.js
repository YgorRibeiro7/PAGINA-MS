const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

// Validação do email corporativo no frontend
cadastrarForm.addEventListener('submit', (event) => {
    const emailInput = cadastrarForm.querySelector('input[name="email"]');
    const email = emailInput.value;

    if (!email.endsWith('@msconnect.com.br')) {
        alert('Apenas emails corporativos (@msconnect.com.br) são permitidos.');
        event.preventDefault(); // Impede o envio do formulário
    }
});