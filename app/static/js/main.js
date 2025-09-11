/**
 * Script principal - initialise tous les modules
 */

// Import des modules
import { initDarkMode } from './lib/dark-mode.js';
import { autoCloseAlerts, initTooltips, highlightActiveNavItem } from './utils/dom.js';
import { initTasksPage } from './pages/tasks.js';
import { initRegistrationForm } from './pages/user_registration.js';
import { initUserEditForm } from './pages/user_edit.js';
import { initUserManagement } from './pages/user_management.js';
import { initProjectFilters } from './pages/project_filters.js';
import { initProjectFavorites } from './pages/project_favorites.js';
import { initNotificationPreferences } from './pages/notification_preferences.js';
import { initCardCollapse } from './pages/card_collapse.js';
import { initWelcomePage } from './pages/welcome-page.js';
import { initTaskFilters } from './pages/task_filters.js';

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Fonctionnalités communes
    initDarkMode();
    autoCloseAlerts();
    initTooltips();
    highlightActiveNavItem();
    
    // Initialiser la fonctionnalité de collapse des cartes sur toutes les pages
    initCardCollapse();
    
    // Détection de la page courante et initialisation spécifique
    const currentPath = window.location.pathname;
    
    // Page d'accueil (bienvenue)
    if (currentPath === '/') {
        initWelcomePage();
    }
    
    // Page des tâches
    if (currentPath.includes('/tasks/') || currentPath.includes('/my-tasks')) {
        initTasksPage();
    }
    
    // Page des projets individuelles - pas d'initialisation spécifique nécessaire

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
        initProjectFavorites();
    }

    // Page des tâches - liste
    if (currentPath === '/my-tasks') {
        initTaskFilters();
    }

    // Page de profil - préférences de notification
    if (currentPath === '/profile') {
        initNotificationPreferences();
    }
});