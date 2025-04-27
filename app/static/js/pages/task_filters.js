/**
 * Script pour gérer les filtres de tâches
 */

// Fonction pour initialiser le panneau de filtres
function initTaskFilters() {
    console.log("Initialisation des filtres de tâches...");
    
    // Éléments DOM
    const filtersToggle = document.getElementById('filtersToggle');
    const filtersPanel = document.getElementById('filtersPanel');
    const filtersBody = document.getElementById('filtersBody');
    const filtersIcon = document.getElementById('filtersIcon');
    const filterForm = document.getElementById('tasksFilterForm');
    const resetButton = document.getElementById('resetFilters');
    const activeFiltersList = document.getElementById('activeFilters');
    
    // Vérifier si les éléments existent (au cas où le script est chargé sur une autre page)
    if (!filtersToggle || !filtersPanel || !filtersBody) {
        console.log("Éléments de filtre non trouvés sur cette page");
        return;
    }
    
    console.log("Éléments de filtre trouvés, configuration des événements");
    
    // État local des filtres
    let filtersVisible = !filtersBody.classList.contains('hidden');
    
    // Basculer la visibilité du panneau de filtres
    function toggleFilters() {
        console.log("Toggle des filtres appelé");
        filtersVisible = !filtersVisible;
        
        if (filtersVisible) {
            filtersBody.classList.remove('hidden');
            filtersPanel.classList.remove('collapsed');
            filtersIcon.classList.replace('fa-plus', 'fa-minus');
        } else {
            filtersBody.classList.add('hidden');
            filtersPanel.classList.add('collapsed');
            filtersIcon.classList.replace('fa-minus', 'fa-plus');
        }
    }
    
    // Réinitialiser les filtres
    function resetFilters(e) {
        console.log("Réinitialisation des filtres appelée");
        if (e) e.preventDefault();
        
        // Réinitialiser les champs du formulaire
        if (filterForm) {
            console.log("Réinitialisation du formulaire");
            filterForm.reset();
            
            // Réinitialiser les select2 s'ils sont utilisés
            const selects = filterForm.querySelectorAll('select');
            selects.forEach(select => {
                if (window.jQuery && window.jQuery(select).data('select2')) {
                    window.jQuery(select).val(null).trigger('change');
                }
            });
            
            // Rediriger directement vers la page sans paramètres plutôt que de soumettre le formulaire
            // qui pourrait conserver certains paramètres
            window.location.href = window.location.pathname;
        } else {
            console.error("Formulaire non trouvé!");
        }
    }
    
    // Supprimer un filtre actif
    function removeFilter(e) {
        console.log("Suppression d'un filtre");
        const filterElement = e.target.closest('.filter-badge');
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
        console.log("Configuration de l'écouteur pour le toggle");
        filtersToggle.addEventListener('click', toggleFilters);
    }
    
    // Utiliser une approche plus directe pour l'écouteur du bouton de réinitialisation
    if (resetButton) {
        console.log("Configuration de l'écouteur pour le bouton de réinitialisation");
        
        // Supprimer les écouteurs existants (au cas où)
        resetButton.removeEventListener('click', resetFilters);
        
        // Ajouter un nouvel écouteur
        resetButton.addEventListener('click', resetFilters);
        
        // Vérification supplémentaire avec un écouteur direct sur l'élément
        resetButton.onclick = function(e) {
            console.log("Clic direct sur le bouton de réinitialisation");
            resetFilters(e);
        };
    } else {
        console.error("Bouton de réinitialisation non trouvé!");
    }
    
    // Écouteur pour les badges de filtres actifs
    if (activeFiltersList) {
        console.log("Configuration des écouteurs pour les badges de filtres");
        const removeButtons = activeFiltersList.querySelectorAll('.remove-filter');
        removeButtons.forEach(button => {
            button.addEventListener('click', removeFilter);
        });
    }
    
    // Si des paramètres de filtre sont dans l'URL, afficher automatiquement le panneau
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.toString() && !filtersVisible) {
        console.log("Des filtres sont actifs, affichage automatique du panneau");
        toggleFilters();
    }
}

// Initialiser le module au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM chargé, initialisation des filtres de tâches");
    initTaskFilters();
});

// Initialiser le module après un court délai au cas où le DOM n'est pas complètement chargé
setTimeout(function() {
    console.log("Initialisation différée des filtres de tâches");
    initTaskFilters();
}, 500);

export { initTaskFilters };