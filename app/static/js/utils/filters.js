/**
 * Module générique pour la gestion des filtres
 * Utilisé par les pages de projets et de tâches
 */

/**
 * Initialise le système de filtres pour une page
 * @param {Object} config - Configuration spécifique à la page
 * @param {string} config.formId - ID du formulaire de filtres
 * @param {string} config.resetBehavior - 'submit' ou 'redirect' pour le comportement de reset
 */
function initFilters(config = {}) {
    const {
        formId = 'filtersForm',
        resetBehavior = 'submit'
    } = config;

    // Éléments DOM
    const filtersToggle = document.getElementById('filtersToggle');
    const filtersPanel = document.getElementById('filtersPanel');
    const filtersBody = document.getElementById('filtersBody');
    const filtersIcon = document.getElementById('filtersIcon');
    const filterForm = document.getElementById(formId);
    const resetButton = document.getElementById('resetFilters');
    const activeFiltersList = document.getElementById('activeFilters');

    // Vérifier si les éléments existent
    if (!filtersToggle || !filtersPanel || !filtersBody) {
        console.warn('Éléments de filtres non trouvés, initialisation ignorée');
        return;
    }

    // État local des filtres
    let filtersVisible = !filtersBody.classList.contains('hidden');

    /**
     * Basculer la visibilité du panneau de filtres
     */
    function toggleFilters() {
        filtersVisible = !filtersVisible;

        if (filtersVisible) {
            filtersBody.classList.remove('hidden');
            filtersPanel.classList.remove('collapsed');
            if (filtersIcon) {
                filtersIcon.classList.replace('fa-plus', 'fa-minus');
            }
        } else {
            filtersBody.classList.add('hidden');
            filtersPanel.classList.add('collapsed');
            if (filtersIcon) {
                filtersIcon.classList.replace('fa-minus', 'fa-plus');
            }
        }
    }

    /**
     * Réinitialiser les filtres
     */
    function resetFilters(e) {
        if (e) e.preventDefault();

        if (!filterForm) return;

        // Réinitialiser les champs du formulaire
        filterForm.reset();

        // Réinitialiser les select2 s'ils sont utilisés
        const selects = filterForm.querySelectorAll('select');
        selects.forEach(select => {
            if (window.jQuery && window.jQuery(select).data('select2')) {
                window.jQuery(select).val(null).trigger('change');
            }
        });

        // Appliquer le comportement de reset configuré
        if (resetBehavior === 'redirect') {
            window.location.href = window.location.pathname;
        } else {
            filterForm.submit();
        }
    }

    /**
     * Supprimer un filtre actif
     */
    function removeFilter(e) {
        const filterElement = e.target.closest('.filter-badge');
        if (!filterElement || !filterForm) return;

        const filterType = filterElement.dataset.type;
        const filterValue = filterElement.dataset.value;

        // Trouver et réinitialiser le champ correspondant dans le formulaire
        const formElement = filterForm.elements[filterType];
        if (formElement) {
            // Gérer différents types d'éléments de formulaire
            if (formElement.type === 'select-multiple') {
                // Pour les selects multiples, désélectionner uniquement la valeur spécifique
                for (let option of formElement.options) {
                    if (option.value === filterValue) {
                        option.selected = false;
                    }
                }

                // Mettre à jour select2 si utilisé
                if (window.jQuery && window.jQuery(formElement).data('select2')) {
                    const currentValues = window.jQuery(formElement).val() || [];
                    const newValues = currentValues.filter(val => val !== filterValue);
                    window.jQuery(formElement).val(newValues).trigger('change');
                }
            } else {
                // Pour les autres types de champs
                formElement.value = '';
            }
        }

        // Soumettre le formulaire pour appliquer les changements
        filterForm.submit();
    }

    // Configurer les écouteurs d'événements
    if (filtersToggle) {
        filtersToggle.addEventListener('click', toggleFilters);
    }

    if (resetButton) {
        resetButton.addEventListener('click', resetFilters);
    }

    // Écouteur pour les badges de filtres actifs
    if (activeFiltersList) {
        const removeButtons = activeFiltersList.querySelectorAll('.remove-filter');
        removeButtons.forEach(button => {
            button.addEventListener('click', removeFilter);
        });
    }

    // Si des paramètres de filtre sont dans l'URL, afficher automatiquement le panneau
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.toString() && !filtersVisible) {
        toggleFilters();
    }

    // Retourner l'API publique si nécessaire
    return {
        toggleFilters,
        resetFilters,
        removeFilter
    };
}

export { initFilters };
