/**
 * Initialise et gère Cloudflare Turnstile
 */
export function initTurnstile() {
    if (typeof turnstile === 'undefined') {
        console.warn('Turnstile is not loaded');
        return;
    }

    // Récupérer tous les éléments avec la classe turnstile-container
    const containers = document.querySelectorAll('.turnstile-container');
    
    containers.forEach(container => {
        const siteKey = container.dataset.siteKey;
        if (!siteKey) {
            console.error('Turnstile site key is missing');
            return;
        }

        // Rendre le conteneur visible
        container.style.display = 'block';

        // Initialiser Turnstile
        turnstile.render(container, {
            sitekey: siteKey,
            theme: 'light',
            callback: function(token) {
                // Ajouter le token au formulaire parent
                const form = container.closest('form');
                if (form) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'cf-turnstile-response';
                    input.value = token;
                    form.appendChild(input);
                }
            }
        });
    });
} 