/**
 * Filtres de la liste clients / sociétés
 */

import { initFilters } from '../utils/filters.js';

function initClientFilters() {
    return initFilters({
        formId: 'clientsFilterForm',
        resetBehavior: 'submit'
    });
}

export { initClientFilters };
