/**
 * Module commun pour le drag & drop du kanban
 * Utilisé par my_tasks et project_details
 */

// Initialise le drag & drop pour le kanban
function initKanbanDragDrop() {
    const kanbanColumns = document.querySelectorAll('.kanban-column');
    
    if (!kanbanColumns.length) {
        return;
    }
    
    // Vérifier si Sortable est disponible
    if (typeof Sortable === 'undefined') {
        console.error('SortableJS n\'est pas chargé !');
        return;
    }
    
    // Configuration de Sortable pour chaque colonne
    kanbanColumns.forEach((column) => {
        const kanbanItems = column.querySelector('.kanban-items');
        
        if (!kanbanItems) {
            return;
        }
        
        const status = column.getAttribute('data-status');
        const isDoneColumn = status === 'terminé';

        new Sortable(kanbanItems, {
            group: isDoneColumn ? { name: 'tasks', put: true, pull: false } : 'tasks',
            sort: !isDoneColumn,
            animation: 150,
            ghostClass: 'kanban-ghost',
            dragClass: 'kanban-drag',
            onEnd: function(evt) {
                // Empêcher seulement de sortir de la colonne "terminé" (mais permettre d'y entrer)
                const toStatus = evt.to.closest('.kanban-column').getAttribute('data-status');
                const fromStatus = evt.from.closest('.kanban-column').getAttribute('data-status');
                
                // Bloquer uniquement si on essaie de sortir de "terminé"
                if (fromStatus === 'terminé') {
                    // Recharger pour remettre l'état visuel si quelque chose a bougé par erreur
                    // et éviter toute mise à jour de position/statut côté serveur
                    location.reload();
                    return;
                }

                // evt.item est l'élément .kanban-task lui-même
                const taskCard = evt.item;
                const taskId = taskCard?.getAttribute('data-task-id');
                const newStatus = toStatus;
                const oldStatus = fromStatus;
                
                if (!taskId) {
                    return;
                }
                
                // Si le statut a changé, mettre à jour le statut
                if (newStatus !== oldStatus) {
                    updateTaskStatus(taskId, newStatus);
                }
                
                // Toujours mettre à jour les positions dans la colonne de destination
                updateTaskPositions(evt.to.closest('.kanban-column'));
                updateColumnCounters();
            }
        });
    });
}

// Effectue l'appel AJAX pour mettre à jour le statut d'une tâche
async function updateTaskStatus(taskId, newStatus) {
    try {
        const response = await fetch('/tasks/update_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                task_id: taskId,
                status: newStatus
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Erreur lors de la mise à jour du statut');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors de la mise à jour');
        location.reload();
    }
}

// Met à jour les positions des tâches dans une colonne
async function updateTaskPositions(column) {
    const tasks = column.querySelectorAll('.kanban-task');
    const taskPositions = [];
    
    tasks.forEach((task, index) => {
        const taskId = task.getAttribute('data-task-id');
        if (taskId) {
            taskPositions.push({
                task_id: parseInt(taskId),
                position: index
            });
        }
    });
    
    if (taskPositions.length === 0) {
        return;
    }
    
    try {
        const response = await fetch('/tasks/update_positions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                task_positions: taskPositions
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            console.error('Erreur lors de la mise à jour des positions:', result.error);
        }
    } catch (error) {
        console.error('Erreur lors de la mise à jour des positions:', error);
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

// Initialise le drag & drop quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    initKanbanDragDrop();
});

// Exporter les fonctions pour utilisation dans d'autres modules
window.initKanbanDragDrop = initKanbanDragDrop;
window.updateTaskStatus = updateTaskStatus;
window.updateTaskPositions = updateTaskPositions;
window.updateColumnCounters = updateColumnCounters;
