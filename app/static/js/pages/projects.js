/**
 * Script pour la gestion des projets et du kanban
 */

import { CONFIG, utils } from '../utils.js';

// Initialise le système de drag & drop pour le kanban
function initKanban() {
    const kanbanColumns = document.querySelectorAll('.kanban-column');
    
    if (!kanbanColumns.length) {
        return;
    }
    
    // Configuration de Sortable pour chaque colonne
    kanbanColumns.forEach(column => {
        new Sortable(column.querySelector('.kanban-items'), {
            group: 'tasks',
            animation: 150,
            ghostClass: 'kanban-ghost',
            dragClass: 'kanban-drag',
            onEnd: function(evt) {
                const taskCard = evt.item.querySelector('.kanban-task');
                const taskId = taskCard?.getAttribute('data-task-id');
                const newStatus = evt.to.closest('.kanban-column').getAttribute('data-status');
                
                if (!taskId) {
                    return;
                }
                
                updateTaskStatus(taskId, newStatus);
                updateColumnCounters();
            }
        });
    });
}

// Effectue l'appel AJAX pour mettre à jour le statut d'une tâche
async function updateTaskStatus(taskId, newStatus) {
    try {
        const data = await utils.fetchWithCsrf('/tasks/update_status', {
            method: 'POST',
            body: JSON.stringify({
                task_id: taskId,
                status: newStatus
            })
        });

        if (!data.success) {
            throw new Error(data.error || 'Erreur lors de la mise à jour du statut');
        }
    } catch (error) {
        alert('Une erreur est survenue lors de la mise à jour');
        location.reload();
    }
}

// Met à jour les compteurs de tâches dans chaque colonne
function updateColumnCounters() {
    const columns = document.querySelectorAll('.kanban-column');
    columns.forEach(column => {
        const counter = column.querySelector('.badge');
        const count = column.querySelector('.kanban-items').children.length;
        if (counter) {
            counter.textContent = count;
        }
    });
}

// Initialise la page de projets
function initProjectsPage() {
    initKanban();
}

export { initProjectsPage };