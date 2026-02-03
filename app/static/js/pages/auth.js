/**
 * Module pour l'initialisation des pages d'authentification
 * Gère le mode sombre et Turnstile si nécessaire
 */

import { initDarkMode } from '../lib/dark-mode.js';

/**
 * Initialise une page d'authentification
 * @param {Object} options - Options d'initialisation
 * @param {boolean} options.turnstileEnabled - Si Turnstile est activé
 */
function initAuthPage(options = {}) {
    const { turnstileEnabled = false } = options;

    // Initialiser le mode sombre
    initDarkMode();

    // Initialiser Turnstile si nécessaire
    if (turnstileEnabled) {
        import('../lib/turnstile.js').then(({ initTurnstile }) => {
            initTurnstile();
        });
    }
}

export { initAuthPage };
