const showSidebar = document.querySelector('#showSidebar');
if (showSidebar) {
    showSidebar.addEventListener('click', e => {
        e.preventDefault();

        const sidebar = document.querySelector('.nav-sidebar');
        sidebar.style.transform = 'translateX(0)';
    });
}

const hideSidebar = document.querySelector('#hideSidebar');
if (hideSidebar) {
    hideSidebar.addEventListener('click', e => {
        e.preventDefault();

        const sidebar = document.querySelector('.nav-sidebar');
        if (!sidebar) return;
        if (window.innerWidth < 480) {
            sidebar.style.transform = 'translateX(100vw)';
        } else {
            sidebar.style.transform = 'translateX(50vw)';
        }
    });
}

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

const userMenu = document.querySelector('.user-menu');
if (userMenu) {
    const userMenuTrigger = userMenu.querySelector('.user-menu-trigger');

    if (userMenuTrigger) {
        userMenuTrigger.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();

            const isOpen = userMenu.classList.toggle('is-open');
            userMenuTrigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        document.addEventListener('click', (event) => {
            if (!userMenu.contains(event.target)) {
                userMenu.classList.remove('is-open');
                userMenuTrigger.setAttribute('aria-expanded', 'false');
            }
        });
    }
}

const userMenuSidebar = document.querySelector('.user-menu.sidebar');
if (userMenuSidebar) {
    const userMenuTrigger = userMenuSidebar.querySelector('.user-menu-trigger');

    if (userMenuTrigger) {
        userMenuTrigger.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();

            const isOpen = userMenuSidebar.classList.toggle('is-open');
            userMenuTrigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        document.addEventListener('click', (event) => {
            if (!userMenuSidebar.contains(event.target)) {
                userMenuSidebar.classList.remove('is-open');
                userMenuTrigger.setAttribute('aria-expanded', 'false');
            }
        });
    }
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