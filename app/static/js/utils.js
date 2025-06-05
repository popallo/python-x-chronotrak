// Configuration globale
const CONFIG = {
    csrfToken: window.csrfToken,
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': window.csrfToken
    }
};

// Fonctions utilitaires
const utils = {
    showToast(type, message) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    },

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    },

    handleApiResponse(data) {
        if (data.success) {
            if (data.message) {
                this.showToast('success', data.message);
            }
            return true;
        } else {
            if (data.error === 'The CSRF token has expired.') {
                this.showToast('warning', 'Votre session a expiré. Veuillez recharger la page pour continuer.');
            } else if (data.errors) {
                Object.entries(data.errors).forEach(([field, error]) => {
                    this.showToast('danger', error);
                });
            } else {
                this.showToast('danger', data.error || 'Une erreur est survenue');
            }
            return false;
        }
    },

    async fetchWithCsrf(url, options = {}) {
        const defaultOptions = {
            headers: CONFIG.headers,
            credentials: 'same-origin'
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();

            if (!data.success && data.error === 'The CSRF token has expired.') {
                this.showToast('warning', 'Votre session a expiré. Veuillez recharger la page pour continuer.');
                return { success: false, error: 'CSRF_EXPIRED' };
            }

            return data;
        } catch (error) {
            console.error('Erreur:', error);
            this.showToast('danger', 'Une erreur est survenue');
            return { success: false, error: error.message };
        }
    }
};

// Exporter les utilitaires
export { CONFIG, utils }; 