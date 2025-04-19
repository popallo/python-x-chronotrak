/**
 * Module de gestion du mode sombre
 */

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

// Initialisation des gestionnaires d'événements pour le dark mode
function initDarkMode() {
    // Chargement des préférences de mode
    loadDarkModePreference();
    
    // Gestionnaire d'événement pour le bouton de basculement
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
}

// Exporter les fonctions
export { toggleDarkMode, loadDarkModePreference, initDarkMode };