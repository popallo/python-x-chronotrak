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
                        <small class="text-muted">${document.querySelector('.project-name')?.textContent || ''}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-${document.querySelector('.status-btn.active')?.dataset.status || 'info'}">${document.querySelector('.status-btn.active')?.dataset.status || ''}</span>
                        <form action="${window.location.pathname}/toggle_pin" method="POST" class="d-inline menu-pin-form">
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
    const pinnedCount = document.querySelector('#pinnedTasksDropdown .badge');
    if (pinnedCount) {
        const currentCount = parseInt(pinnedCount.textContent) || 0;
        const newCount = data.is_pinned ? currentCount + 1 : currentCount - 1;
        
        if (newCount > 0) {
            pinnedCount.textContent = newCount;
        } else {
            pinnedCount.remove();
        }
    } else if (data.is_pinned) {
        // Si le badge n'existe pas et qu'on ajoute une tâche, le créer
        const dropdownToggle = document.querySelector('#pinnedTasksDropdown');
        const badge = document.createElement('span');
        badge.className = 'badge bg-info';
        badge.textContent = '1';
        dropdownToggle.appendChild(badge);
    }
}

// Fonction pour configurer un formulaire d'épinglage
function setupPinForm(form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const button = form.querySelector('button');
        button.disabled = true;
        
        fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePinInterface(data);
            } else {
                showToast('danger', data.error || 'Une erreur est survenue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
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
        const taskItem = dropdownMenu.querySelector(`.dropdown-item[href="${window.location.pathname}"]`)?.closest('li');
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
                        <small class="text-muted">${document.querySelector('.project-name')?.textContent || ''}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-${statusColor}">${status}</span>
                        <form action="${window.location.pathname}/toggle_pin" method="POST" class="d-inline menu-pin-form">
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

            // Mettre à jour le compteur
            const badge = document.querySelector('#pinnedTasksDropdown .badge');
            if (badge) {
                const count = parseInt(badge.textContent) + 1;
                badge.textContent = count;
            } else {
                const newBadge = document.createElement('span');
                newBadge.className = 'badge bg-info';
                newBadge.textContent = '1';
                document.querySelector('#pinnedTasksDropdown').appendChild(newBadge);
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

            // Mettre à jour le compteur
            const badge = document.querySelector('#pinnedTasksDropdown .badge');
            if (badge) {
                const count = parseInt(badge.textContent) - 1;
                if (count > 0) {
                    badge.textContent = count;
                } else {
                    badge.remove();
                }
            }

            // Vérifier s'il reste des tâches épinglées
            const remainingTasks = dropdownMenu.querySelectorAll('li[data-task-id]');
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
    }

    // Afficher la notification
    showToast('success', data.message);
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
    // Gérer les formulaires d'épinglage
    document.querySelectorAll('.menu-pin-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const button = this.querySelector('button');
            const originalContent = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updatePinInterface(data);
                } else {
                    showToast('danger', data.error || 'Une erreur est survenue.');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showToast('danger', 'Une erreur est survenue lors de l\'opération.');
            })
            .finally(() => {
                button.disabled = false;
                button.innerHTML = originalContent;
            });
        });
    });
}); 