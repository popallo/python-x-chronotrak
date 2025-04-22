/**
 * Script principal - initialise tous les modules
 */

// Import des modules
import { initDarkMode } from './lib/dark-mode.js';
import { autoCloseAlerts, initTooltips, highlightActiveNavItem } from './utils/dom.js';
import { initTasksPage } from './pages/tasks.js';
import { initProjectsPage } from './pages/projects.js';
import { initRegistrationForm } from './pages/user_registration.js';
import { initUserEditForm } from './pages/user_edit.js';
import { initUserManagement } from './pages/user_management.js';
import { initProjectFilters } from './pages/project_filters.js';

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

    // Page d'inscription utilisateur
    if (currentPath.includes('/register')) {
        initRegistrationForm();
    }

    // Page d'édition utilisateur
    if (currentPath.includes('/users/') && currentPath.includes('/edit')) {
        initUserEditForm();
    }

    // Page de gestion des utilisateurs
    if (currentPath.includes('/users') && !currentPath.includes('/edit')) {
        initUserManagement();
    }

    // Page des projets - liste
    if (currentPath === '/projects') {
        initProjectFilters();
    }
});