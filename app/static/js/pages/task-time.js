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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getTimeHistoryContainer() {
    return document.querySelector('#timeHistoryModal .time-history');
}

function isTimeHistoryAdmin() {
    const container = getTimeHistoryContainer();
    return container?.dataset.isAdmin === 'true';
}

function getTaskSlugFromPage() {
    const container = getTimeHistoryContainer();
    if (container?.dataset.taskSlug) {
        return container.dataset.taskSlug;
    }
    const urlParts = window.location.pathname.split('/');
    const taskIndex = urlParts.indexOf('tasks');
    if (taskIndex !== -1 && taskIndex + 1 < urlParts.length) {
        return urlParts[taskIndex + 1];
    }
    return null;
}

function buildTimeEntryRowHtml(timeEntry, showDelete) {
    const deleteBtn = showDelete && timeEntry.id
        ? `<button type="button" class="btn btn-sm btn-link text-danger py-0 px-1 delete-time-entry-btn"
                  title="Supprimer cette saisie" data-entry-id="${timeEntry.id}">
               <i class="fas fa-trash"></i>
           </button>`
        : '';
    const description = timeEntry.description
        ? `<small class="text-muted d-block mt-1">${escapeHtml(timeEntry.description)}</small>`
        : '';

    return `
        <div class="list-group-item py-2 px-0 time-entry-item" data-entry-id="${timeEntry.id}">
            <div class="d-flex justify-content-between align-items-center time-entry-row-header">
                <span class="text-primary fw-medium">${formatTime(timeEntry.hours)}</span>
                <div class="d-flex align-items-center gap-2">
                    <small class="text-muted">${escapeHtml(timeEntry.created_at)}</small>
                    ${deleteBtn}
                </div>
            </div>
            <small class="text-muted d-block">${escapeHtml(timeEntry.user_name)}</small>
            ${description}
        </div>
    `;
}

function updateTaskTimeBadges(taskData) {
    if (!taskData) return;

    const formatted = taskData.actual_time !== undefined && taskData.actual_time !== null
        ? formatTime(taskData.actual_time)
        : '0 min';
    const timeBadge = document.getElementById('total-time-badge');
    if (timeBadge) timeBadge.textContent = formatted;
    const timeBadgeModal = document.getElementById('total-time-badge-modal');
    if (timeBadgeModal) timeBadgeModal.textContent = formatted;

    if (taskData.remaining_credit !== null && taskData.remaining_credit !== undefined) {
        const oldBadge = document.getElementById('remaining-credit-badge');
        if (oldBadge) {
            const remainingCredit = parseTimeString(taskData.remaining_credit);

            if (!isNaN(remainingCredit)) {
                const newBadge = document.createElement('span');
                newBadge.id = 'remaining-credit-badge';
                newBadge.className = `badge ${remainingCredit < 2 ? 'bg-danger' :
                                     remainingCredit < 5 ? 'bg-warning' :
                                     'bg-success'} text-white d-flex align-items-center`;
                newBadge.setAttribute('data-bs-toggle', 'tooltip');
                newBadge.setAttribute('title', 'Crédit restant du projet');
                newBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(remainingCredit)}`;

                oldBadge.parentNode.replaceChild(newBadge, oldBadge);

                const tooltip = bootstrap.Tooltip.getInstance(newBadge);
                if (tooltip) {
                    tooltip.dispose();
                }
                new bootstrap.Tooltip(newBadge);

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
}

function prependTimeEntryRow(timeEntry) {
    const timeHistoryContainer = getTimeHistoryContainer();
    if (!timeHistoryContainer || !timeEntry) return;

    const entryHtml = buildTimeEntryRowHtml(timeEntry, isTimeHistoryAdmin());
    let timeList = timeHistoryContainer.querySelector('.list-group');

    if (!timeList) {
        const noTimeMessage = timeHistoryContainer.querySelector('.time-history-empty, .text-muted.small');
        if (noTimeMessage) {
            noTimeMessage.outerHTML = `<div class="list-group list-group-flush">${entryHtml}</div>`;
        }
    } else {
        timeList.insertAdjacentHTML('afterbegin', entryHtml);
    }
}

function removeTimeEntryFromUI(entryId, taskData) {
    const timeHistoryContainer = getTimeHistoryContainer();
    if (!timeHistoryContainer) return;

    const item = timeHistoryContainer.querySelector(`.time-entry-item[data-entry-id="${entryId}"]`);
    if (item) {
        item.remove();
    }

    const timeList = timeHistoryContainer.querySelector('.list-group');
    if (timeList && !timeList.querySelector('.time-entry-item')) {
        timeList.remove();
        const emptyMsg = document.createElement('p');
        emptyMsg.className = 'text-muted small mb-0 time-history-empty';
        emptyMsg.textContent = 'Aucun temps enregistré';
        timeHistoryContainer.appendChild(emptyMsg);
    }

    updateTaskTimeBadges(taskData);
}

// Fonction pour mettre à jour l'interface après l'ajout de temps
async function updateTimeInterface(data) {
    updateTaskTimeBadges(data.task);
    prependTimeEntryRow(data.time_entry);

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

// Initialisation (les modules s'exécutent après le DOM ; si DOMContentLoaded est déjà passé, on lance tout de suite)
function initTimePage() {
    createToastContainer();

    const timeForm = document.querySelector('#timeEntryModal form');
    if (timeForm) {
        timeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleTimeSubmit(e);
        });
    }

    const timeHistoryModal = document.getElementById('timeHistoryModal');
    if (timeHistoryModal) {
        timeHistoryModal.addEventListener('click', handleDeleteTimeEntryClick);
    }

    // La checklist gère elle-même l'ouverture de la modale + dataset.checklistItemId via handleCopyToTime
    // On n'attache pas de second handler ici pour éviter de ne pas définir l'id.
}

async function handleDeleteTimeEntryClick(e) {
    const btn = e.target.closest('.delete-time-entry-btn');
    if (!btn) return;

    e.preventDefault();
    const entryId = btn.dataset.entryId;
    const taskSlug = getTaskSlugFromPage();

    if (!entryId || !taskSlug) return;

    if (!confirm('Supprimer cette saisie de temps ?')) {
        return;
    }

    btn.disabled = true;

    try {
        const data = await utils.fetchWithCsrf(
            `/tasks/${encodeURIComponent(taskSlug)}/time_entries/${encodeURIComponent(entryId)}`,
            { method: 'DELETE' }
        );

        if (data.success) {
            removeTimeEntryFromUI(entryId, data.task);
            if (data.message) {
                showToast(data.message, 'success');
            }
        } else {
            showToast(data.error || 'Erreur lors de la suppression', 'danger');
            btn.disabled = false;
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression du temps', 'danger');
        btn.disabled = false;
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTimePage);
} else {
    initTimePage();
}

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

            const modalEl = document.getElementById('timeEntryModal');
            if (modalEl && modalEl.dataset.checklistItemId) {
                document.dispatchEvent(new CustomEvent('time-logged-from-checklist', { detail: { checklistItemId: modalEl.dataset.checklistItemId } }));
                delete modalEl.dataset.checklistItemId;
            }

            const modal = bootstrap.Modal.getInstance(modalEl);
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
    updateTaskTimeBadges({ actual_time: totalTime });
}

function updateRemainingCredit(remainingCredit) {
    updateTaskTimeBadges({ remaining_credit: remainingCredit });
}

// Cette fonction a été supprimée car la réorganisation est maintenant gérée côté serveur
// dans l'endpoint update_checklist_item

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

// Cette fonction a été supprimée car la réorganisation est maintenant gérée côté serveur

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
