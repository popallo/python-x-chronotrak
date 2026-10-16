/**
 * Filtres de la liste clients / sociétés
 */

import { initFilters } from '../utils/filters.js';

function initClientFilters() {
    return initFilters({
        formId: 'clientsFilterForm',
        resetBehavior: 'submit',
        // Ouverture gérée uniquement par le template (panel_filters_open).
        // Un filtre rapide (tuiles) ne doit jamais dérouler le panneau.
        autoOpen: false,
    });
}

export { initClientFilters };
