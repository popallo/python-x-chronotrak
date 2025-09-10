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
                // evt.item est l'élément .kanban-task lui-même
                const taskCard = evt.item;
                const taskId = taskCard?.getAttribute('data-task-id');
                const newStatus = evt.to.closest('.kanban-column').getAttribute('data-status');
                const oldStatus = evt.from.closest('.kanban-column').getAttribute('data-status');
                
                if (!taskId) {
                    return;
                }
                
                // Si le statut a changé, mettre à jour le statut
                if (newStatus !== oldStatus) {
                    updateTaskStatus(taskId, newStatus);
                }
                
                // Toujours mettre à jour les positions
                updateTaskPositions(evt.to.closest('.kanban-column'));
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
        const data = await utils.fetchWithCsrf('/tasks/update_positions', {
            method: 'POST',
            body: JSON.stringify({
                task_positions: taskPositions
            })
        });
        
        if (!data.success) {
            console.error('Erreur lors de la mise à jour des positions:', data.error);
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

// Initialise la page de projets
function initProjectsPage() {
    initKanban();
}

export { initProjectsPage };