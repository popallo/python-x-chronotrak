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

// Fonction pour activer/désactiver le mode sombre
function toggleDarkMode() {
    const body = document.body;
    const darkModeIcon = document.getElementById('darkModeIcon');
    
    // Basculer la classe dark-mode sur le body
    body.classList.toggle('dark-mode');
    
    // Mettre à jour l'icône
    if (body.classList.contains('dark-mode')) {
        darkModeIcon.classList.replace('fa-sun', 'fa-moon');
        localStorage.setItem('darkMode', 'enabled');
    } else {
        darkModeIcon.classList.replace('fa-moon', 'fa-sun');
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Fonction pour charger la préférence de mode
function loadDarkModePreference() {
    const darkMode = localStorage.getItem('darkMode');
    const darkModeIcon = document.getElementById('darkModeIcon');
    
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
        if (darkModeIcon) {
            darkModeIcon.classList.replace('fa-sun', 'fa-moon');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Chargement des préférences de mode
    loadDarkModePreference();
    
    // Gestionnaire d'événement pour le bouton de basculement
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
    
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