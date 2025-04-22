/**
 * Script pour gérer la liste des utilisateurs et les actions associées
 */

function initUserManagement() {
    // Sélectionner tous les boutons de suppression
    const deleteButtons = document.querySelectorAll('.delete-user-btn');
    const modal = document.getElementById('deleteUserModal');
    
    if (!deleteButtons.length || !modal) return;
    
    // Initialiser la modale Bootstrap
    const deleteModal = new bootstrap.Modal(modal);
    
    // Ajouter les écouteurs d'événements aux boutons de suppression
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Récupérer les données de l'utilisateur
            const userId = this.dataset.userId;
            const userName = this.dataset.userName;
            const isClient = this.dataset.isClient === 'true';
            const clientCount = parseInt(this.dataset.clientCount);
            
            // Mettre à jour le contenu de la modale
            document.getElementById('userName').textContent = userName;
            
            // Afficher l'avertissement si c'est un client avec des clients associés
            const clientWarning = document.getElementById('clientWarning');
            if (isClient && clientCount > 0) {
                document.getElementById('clientCount').textContent = clientCount;
                document.getElementById('clientPlural').textContent = clientCount > 1 ? 's' : '';
                clientWarning.style.display = 'block';
            } else {
                clientWarning.style.display = 'none';
            }
            
            // Mettre à jour l'action du formulaire
            const form = document.getElementById('deleteUserForm');
            form.action = `/users/${userId}/delete`;
            
            // Afficher la modale
            deleteModal.show();
        });
    });
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initUserManagement();
});

export { initUserManagement };