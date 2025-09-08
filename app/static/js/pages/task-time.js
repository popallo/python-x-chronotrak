import { CONFIG, utils } from '../utils.js';

// Fonction pour récupérer le temps restant
async function getRemainingCredit(taskSlug) {
    const data = await utils.fetchWithCsrf(`/api/tasks/${taskSlug}/remaining-credit`, {
        method: 'GET'
    });

    if (data.success) {
        return data.remaining_credit;
    }
    return null;
}

// Fonction pour convertir le format "XhYmin" en nombre décimal
function parseTimeString(timeStr) {
    if (!timeStr) return 0;
    
    // Si c'est déjà un nombre, le retourner
    if (typeof timeStr === 'number') return timeStr;
    
    // Extraire les heures et les minutes
    const hoursMatch = timeStr.match(/(\d+)h/);
    const minutesMatch = timeStr.match(/(\d+)min/);
    
    const hours = hoursMatch ? parseInt(hoursMatch[1]) : 0;
    const minutes = minutesMatch ? parseInt(minutesMatch[1]) : 0;
    
    // Convertir en nombre décimal (heures)
    return hours + (minutes / 60);
}

// Fonction pour formater le temps
function formatTime(hours) {
    if (!hours) return '0 min';
    const totalMinutes = Math.round(hours * 60);
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    return h > 0 ? `${h}h${m.toString().padStart(2, '0')}min` : `${m}min`;
}

// Fonction pour mettre à jour l'interface après l'ajout de temps
async function updateTimeInterface(data) {
    // Mettre à jour le temps total
    const timeBadge = document.querySelector('.badge[title="Temps total passé sur la tâche"]');
    if (timeBadge) {
        timeBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(data.task.actual_time)}`;
    }
    
    // Mettre à jour le crédit restant directement depuis les données reçues
    if (data.task.remaining_credit !== null && data.task.remaining_credit !== undefined) {
        const oldBadge = document.getElementById('remaining-credit-badge');
        if (oldBadge) {
            // Convertir le temps restant en nombre décimal
            const remainingCredit = parseTimeString(data.task.remaining_credit);
            
            if (!isNaN(remainingCredit)) {
                // Créer un nouveau badge
                const newBadge = document.createElement('span');
                newBadge.id = 'remaining-credit-badge';
                newBadge.className = `badge ${remainingCredit < 2 ? 'bg-danger' : 
                                     remainingCredit < 5 ? 'bg-warning' : 
                                     'bg-success'} text-white d-flex align-items-center`;
                newBadge.setAttribute('data-bs-toggle', 'tooltip');
                newBadge.setAttribute('title', 'Crédit restant du projet');
                newBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(remainingCredit)}`;
                
                // Remplacer l'ancien badge par le nouveau
                oldBadge.parentNode.replaceChild(newBadge, oldBadge);
                
                // Réinitialiser le tooltip Bootstrap
                const tooltip = bootstrap.Tooltip.getInstance(newBadge);
                if (tooltip) {
                    tooltip.dispose();
                }
                new bootstrap.Tooltip(newBadge);

                // Mettre à jour aussi l'alerte dans le modal si elle existe
                const creditAlert = document.querySelector('#timeEntryModal .alert');
                if (creditAlert) {
                    const alertClass = remainingCredit < 2 ? 'alert-danger' : 
                                     remainingCredit < 5 ? 'alert-warning' : 
                                     'alert-success';
                    creditAlert.className = `alert ${alertClass} mb-4 no-auto-close`;
                    const creditText = creditAlert.querySelector('strong');
                    if (creditText) {
                        creditText.textContent = formatTime(remainingCredit);
                        creditText.className = `${remainingCredit < 2 ? 'text-danger' : 
                                              remainingCredit < 5 ? 'text-warning' : 
                                              'text-success'} ms-2`;
                    }
                }
            }
        }
    }
    
    // Ajouter la nouvelle entrée de temps à la liste
    const timeHistoryContainer = document.querySelector('.time-history');
    if (timeHistoryContainer) {
        const timeEntry = data.time_entry;
        const entryHtml = `
            <div class="list-group-item py-1 px-2 time-entry-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-minus me-1 text-danger"></i>
                        <span class="text-danger">
                            ${formatTime(timeEntry.hours)}
                        </span>
                    </div>
                    <small class="text-muted">${timeEntry.created_at}</small>
                </div>
                <small class="text-muted d-block">${timeEntry.user_name}</small>
                ${timeEntry.description ? `<small class="text-muted d-block mt-1">${timeEntry.description}</small>` : ''}
            </div>
        `;
        
        // Vérifier s'il y a déjà une liste d'entrées de temps
        let timeList = timeHistoryContainer.querySelector('.list-group');
        
        if (!timeList) {
            // S'il n'y a pas de liste, créer une nouvelle liste et remplacer le message "Aucun temps enregistré"
            const noTimeMessage = timeHistoryContainer.querySelector('.text-muted.small');
            if (noTimeMessage) {
                // Créer la structure de liste
                const listGroupHtml = `<div class="list-group list-group-flush">${entryHtml}</div>`;
                noTimeMessage.outerHTML = listGroupHtml;
            }
        } else {
            // S'il y a déjà une liste, ajouter la nouvelle entrée au début
            timeList.insertAdjacentHTML('afterbegin', entryHtml);
        }
    }
    
    // Afficher les messages de succès/alerte
    if (data.message) {
        showToast(data.message, 'success');
    }
    if (data.warning) {
        showToast(data.warning, 'warning');
    }
}

// Fonction pour afficher un toast
function showToast(message, type = 'success') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = createToastContainer();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white border-0`;
    
    // Appliquer les bonnes classes de couleur
    if (type === 'success') {
        toast.classList.add('bg-success');
    } else if (type === 'warning') {
        toast.classList.add('bg-warning');
    } else if (type === 'danger') {
        toast.classList.add('bg-danger');
    } else {
        toast.classList.add('bg-info');
    }
    
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Fonction pour créer le conteneur de toasts s'il n'existe pas
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Créer le conteneur de toasts
    createToastContainer();
    
    // Gérer la soumission du formulaire d'ajout de temps
    const timeForm = document.querySelector('#timeEntryModal form');
    if (timeForm) {
        timeForm.addEventListener('submit', handleTimeSubmit);
    } else {
        console.error('Formulaire d\'ajout de temps non trouvé');
    }
    
    // Gérer le bouton de copie depuis la checklist
    document.querySelectorAll('.copy-to-time-btn').forEach(button => {
        button.addEventListener('click', function() {
            const checklistItem = this.closest('.checklist-item');
            const content = checklistItem.querySelector('.checklist-content').textContent;
            const timeForm = document.querySelector('#timeEntryModal form');
            if (timeForm) {
                const descriptionField = timeForm.querySelector('textarea[name="description"]');
                if (descriptionField) {
                    descriptionField.value = content;
                    const modal = bootstrap.Modal.getInstance(document.getElementById('timeEntryModal'));
                    if (modal) {
                        modal.show();
                    }
                }
            }
        });
    });
});

async function handleTimeSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    
    if (!submitButton) {
        console.error('Bouton de soumission non trouvé dans le formulaire:', form);
        return;
    }
    
    const originalButtonText = submitButton.innerHTML || submitButton.value;
    
    try {
        submitButton.disabled = true;
        if (submitButton.tagName === 'BUTTON') {
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            submitButton.value = 'Enregistrement...';
        }
        
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': window.csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Utiliser la fonction updateTimeInterface pour mettre à jour l'interface de manière cohérente
            await updateTimeInterface(data);
            
            // Réorganiser les éléments cochés en bas de la checklist
            await reorderCheckedItemsToBottom();
            
            // Fermer le modal et réinitialiser le formulaire
            const modal = bootstrap.Modal.getInstance(document.getElementById('timeEntryModal'));
            if (modal) {
                modal.hide();
            }
            form.reset();
        } else {
            showToast(data.error || 'Erreur lors de l\'enregistrement du temps', 'danger');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de l\'enregistrement du temps', 'danger');
    } finally {
        if (submitButton) {
            submitButton.disabled = false;
            if (submitButton.tagName === 'BUTTON') {
                submitButton.innerHTML = originalButtonText;
            } else {
                submitButton.value = originalButtonText;
            }
        }
    }
}



function updateTimeDisplay(totalTime) {
    // Mettre à jour le temps total
    const timeBadge = document.querySelector('.badge[title="Temps total passé sur la tâche"]');
    if (timeBadge) {
        timeBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(totalTime)}`;
    }
}

function updateRemainingCredit(remainingCredit) {
    // Mettre à jour le crédit restant directement depuis les données reçues
    if (remainingCredit !== null && remainingCredit !== undefined) {
        const oldBadge = document.getElementById('remaining-credit-badge');
        if (oldBadge) {
            // Convertir le temps restant en nombre décimal
            const remainingCreditDecimal = parseTimeString(remainingCredit);
            
            if (!isNaN(remainingCreditDecimal)) {
                // Créer un nouveau badge
                const newBadge = document.createElement('span');
                newBadge.id = 'remaining-credit-badge';
                newBadge.className = `badge ${remainingCreditDecimal < 2 ? 'bg-danger' : 
                                     remainingCreditDecimal < 5 ? 'bg-warning' : 
                                     'bg-success'} text-white d-flex align-items-center`;
                newBadge.setAttribute('data-bs-toggle', 'tooltip');
                newBadge.setAttribute('title', 'Crédit restant du projet');
                newBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(remainingCreditDecimal)}`;
                
                // Remplacer l'ancien badge par le nouveau
                oldBadge.parentNode.replaceChild(newBadge, oldBadge);
                
                // Réinitialiser le tooltip Bootstrap
                const tooltip = bootstrap.Tooltip.getInstance(newBadge);
                if (tooltip) {
                    tooltip.dispose();
                }
                new bootstrap.Tooltip(newBadge);

                // Mettre à jour aussi l'alerte dans le modal si elle existe
                const creditAlert = document.querySelector('#timeEntryModal .alert');
                if (creditAlert) {
                    const alertClass = remainingCreditDecimal < 2 ? 'alert-danger' : 
                                     remainingCreditDecimal < 5 ? 'alert-warning' : 
                                     'alert-success';
                    creditAlert.className = `alert ${alertClass} mb-4 no-auto-close`;
                    const creditText = creditAlert.querySelector('strong');
                    if (creditText) {
                        creditText.textContent = formatTime(remainingCreditDecimal);
                        creditText.className = `${remainingCreditDecimal < 2 ? 'text-danger' : 
                                              remainingCreditDecimal < 5 ? 'text-warning' : 
                                              'text-success'} ms-2`;
                    }
                }
            }
        }
    }
}

async function reorderCheckedItemsToBottom() {
    try {
        // Récupérer l'ID de la tâche depuis l'URL ou le DOM
        const taskId = getTaskIdFromPage();
        if (!taskId) {
            console.error('Impossible de récupérer l\'ID de la tâche');
            return;
        }
        
        // Récupérer tous les éléments de la checklist
        const items = Array.from(document.querySelectorAll('.checklist-item'));
        
        if (items.length === 0) return;
        
        // Séparer les éléments cochés et non cochés
        const uncheckedItems = [];
        const checkedItems = [];
        
        items.forEach(item => {
            const checkbox = item.querySelector('.checklist-checkbox');
            const itemData = {
                id: item.dataset.id,
                is_checked: checkbox.checked
            };
            
            if (checkbox.checked) {
                checkedItems.push(itemData);
            } else {
                uncheckedItems.push(itemData);
            }
        });
        
        // Créer le nouvel ordre : non cochés d'abord, puis cochés
        const newOrder = [...uncheckedItems, ...checkedItems].map((item, index) => ({
            id: item.id,
            position: index
        }));
        
        // Envoyer le nouvel ordre au serveur
        const response = await fetch(`/tasks/${taskId}/checklist/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ items: newOrder })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Réorganiser directement dans le DOM sans recharger depuis le serveur
            reorderChecklistInDOM(uncheckedItems, checkedItems);
        } else {
            console.error('Erreur lors de la réorganisation:', data.error);
        }
    } catch (error) {
        console.error('Erreur lors de la réorganisation des éléments:', error);
    }
}

function getTaskIdFromPage() {
    // Essayer de récupérer l'ID depuis le conteneur de checklist
    const checklistContainer = document.getElementById('checklist-container');
    if (checklistContainer && checklistContainer.dataset.taskId) {
        return checklistContainer.dataset.taskId;
    }
    
    // Essayer de récupérer depuis l'URL
    const urlParts = window.location.pathname.split('/');
    const taskIndex = urlParts.indexOf('tasks');
    if (taskIndex !== -1 && taskIndex + 1 < urlParts.length) {
        return urlParts[taskIndex + 1];
    }
    
    return null;
}

async function refreshChecklistDisplay(taskId) {
    try {
        // Récupérer la checklist mise à jour depuis le serveur
        const response = await fetch(`/tasks/${taskId}/checklist`, {
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Mettre à jour l'affichage de la checklist
                updateChecklistDisplay(data.checklist);
            }
        }
    } catch (error) {
        console.error('Erreur lors de la récupération de la checklist:', error);
    }
}

function reorderChecklistInDOM(uncheckedItems, checkedItems) {
    const checklistItems = document.getElementById('checklist-items');
    if (!checklistItems) return;
    
    // Créer un tableau avec tous les éléments dans le bon ordre
    const allItems = [...uncheckedItems, ...checkedItems];
    
    // Réorganiser les éléments dans le DOM
    allItems.forEach(itemData => {
        const itemElement = document.querySelector(`.checklist-item[data-id="${itemData.id}"]`);
        if (itemElement) {
            // S'assurer que l'état de la checkbox correspond à l'état attendu
            const checkbox = itemElement.querySelector('.checklist-checkbox');
            if (checkbox) {
                checkbox.checked = itemData.is_checked;
                
                // Mettre à jour l'état du bouton de copie
                const copyButton = itemElement.querySelector('.copy-to-time-btn');
                if (copyButton) {
                    copyButton.classList.toggle('disabled', !itemData.is_checked);
                    copyButton.disabled = !itemData.is_checked;
                }
            }
            
            checklistItems.appendChild(itemElement);
        }
    });
    
    // Ajouter une animation subtile pour montrer le changement
    const movedItems = document.querySelectorAll('.checklist-item');
    movedItems.forEach(item => {
        item.style.transition = 'background-color 0.3s ease';
        item.style.backgroundColor = 'rgba(var(--bs-primary-rgb), 0.05)';
        setTimeout(() => {
            item.style.backgroundColor = '';
        }, 300);
    });
}

function updateChecklistDisplay(checklist) {
    const checklistItems = document.getElementById('checklist-items');
    if (!checklistItems) return;
    
    // Vider le conteneur
    checklistItems.innerHTML = '';
    
    // Ajouter chaque élément dans le nouvel ordre
    checklist.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'checklist-item';
        itemElement.dataset.id = item.id;
        itemElement.style.padding = '0.25rem 0';
        
        itemElement.innerHTML = `
            <div class="form-check d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center flex-grow-1">
                    <input class="form-check-input checklist-checkbox me-2" type="checkbox" id="checklist-item-${item.id}" ${item.is_checked ? 'checked' : ''}>
                    <div class="checklist-drag-handle me-2" title="Déplacer cet élément">
                        <i class="fas fa-grip-vertical text-muted"></i>
                    </div>
                    <label class="form-check-label mb-0" for="checklist-item-${item.id}" style="font-size: 0.9rem;">
                        <span class="checklist-content">${item.content}</span>
                    </label>
                </div>
                <div class="btn-group btn-group-sm ms-2">
                    <button type="button" class="btn btn-outline-primary btn-sm py-0 px-2 copy-to-time-btn ${!item.is_checked ? 'disabled' : ''}" title="Copier dans le formulaire de temps" ${!item.is_checked ? 'disabled' : ''}>
                        <i class="fas fa-clock"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger btn-sm py-0 px-2 delete-checklist-item" title="Supprimer">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        checklistItems.appendChild(itemElement);
        
        // Réattacher les événements
        const checkbox = itemElement.querySelector('.checklist-checkbox');
        const deleteButton = itemElement.querySelector('.delete-checklist-item');
        const copyButton = itemElement.querySelector('.copy-to-time-btn');
        const contentSpan = itemElement.querySelector('.checklist-content');
        
        // Réattacher les événements de la checklist
        if (window.checklistEventHandlers) {
            checkbox.addEventListener('change', window.checklistEventHandlers.handleCheckboxChange);
            deleteButton.addEventListener('click', window.checklistEventHandlers.handleDeleteClick);
            copyButton.addEventListener('click', window.checklistEventHandlers.handleCopyToTime);
            contentSpan.addEventListener('dblclick', () => window.checklistEventHandlers.makeContentEditable(contentSpan));
        }
    });
} 