/**
 * Filtres de la liste clients / sociétés
 */

import { initFilters } from '../utils/filters.js';

function initClientFilters() {
    return initFilters({
        formId: 'clientsFilterForm',
        resetBehavior: 'submit',
        // Ne pas ouvrir le panneau pour un simple filtre rapide (quick) / tri / page
        autoOpenIgnoreParams: ['quick', 'sort_by', 'page', 'sort_order'],
    });
}

export { initClientFilters };
