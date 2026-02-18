console.log('main.js');

const landingCustomerBtn = document.querySelector('#landingCustomerBtn');
if (landingCustomerBtn) {
    landingCustomerBtn.addEventListener('click', e => {
        e.preventDefault();

        window.location.href = landingCustomerBtn.dataset.url;
    });
}

const landingRegisterBtn = document.querySelector('#landingRegisterBtn');
if (landingRegisterBtn) {
    landingRegisterBtn.addEventListener('click', e => {
        e.preventDefault();

        window.location.href = landingRegisterBtn.dataset.url;
    });
}

const loginBtn = document.querySelector('#loginBtn');
if (loginBtn && loginBtn.dataset.url) {
    loginBtn.addEventListener('click', e => {
        e.preventDefault();
        window.location.href = loginBtn.dataset.url;
    });
}

const registerBtn = document.querySelector('#registerBtn');
if (registerBtn && registerBtn.dataset.url) {
    registerBtn.addEventListener('click', e => {
        e.preventDefault();
        window.location.href = registerBtn.dataset.url;
    });
}

const backToHome = document.querySelector('#backToHome');
if (backToHome) {
    backToHome.addEventListener('click', e => {
        e.preventDefault();

        window.location.href = backToHome.dataset.url;
    });
}

const passwordToggleButtons = document.querySelectorAll('.password-toggle-btn');
if (passwordToggleButtons.length) {
    passwordToggleButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const targetId = button.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            button.setAttribute('aria-label', isPassword ? 'Sakrij lozinku' : 'Prikaži lozinku');
            button.setAttribute('aria-pressed', isPassword ? 'true' : 'false');
            button.classList.toggle('is-visible', isPassword);
        });
    });
}

const noNavLink = document.getElementById('alreadyHasAccountLink');
if (noNavLink) {
    noNavLink.addEventListener('click', (event) => {
        event.preventDefault();
    });
}

const flashMessages = document.querySelectorAll('.messages .message');
if (flashMessages.length) {
    setTimeout(() => {
        flashMessages.forEach((message) => {
            message.style.transition = 'opacity 240ms ease, transform 240ms ease';
            message.style.opacity = '0';
            message.style.transform = 'translateY(-6px)';

            setTimeout(() => {
                const container = message.parentElement;
                message.remove();

                if (container && container.classList.contains('messages') && container.children.length === 0) {
                    container.remove();
                }
            }, 250);
        });
    }, 3000);
}