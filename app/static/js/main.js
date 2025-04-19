/**
 * Script principal - initialise tous les modules
 */

// Import des modules
import { initDarkMode } from './lib/dark-mode.js';
import { autoCloseAlerts, initTooltips, highlightActiveNavItem } from './utils/dom.js';
import { initTasksPage } from './pages/tasks.js';
import { initProjectsPage } from './pages/projects.js';

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Fonctionnalités communes
    initDarkMode();
    autoCloseAlerts();
    initTooltips();
    highlightActiveNavItem();
    
    // Détection de la page courante et initialisation spécifique
    const currentPath = window.location.pathname;
    
    // Page des tâches
    if (currentPath.includes('/tasks/') || currentPath.includes('/my_tasks')) {
        initTasksPage();
    }
    
    // Page des projets
    if (currentPath.includes('/projects/')) {
        initProjectsPage();
    }
});