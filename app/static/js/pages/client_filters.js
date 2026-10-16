/**
 * Filtres de la liste clients / sociétés
 */

import { initFilters } from '../utils/filters.js';

/**
 * Garantit que le panneau avancé reste fermé quand un filtre rapide (tuile) est actif.
 */
function ensureClosedForQuickFilter() {
    const quick = new URLSearchParams(window.location.search).get('quick');
    if (!quick || quick === 'all') {
        return;
    }

    const filtersPanel = document.getElementById('filtersPanel');
    const filtersBody = document.getElementById('filtersBody');
    const filtersIcon = document.getElementById('filtersIcon');
    if (!filtersPanel || !filtersBody) {
        return;
    }

    filtersBody.classList.add('hidden');
    filtersBody.style.display = 'none';
    filtersPanel.classList.add('collapsed');
    if (filtersIcon) {
        filtersIcon.classList.remove('fa-minus');
        filtersIcon.classList.add('fa-plus');
    }
}

function initClientFilters() {
    const api = initFilters({
        formId: 'clientsFilterForm',
        resetBehavior: 'submit',
    });
    ensureClosedForQuickFilter();
    return api;
}

export { initClientFilters };
