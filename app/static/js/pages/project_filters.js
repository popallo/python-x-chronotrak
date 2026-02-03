/**
 * Script pour gérer les filtres de projets
 * Utilise le module générique de filtres
 */

import { initFilters } from '../utils/filters.js';

// Fonction pour initialiser le panneau de filtres des projets
function initProjectFilters() {
    return initFilters({
        formId: 'projectsFilterForm',
        resetBehavior: 'submit'
    });
}

// Initialiser le module
document.addEventListener('DOMContentLoaded', function() {
    initProjectFilters();
});

export { initProjectFilters };
