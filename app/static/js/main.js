// Fermeture automatique des alertes après 5 secondes
document.addEventListener('DOMContentLoaded', function() {
    // Fermeture automatique des alertes après 5 secondes
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-warning):not(.alert-danger)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Activer tous les tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Mettre en surbrillance l'élément de navigation actif
    var currentUrl = window.location.pathname;
    
    document.querySelectorAll('.nav-link').forEach(function(link) {
        var href = link.getAttribute('href');
        if (href && currentUrl.includes(href) && href !== '/') {
            link.classList.add('active');
        }
    });
});