/**
 * Script pour gérer les formulaires d'inscription utilisateur
 */

function initRegistrationForm() {
    const roleSelect = document.getElementById('role-select');
    const clientField = document.querySelector('.client-field');
    
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

export { initRegistrationForm };