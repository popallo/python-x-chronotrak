/**
 * Gestion de l'archivage des tâches via AJAX
 */

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales pour stocker les données de la tâche
    let currentTaskId = null;
    let currentTaskSlug = null;
    let currentTaskTitle = null;

    // Gestion des boutons d'archivage
    document.addEventListener('click', function(e) {
        if (e.target.closest('.archive-task-btn')) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            const btn = e.target.closest('.archive-task-btn');
            currentTaskId = btn.dataset.taskId;
            currentTaskSlug = btn.dataset.taskSlug;
            currentTaskTitle = btn.dataset.taskTitle;

            // Mettre à jour le titre dans le modal
            document.getElementById('archiveTaskTitle').textContent = currentTaskTitle;

            // Afficher le modal
            const modal = new bootstrap.Modal(document.getElementById('archiveTaskModal'));
            modal.show();

            return false;
        }

        if (e.target.closest('.unarchive-task-btn')) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            const btn = e.target.closest('.unarchive-task-btn');
            currentTaskId = btn.dataset.taskId;
            currentTaskSlug = btn.dataset.taskSlug;
            currentTaskTitle = btn.dataset.taskTitle;

            // Mettre à jour le titre dans le modal
            document.getElementById('unarchiveTaskTitle').textContent = currentTaskTitle;

            // Afficher le modal
            const modal = new bootstrap.Modal(document.getElementById('unarchiveTaskModal'));
            modal.show();

            return false;
        }
    });

    // Confirmation d'archivage
    document.getElementById('confirmArchiveBtn')?.addEventListener('click', function() {
        if (currentTaskSlug) {
            archiveTask(currentTaskSlug);
        }
    });

    // Confirmation de désarchivage
    document.getElementById('confirmUnarchiveBtn')?.addEventListener('click', function() {
        if (currentTaskSlug) {
            unarchiveTask(currentTaskSlug);
        }
    });

    // Fonction d'archivage
    async function archiveTask(taskSlug) {
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
                // Fermer le modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('archiveTaskModal'));
                modal.hide();

                // Afficher un message de succès
                showNotification('Tâche archivée avec succès', 'success');

                // Supprimer ou masquer l'élément de la page
                removeTaskFromPage(currentTaskId);

                // Mettre à jour les compteurs sans recharger la page
                updateCounters();
            } else {
                showNotification(result.error || 'Erreur lors de l\'archivage', 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            showNotification('Erreur lors de l\'archivage', 'error');
        }
    }

    // Fonction de désarchivage
    async function unarchiveTask(taskSlug) {
        try {
            const response = await fetch(`/tasks/${taskSlug}/unarchive`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                }
            });

            const result = await response.json();

            if (result.success) {
                // Fermer le modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('unarchiveTaskModal'));
                modal.hide();

                // Afficher un message de succès
                showNotification('Tâche désarchivée avec succès', 'success');

                // Supprimer ou masquer l'élément de la page
                removeTaskFromPage(currentTaskId);

                // Mettre à jour les compteurs sans recharger la page
                updateCounters();
            } else {
                showNotification(result.error || 'Erreur lors du désarchivage', 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            showNotification('Erreur lors du désarchivage', 'error');
        }
    }

    // Fonction pour supprimer une tâche de la page
    function removeTaskFromPage(taskId) {
        // Chercher l'élément de la tâche dans différents contextes
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`) ||
                          document.querySelector(`.kanban-task[data-task-id="${taskId}"]`) ||
                          document.querySelector(`.list-group-item:has([data-task-id="${taskId}"])`);

        if (taskElement) {
            // Animation de disparition
            taskElement.style.transition = 'opacity 0.3s ease';
            taskElement.style.opacity = '0';

            setTimeout(() => {
                taskElement.remove();
            }, 300);
        }
    }

    // Fonction pour mettre à jour les compteurs
    function updateCounters() {
        // Mettre à jour le compteur de la colonne "Terminé" dans le kanban
        const doneColumn = document.querySelector('.kanban-column[data-status="terminé"] .kanban-title .badge');
        if (doneColumn) {
            const currentCount = parseInt(doneColumn.textContent) || 0;
            doneColumn.textContent = Math.max(0, currentCount - 1);
        }

        // Mettre à jour le compteur dans "Mes tâches" si présent
        const completedBadge = document.querySelector('.card-header:has(.fa-check) .badge');
        if (completedBadge) {
            const currentCount = parseInt(completedBadge.textContent) || 0;
            completedBadge.textContent = Math.max(0, currentCount - 1);
        }

        // Mettre à jour le compteur total des archives si présent
        const archivesBadge = document.querySelector('.card-header:has(.fa-archive) .badge');
        if (archivesBadge) {
            const currentCount = parseInt(archivesBadge.textContent) || 0;
            archivesBadge.textContent = currentCount + 1;
        }
    }

    // Fonction pour afficher des notifications
    function showNotification(message, type = 'info') {
        // Créer une alerte Bootstrap
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(alertDiv);

        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
});
