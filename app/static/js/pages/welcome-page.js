/**
 * Script spécifique à la page d'accueil
 */

import { toggleDarkMode, loadDarkModePreference } from '../lib/dark-mode.js';

// Fonction pour initialiser le bouton dark mode sur la page de bienvenue
function initWelcomeDarkMode() {
    // Charger la préférence de thème actuelle
    loadDarkModePreference();
    
    // Mettre à jour l'icône en fonction du mode actuel
    const darkModeIcon = document.getElementById('darkModeIcon');
    if (darkModeIcon) {
        if (document.documentElement.classList.contains('dark-mode')) {
            darkModeIcon.classList.replace('fa-sun', 'fa-moon');
        } else {
            darkModeIcon.classList.replace('fa-moon', 'fa-sun');
        }
    }
    
    // Ajouter l'écouteur d'événement au bouton
    const welcomeDarkModeToggle = document.getElementById('welcomeDarkModeToggle');
    if (welcomeDarkModeToggle) {
        welcomeDarkModeToggle.addEventListener('click', function() {
            toggleDarkMode();
        });
    }
}

// Fonction pour égaliser la hauteur des cartes de caractéristiques
function equalizeCardHeights() {
    const featureCards = document.querySelectorAll('.features-card .card-body');
    if (featureCards.length < 2) return; // Ne rien faire s'il n'y a pas assez de cartes
    
    // Réinitialiser les hauteurs en cas de redimensionnement
    featureCards.forEach(card => {
        card.style.height = 'auto';
    });
    
    // Calculer la hauteur maximale
    let maxHeight = 0;
    featureCards.forEach(card => {
        const height = card.offsetHeight;
        if (height > maxHeight) {
            maxHeight = height;
        }
    });
    
    // Appliquer la hauteur maximale à toutes les cartes
    featureCards.forEach(card => {
        card.style.height = `${maxHeight}px`;
    });
}

// Fonction pour initialiser la page d'accueil
function initWelcomePage() {
    // Initialiser le bouton dark mode
    initWelcomeDarkMode();
    
    // Égaliser la hauteur des cartes
    equalizeCardHeights();
    
    // Recalculer en cas de redimensionnement
    window.addEventListener('resize', function() {
        // Utiliser un debounce pour éviter trop d'appels pendant le redimensionnement
        clearTimeout(window.resizeTimer);
        window.resizeTimer = setTimeout(equalizeCardHeights, 250);
    });
}

export { initWelcomePage };