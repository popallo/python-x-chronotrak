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

// Variables globales pour le filtrage
let kanbanSearchTimeout = null;
let originalTaskData = new Map();

// Fonction pour extraire les données de recherche d'une tâche
function extractTaskSearchData(taskElement) {
    const title = taskElement.querySelector('.kanban-task-title')?.textContent?.trim() || '';
    const meta = taskElement.querySelector('.kanban-task-meta')?.textContent?.trim() || '';
    const time = taskElement.querySelector('.kanban-task-time')?.textContent?.trim() || '';

    return {
        title: title.toLowerCase(),
        meta: meta.toLowerCase(),
        time: time.toLowerCase(),
        fullText: (title + ' ' + meta + ' ' + time).toLowerCase()
    };
}

// Fonction pour sauvegarder les données originales des tâches
function saveOriginalTaskData() {
    const tasks = document.querySelectorAll('.kanban-task');
    tasks.forEach(task => {
        const taskId = task.getAttribute('data-task-id');
        if (taskId && !originalTaskData.has(taskId)) {
            originalTaskData.set(taskId, extractTaskSearchData(task));
        }
    });
}

// Fonction pour filtrer les tâches
function filterKanbanTasks(searchTerm) {
    if (!searchTerm || searchTerm.trim() === '') {
        // Afficher toutes les tâches
        document.querySelectorAll('.kanban-task').forEach(task => {
            task.style.display = 'block';
            task.classList.remove('kanban-task-filtered');
        });

        // Masquer l'info de recherche
        document.getElementById('kanban-search-info').style.display = 'none';

        // Mettre à jour les compteurs
        updateColumnCounters();
        return;
    }

    const searchLower = searchTerm.toLowerCase().trim();
    let visibleCount = 0;

    // Filtrer les tâches
    document.querySelectorAll('.kanban-task').forEach(task => {
        const taskId = task.getAttribute('data-task-id');
        const taskData = originalTaskData.get(taskId);

        if (!taskData) {
            task.style.display = 'none';
            task.classList.add('kanban-task-filtered');
            return;
        }

        const matches = taskData.fullText.includes(searchLower) ||
                       taskData.title.includes(searchLower) ||
                       taskData.meta.includes(searchLower);

        if (matches) {
            task.style.display = 'block';
            task.classList.remove('kanban-task-filtered');
            visibleCount++;
        } else {
            task.style.display = 'none';
            task.classList.add('kanban-task-filtered');
        }
    });

    // Afficher l'info de recherche
    const searchInfo = document.getElementById('kanban-search-info');
    const searchCount = document.getElementById('kanban-search-count');

    if (visibleCount > 0) {
        searchInfo.style.display = 'block';
        searchCount.textContent = visibleCount;
    } else {
        searchInfo.style.display = 'block';
        searchCount.textContent = '0';
    }

    // Mettre à jour les compteurs des colonnes
    updateColumnCounters();
}

// Fonction pour mettre à jour les compteurs des colonnes
function updateColumnCounters() {
    document.querySelectorAll('.kanban-column').forEach(column => {
        const visibleTasks = column.querySelectorAll('.kanban-task:not([style*="display: none"])');
        const badge = column.querySelector('.kanban-title .badge');
        if (badge) {
            badge.textContent = visibleTasks.length;
        }
    });
}

// Fonction pour effacer la recherche
function clearKanbanSearch() {
    const searchInput = document.getElementById('kanban-search');
    if (searchInput) {
        searchInput.value = '';
        filterKanbanTasks('');
    }
}

// Fonction pour initialiser le système de recherche
function initKanbanSearch() {
    const searchInput = document.getElementById('kanban-search');
    const clearButton = document.getElementById('kanban-clear-search');

    if (!searchInput) {
        return; // Pas de kanban sur cette page
    }

    // Sauvegarder les données originales
    saveOriginalTaskData();

    // Événement de recherche en temps réel
    searchInput.addEventListener('input', function() {
        clearTimeout(kanbanSearchTimeout);
        kanbanSearchTimeout = setTimeout(() => {
            filterKanbanTasks(this.value);
        }, 150); // Délai de 150ms pour éviter trop de recherches
    });

    // Bouton pour effacer la recherche
    if (clearButton) {
        clearButton.addEventListener('click', clearKanbanSearch);
    }

    // Raccourci clavier pour effacer (Escape)
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            clearKanbanSearch();
            this.blur(); // Retirer le focus
        }
    });
}

// Initialisation du kanban
function initKanban() {
    // Vérifier que le token CSRF est disponible
    if (!window.csrfToken) {
        console.warn('Token CSRF non trouvé pour le kanban');
    }

    // Initialiser le système de recherche
    initKanbanSearch();
}

// Auto-initialisation si le DOM est déjà chargé
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initKanban);
} else {
    initKanban();
}
