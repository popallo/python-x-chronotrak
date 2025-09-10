// Fonction pour activer/désactiver le mode sombre
function toggleDarkMode() {
    const html = document.documentElement;
    const darkModeIcon = document.getElementById('darkModeIcon');
    
    // Basculer la classe dark-mode sur html
    html.classList.toggle('dark-mode');
    
    // S'assurer que theme-loaded est toujours présent
    html.classList.add('theme-loaded');
    
    // Mettre à jour l'icône et l'attribut Bootstrap
    if (html.classList.contains('dark-mode')) {
        html.setAttribute('data-bs-theme', 'dark');
        if (darkModeIcon) {
            darkModeIcon.classList.replace('fa-sun', 'fa-moon');
        }
        localStorage.setItem('darkMode', 'enabled');
    } else {
        html.setAttribute('data-bs-theme', 'light');
        if (darkModeIcon) {
            darkModeIcon.classList.replace('fa-moon', 'fa-sun');
        }
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Fonction pour charger la préférence de mode
function loadDarkModePreference() {
    const darkMode = localStorage.getItem('darkMode');
    const darkModeIcon = document.getElementById('darkModeIcon');
    
    if (darkMode === 'enabled') {
        document.documentElement.classList.add('dark-mode');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        document.documentElement.classList.add('theme-loaded');
        
        if (darkModeIcon) {
            darkModeIcon.classList.replace('fa-sun', 'fa-moon');
        }
    } else {
        document.documentElement.setAttribute('data-bs-theme', 'light');
        // S'assurer que le thème est marqué comme chargé même en mode clair
        document.documentElement.classList.add('theme-loaded');
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