/**
 * Utilitaires pour la manipulation du DOM
 */

// Ferme automatiquement les alertes après un délai
function autoCloseAlerts(delay = 5000, excludeClasses = ['alert-warning', 'alert-danger', 'no-auto-close']) {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            // Ne pas fermer automatiquement les alertes exclues
            if (!excludeClasses.some(cls => alert.classList.contains(cls))) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, delay);
}

// Active les tooltips Bootstrap
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Met en surbrillance l'élément de navigation actif
function highlightActiveNavItem() {
    const currentUrl = window.location.pathname;
    
    document.querySelectorAll('.nav-link').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentUrl.includes(href) && href !== '/') {
            link.classList.add('active');
        }
    });
}

export { autoCloseAlerts, initTooltips, highlightActiveNavItem };