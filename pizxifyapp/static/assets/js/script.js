/* ============================================================
   PIZXIFY — Main JavaScript
============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    /* ---- AOS ---- */
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 650,
            once: true,
            offset: 60
        });
    }

    /* ---- Navbar Scroll Effect ---- */
    const navbar = document.querySelector('.navbar-pizxify');

    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    /* ---- Smooth Scroll ---- */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {

        anchor.addEventListener('click', function (e) {

            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                e.preventDefault();

                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }

        });

    });

    /* ---- Counter Animation ---- */
    function animateCounter(el) {

        const target = parseInt(el.dataset.target, 10);
        const duration = 1800;
        const step = target / (duration / 16);

        let current = 0;

        const timer = setInterval(() => {

            current += step;

            if (current >= target) {
                current = target;
                clearInterval(timer);
            }

            el.textContent =
                Math.floor(current).toLocaleString() +
                (el.dataset.suffix || '');

        }, 16);

    }

    const statEls = document.querySelectorAll('.counter');

    if (statEls.length) {

        const observer = new IntersectionObserver((entries, obs) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    obs.unobserve(entry.target);
                }

            });

        }, {
            threshold: 0.4
        });

        statEls.forEach(el => observer.observe(el));

    }

    /* ---- Password Toggle ---- */
    document.querySelectorAll('.btn-toggle-pw').forEach(btn => {

        btn.addEventListener('click', function () {

            const input =
                this.closest('.input-group')
                ?.querySelector('input');

            if (!input) return;

            const isText = input.type === 'text';

            input.type = isText ? 'password' : 'text';

            this.innerHTML = isText
                ? '<i class="bi bi-eye"></i>'
                : '<i class="bi bi-eye-slash"></i>';

        });

    });

    /* ---- User Type Selection ---- */
    const typeCards = document.querySelectorAll('.type-card');
    const typeInput = document.getElementById('userTypeInput');
    const typeDisplay = document.getElementById('typeDisplay');

    if (typeCards.length) {

        typeCards.forEach(card => {

            card.addEventListener('click', function () {

                typeCards.forEach(c =>
                    c.classList.remove('selected')
                );

                this.classList.add('selected');

                const selectedType = this.dataset.type;

                if (typeInput) {
                    typeInput.value = selectedType;
                }

                if (typeDisplay) {
                    typeDisplay.textContent =
                        this.querySelector('span').textContent;
                }

            });

        });

    }

    /* ---- Register Form Validation ---- */
    const registerForm = document.getElementById('registerForm');

    if (registerForm) {

        registerForm.addEventListener('submit', function (e) {

            const password =
                document.querySelector('[name="password"]');

            const confirmPassword =
                document.querySelector('[name="confirm_password"]');

            if (
                password &&
                confirmPassword &&
                password.value !== confirmPassword.value
            ) {

                e.preventDefault();

                alert('Passwords do not match');

                confirmPassword.focus();

                return false;
            }

        });

        const resetBtn = document.getElementById('resetBtn');

        if (resetBtn) {

            resetBtn.addEventListener('click', function () {

                registerForm.reset();

                typeCards.forEach((card, index) => {
                    card.classList.toggle(
                        'selected',
                        index === 0
                    );
                });

                if (typeInput) {
                    typeInput.value = 'photographer';
                }

                if (typeDisplay) {
                    typeDisplay.textContent = 'Photographer';
                }

            });

        }

    }

    /* ---- Dashboard Sidebar ---- */
    const sidebar = document.getElementById('dashSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const sidebarToggle =
        document.getElementById('sidebarToggle');

    function openSidebar() {

        if (sidebar)
            sidebar.classList.add('open');

        if (overlay)
            overlay.classList.add('show');

    }

    function closeSidebar() {

        if (sidebar)
            sidebar.classList.remove('open');

        if (overlay)
            overlay.classList.remove('show');

    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener(
            'click',
            openSidebar
        );
    }

    if (overlay) {
        overlay.addEventListener(
            'click',
            closeSidebar
        );
    }

    /* ---- Auto-dismiss Alerts / Messages after 5 seconds ---- */
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length) {
        setTimeout(() => {
            alerts.forEach(alert => {
                try {
                    if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                        if (bsAlert) {
                            bsAlert.close();
                            return;
                        }
                    }
                } catch (e) {
                    // fallback
                }
                alert.classList.remove('show');
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 300);
            });
        }, 5000);
    }

});