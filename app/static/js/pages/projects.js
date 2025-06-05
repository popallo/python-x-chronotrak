/**
 * Script pour la gestion des projets et du kanban
 */

import { CONFIG, utils } from '../utils.js';

// Initialise le système de drag & drop pour le kanban
function initKanban() {
    const kanbanTasks = document.querySelectorAll('.kanban-task');
    const kanbanColumns = document.querySelectorAll('.kanban-column');
    
    if (!kanbanTasks.length || !kanbanColumns.length) {
        return; // Sortir si les éléments du kanban n'existent pas
    }
    
    // Configuration du drag and drop
    kanbanTasks.forEach(task => {
        task.setAttribute('draggable', true);
        
        task.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', task.dataset.taskId);
            task.classList.add('dragging');
        });
        
        task.addEventListener('dragend', function() {
            task.classList.remove('dragging');
        });
    });
    
    kanbanColumns.forEach(column => {
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
            column.classList.add('drag-over');
        });
        
        column.addEventListener('dragleave', function() {
            column.classList.remove('drag-over');
        });
        
        column.addEventListener('drop', function(e) {
            e.preventDefault();
            column.classList.remove('drag-over');
            
            const taskId = e.dataTransfer.getData('text/plain');
            const newStatus = column.dataset.status;
            
            updateTaskStatus(taskId, newStatus);
        });
    });
}

// Effectue l'appel AJAX pour mettre à jour le statut d'une tâche
function updateTaskStatus(taskId, newStatus) {
    fetch('/tasks/update_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            task_id: taskId,
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Recharger la page pour refléter les changements
            location.reload();
        } else {
            alert('Erreur lors de la mise à jour du statut: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors de la mise à jour');
    });
}

async function handleStatusUpdate(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    const data = await utils.fetchWithCsrf('/tasks/update_status', {
        method: 'POST',
        body: JSON.stringify({
            task_id: formData.get('task_id'),
            status: formData.get('status'),
            csrf_token: CONFIG.csrfToken
        })
    });

    if (data.success) {
        updateTaskStatus(data.task_id, data.status);
    }
}

// Initialise la page de projets
function initProjectsPage() {
    initKanban();
}

export { initProjectsPage };