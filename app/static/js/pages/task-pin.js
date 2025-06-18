import { CONFIG, utils } from '../utils.js';

// Fonction pour récupérer le nom du projet de manière robuste
function getProjectName() {
    // Essayer plusieurs sélecteurs pour trouver le nom du projet
    const projectNameElement = document.querySelector('.project-name') || 
                              document.querySelector('a[href*="/projects/"]') ||
                              document.querySelector('.d-flex.align-items-center a[href*="/projects/"]');
    
    return projectNameElement?.textContent?.trim() || '';
}

// Fonction pour extraire le slug de la tâche depuis l'URL
function getTaskSlug() {
    // L'URL peut être /task/slug ou /tasks/slug
    const pathParts = window.location.pathname.split('/');
    // Chercher le slug après /task/ ou /tasks/
    for (let i = 0; i < pathParts.length - 1; i++) {
        if (pathParts[i] === 'task' || pathParts[i] === 'tasks') {
            return pathParts[i + 1];
        }
    }
    // Fallback: prendre le dernier segment de l'URL
    return pathParts[pathParts.length - 1];
}

// Fonction pour mettre à jour le menu de navigation
function updateNavigationMenu(data) {
    const dropdownMenu = document.querySelector('#pinnedTasksDropdown + .dropdown-menu');
    if (!dropdownMenu) return;

    const taskItem = document.querySelector(`.dropdown-item[href*="${window.location.pathname}"]`);
    const noTasksMessage = dropdownMenu.querySelector('.dropdown-item-text.text-muted');
    const separator = dropdownMenu.querySelector('.dropdown-divider');
    const viewAllLink = dropdownMenu.querySelector('.dropdown-item[href*="my_tasks"]');
    
    if (data.is_pinned) {
        // Supprimer le message "aucune tâche épinglée" s'il existe
        if (noTasksMessage) {
            noTasksMessage.closest('li').remove();
        }
        
        // Si la tâche n'est pas déjà dans le menu, l'ajouter
        if (!taskItem) {
            const newItem = document.createElement('li');
            newItem.innerHTML = `
                <a class="dropdown-item d-flex justify-content-between align-items-center" href="${window.location.pathname}">
                    <div class="d-flex flex-column">
                        <span class="text-truncate" style="max-width: 200px;">${document.title}</span>
                        <small class="text-muted">${getProjectName()}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-${document.querySelector('.status-btn.active')?.dataset.status || 'info'}">${document.querySelector('.status-btn.active')?.dataset.status || ''}</span>
                        <form action="/task/${getTaskSlug()}/toggle_pin" method="POST" class="d-inline menu-pin-form">
                            <button type="submit" class="btn btn-link btn-sm text-muted p-0" title="Désépingler">
                                <i class="fas fa-thumbtack"></i>
                            </button>
                        </form>
                    </div>
                </a>
            </li>
            `;
            
            // Insérer avant le séparateur ou à la fin
            if (separator) {
                dropdownMenu.insertBefore(newItem, separator);
            } else {
                dropdownMenu.appendChild(newItem);
            }
            
            // Ajouter le gestionnaire d'événements au nouveau formulaire
            const newForm = newItem.querySelector('.menu-pin-form');
            if (newForm) {
                setupPinForm(newForm);
            }
        }
    } else {
        // Si la tâche est dans le menu, la supprimer
        if (taskItem) {
            taskItem.closest('li').remove();
        }
        
        // Vérifier s'il reste des tâches épinglées
        const remainingTasks = dropdownMenu.querySelectorAll('.dropdown-item:not([href*="my_tasks"])');
        if (remainingTasks.length === 0) {
            // Supprimer le séparateur et le lien "Voir toutes mes tâches"
            if (separator) separator.closest('li').remove();
            if (viewAllLink) viewAllLink.closest('li').remove();
            
            // Ajouter le message "aucune tâche épinglée"
            const noTasksItem = document.createElement('li');
            noTasksItem.innerHTML = '<span class="dropdown-item-text text-muted">Aucune tâche épinglée</span>';
            dropdownMenu.appendChild(noTasksItem);
        }
    }
    
    // Mettre à jour le compteur dans le menu déroulant
    updatePinnedCount();
}

// Fonction pour configurer un formulaire d'épinglage
function setupPinForm(form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const button = form.querySelector('button');
        button.disabled = true;
        
        // Récupérer le token CSRF depuis window.csrfToken ou depuis un élément meta
        const csrfToken = window.csrfToken || document.querySelector('meta[name="csrf-token"]')?.content;
        
        fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updatePinInterface(data);
            } else {
                showToast('danger', data.error || 'Une erreur est survenue');
            }
        })
        .catch(error => {
            console.error('Erreur lors de l\'épinglage/désépinglage:', error);
            showToast('danger', 'Une erreur est survenue lors de l\'épinglage/désépinglage');
        })
        .finally(() => {
            button.disabled = false;
        });
    });
}

// Fonction pour mettre à jour l'interface après un changement d'état d'épinglage
function updatePinInterface(data) {
    // Mettre à jour le bouton dans la barre d'outils
    const toolbarButton = document.querySelector('.action-toolbar .menu-pin-form button');
    if (toolbarButton) {
        // Attendre que l'icône de chargement soit remplacée par l'icône d'épinglage
        const checkIcon = setInterval(() => {
            const icon = toolbarButton.querySelector('i.fa-thumbtack');
            if (icon) {
                clearInterval(checkIcon);
                
                // Gérer la classe text-warning
                if (data.is_pinned) {
                    icon.classList.add('text-warning');
                } else {
                    icon.classList.remove('text-warning');
                }
                
                // Mettre à jour le tooltip
                const tooltipText = data.is_pinned ? 'Désépingler la tâche' : 'Épingler la tâche';
                toolbarButton.setAttribute('data-bs-original-title', tooltipText);
                toolbarButton.setAttribute('title', tooltipText);
            }
        }, 50);
        
        // Arrêter la vérification après 2 secondes au cas où
        setTimeout(() => clearInterval(checkIcon), 2000);
    }

    // Mettre à jour le menu de navigation uniquement s'il existe
    const dropdownMenu = document.querySelector('#pinnedTasksDropdown + .dropdown-menu');
    if (dropdownMenu) {
        // Trouver l'élément du menu qui correspond à la tâche actuelle
        // Utiliser l'ID de la tâche si disponible, sinon utiliser le pathname
        let taskItem;
        if (data.task_id) {
            taskItem = dropdownMenu.querySelector(`li[data-task-id="${data.task_id}"]`);
        }
        if (!taskItem) {
            taskItem = dropdownMenu.querySelector(`.dropdown-item[href="${window.location.pathname}"]`)?.closest('li');
        }
        const noTasksMessage = dropdownMenu.querySelector('.dropdown-item-text');
        const separator = dropdownMenu.querySelector('.dropdown-divider');
        const viewAllLink = dropdownMenu.querySelector('.dropdown-item.text-center');

        if (data.is_pinned) {
            // Ajouter la tâche au menu
            if (taskItem) {
                taskItem.remove();
            }
            if (noTasksMessage) {
                noTasksMessage.closest('li').remove();
            }

            const newTaskItem = document.createElement('li');
            newTaskItem.setAttribute('data-task-id', data.task_id);
            
            // Récupérer le statut actuel
            const statusBtn = document.querySelector('.status-btn.btn-warning, .status-btn.btn-info, .status-btn.btn-success');
            const status = statusBtn?.dataset.status || 'à faire';
            const statusColor = statusBtn?.classList.contains('btn-info') ? 'info' : 
                              statusBtn?.classList.contains('btn-warning') ? 'warning' : 
                              statusBtn?.classList.contains('btn-success') ? 'success' : 'info';

            newTaskItem.innerHTML = `
                <a class="dropdown-item d-flex justify-content-between align-items-center" href="${window.location.pathname}">
                    <div class="d-flex flex-column">
                        <span class="text-truncate" style="max-width: 200px;">${document.title}</span>
                        <small class="text-muted">${getProjectName()}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-${statusColor}">${status}</span>
                        <form action="/task/${getTaskSlug()}/toggle_pin" method="POST" class="d-inline menu-pin-form">
                            <button type="submit" class="btn btn-link btn-sm text-muted p-0" title="Désépingler">
                                <i class="fas fa-thumbtack"></i>
                            </button>
                        </form>
                    </div>
                </a>
            `;

            // Insérer avant le séparateur ou le lien "Voir toutes mes tâches"
            if (separator) {
                separator.parentNode.insertBefore(newTaskItem, separator);
            } else if (viewAllLink) {
                viewAllLink.parentNode.insertBefore(newTaskItem, viewAllLink);
            } else {
                dropdownMenu.appendChild(newTaskItem);
            }

            // Ajouter le gestionnaire d'événements au nouveau formulaire
            const newForm = newTaskItem.querySelector('.menu-pin-form');
            if (newForm) {
                setupPinForm(newForm);
            }
        } else {
            // Supprimer la tâche du menu
            if (taskItem) {
                taskItem.remove();
            }
        }
        
        // Mettre à jour le compteur de manière robuste
        updatePinnedCount();
    }

    // Afficher la notification
    showToast('success', data.message);
}

// Fonction pour mettre à jour le compteur des tâches épinglées
function updatePinnedCount() {
    const dropdownMenu = document.querySelector('#pinnedTasksDropdown + .dropdown-menu');
    if (!dropdownMenu) return;
    
    // Compter les tâches épinglées (exclure les éléments spéciaux)
    const pinnedTasks = dropdownMenu.querySelectorAll('li[data-task-id]');
    const count = pinnedTasks.length;
    
    const badge = document.querySelector('#pinnedTasksDropdown .badge');
    
    if (count > 0) {
        if (badge) {
            badge.textContent = count;
        } else {
            const newBadge = document.createElement('span');
            newBadge.className = 'badge bg-info';
            newBadge.textContent = count;
            document.querySelector('#pinnedTasksDropdown').appendChild(newBadge);
        }
    } else {
        if (badge) {
            badge.remove();
        }
    }
    
    // Gérer l'affichage du message "aucune tâche épinglée"
    const noTasksMessage = dropdownMenu.querySelector('.dropdown-item-text.text-muted');
    const separator = dropdownMenu.querySelector('.dropdown-divider');
    const viewAllLink = dropdownMenu.querySelector('.dropdown-item.text-center');
    
    if (count === 0) {
        // Supprimer le séparateur et le lien "Voir toutes mes tâches"
        if (separator) separator.closest('li').remove();
        if (viewAllLink) viewAllLink.closest('li').remove();
        
        // Ajouter le message "aucune tâche épinglée" s'il n'existe pas déjà
        if (!noTasksMessage) {
            const noTasksItem = document.createElement('li');
            noTasksItem.innerHTML = '<span class="dropdown-item-text text-muted">Aucune tâche épinglée</span>';
            dropdownMenu.appendChild(noTasksItem);
        }
    } else {
        // Supprimer le message "aucune tâche épinglée" s'il existe
        if (noTasksMessage) {
            noTasksMessage.closest('li').remove();
        }
        
        // S'assurer que le séparateur et le lien "Voir toutes mes tâches" existent
        if (!separator) {
            const separatorItem = document.createElement('li');
            separatorItem.innerHTML = '<hr class="dropdown-divider">';
            dropdownMenu.appendChild(separatorItem);
        }
        
        if (!viewAllLink) {
            const viewAllItem = document.createElement('li');
            viewAllItem.innerHTML = '<a class="dropdown-item text-center" href="/tasks/my_tasks">Voir toutes mes tâches</a>';
            dropdownMenu.appendChild(viewAllItem);
        }
    }
}

// Fonction pour afficher une notification toast
function showToast(type, message) {
    createToastContainer();
    const toastContainer = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    const icon = type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'times-circle';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${icon} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: type === 'warning' ? 5000 : 3000
    });
    bsToast.show();
}

// Fonction pour créer le conteneur de toasts s'il n'existe pas
function createToastContainer() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Gérer les formulaires d'épinglage existants
    document.querySelectorAll('.menu-pin-form').forEach(form => {
        setupPinForm(form);
    });
    
    // Gérer les formulaires d'épinglage dans le menu de navigation
    const dropdownMenu = document.querySelector('#pinnedTasksDropdown + .dropdown-menu');
    if (dropdownMenu) {
        dropdownMenu.querySelectorAll('.menu-pin-form').forEach(form => {
            setupPinForm(form);
        });
    }
}); 