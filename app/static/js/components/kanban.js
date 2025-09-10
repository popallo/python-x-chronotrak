/**
 * Kanban Board Component
 * Gère les actions rapides sur les tâches du kanban
 */

// Fonction pour changer le statut d'une tâche
async function changeTaskStatus(taskSlug, newStatus) {
    try {
        const response = await fetch(`/tasks/${taskSlug}/update_status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                status: newStatus
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Recharger la page pour voir les changements
            window.location.reload();
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    }
}

// Fonction pour archiver une tâche
async function archiveTask(taskSlug) {
    if (!confirm('Êtes-vous sûr de vouloir archiver cette tâche ?')) {
        return;
    }
    
    try {
        const response = await fetch(`/tasks/${taskSlug}/archive`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Recharger la page pour voir les changements
            window.location.reload();
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    }
}

// Initialisation du kanban
function initKanban() {
    // Vérifier que le token CSRF est disponible
    if (!window.csrfToken) {
        console.warn('Token CSRF non trouvé pour le kanban');
    }
}

// Auto-initialisation si le DOM est déjà chargé
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initKanban);
} else {
    initKanban();
}
