/**
 * Script pour gérer les filtres de tâches
 * Utilise le module générique de filtres
 */

import { initFilters } from '../utils/filters.js';

// Fonction pour initialiser le panneau de filtres des tâches
function initTaskFilters() {
    return initFilters({
        formId: 'tasksFilterForm',
        resetBehavior: 'redirect'
    });
}

// Initialiser le module au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initTaskFilters();
});

export { initTaskFilters };