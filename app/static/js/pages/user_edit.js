/**
 * Script pour gérer le formulaire d'édition d'utilisateur
 */

function initUserEditForm() {
    const roleSelect = document.getElementById('role-select');
    const clientField = document.getElementById('client-field');
    
    if (!roleSelect || !clientField) return;
    
    // Fonction pour afficher/masquer le champ clients en fonction du rôle
    function toggleClientField() {
        if (roleSelect.value === 'client') {
            clientField.style.display = 'block';
        } else {
            clientField.style.display = 'none';
        }
    }
    
    // Initialiser l'état du champ client
    toggleClientField();
    
    // Configurer l'écouteur d'événements
    roleSelect.addEventListener('change', toggleClientField);
}

// Initialiser le formulaire au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initUserEditForm();
});

export { initUserEditForm };