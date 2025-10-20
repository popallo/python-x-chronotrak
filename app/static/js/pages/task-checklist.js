/**
 * Gestion des checklists pour les tâches
 */
import { CONFIG, utils } from '../utils.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des éléments DOM
    const checklistContainer = document.getElementById('checklist-container');
    if (!checklistContainer) return;
    
    const taskId = checklistContainer.dataset.taskId;
    const addItemForm = document.getElementById('add-checklist-item-form');
    const addItemInput = document.getElementById('add-checklist-item-input');
    const shortcodeButton = document.getElementById('add-checklist-shortcode-button');
    const shortcodeModal = document.getElementById('shortcode-modal');
    const shortcodeInput = document.getElementById('shortcode-input');
    const shortcodeSubmit = document.getElementById('shortcode-submit');
    const toggleSizeButton = document.querySelector('.toggle-checklist-size');
    const toggleTimeSizeButton = document.querySelector('.toggle-time-size');

    // Initialisation des écouteurs d'événements
    initChecklistEventListeners();
    initSortable();
    initTimeHistoryHeight();
    initChecklistSizeToggle();
    initTimeSizeToggle();
    
    // ==========================================================================
    // Gestion de la taille de la checklist
    // ==========================================================================
    function initChecklistSizeToggle() {
        if (toggleSizeButton) {
            toggleSizeButton.addEventListener('click', function() {
                checklistContainer.classList.toggle('expanded');
                const icon = this.querySelector('i');
                if (checklistContainer.classList.contains('expanded')) {
                    icon.classList.replace('fa-expand-alt', 'fa-compress-alt');
                } else {
                    icon.classList.replace('fa-compress-alt', 'fa-expand-alt');
                }
            });
        }
    }
    
    // ==========================================================================
    // Gestion des événements de la checklist
    // ==========================================================================
    function initChecklistEventListeners() {
        // Écouteurs pour les cases à cocher existantes
        document.querySelectorAll('.checklist-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', handleCheckboxChange);
        });
        
        // Écouteurs pour les boutons de suppression
        document.querySelectorAll('.delete-checklist-item').forEach(button => {
            button.addEventListener('click', handleDeleteClick);
        });
        
        // Écouteurs pour le contenu éditable
        document.querySelectorAll('.checklist-content').forEach(content => {
            content.addEventListener('dblclick', () => makeContentEditable(content));
        });
        
        // Écouteurs pour les boutons de copie vers le temps
        document.querySelectorAll('.copy-to-time-btn').forEach(button => {
            button.addEventListener('click', handleCopyToTime);
        });
        
        // Gestion du formulaire d'ajout
        if (addItemForm) {
            addItemForm.addEventListener('submit', e => {
                e.preventDefault();
                addChecklistItem(taskId);
            });
        }
        
        // Gestion de la touche Entrée
        if (addItemInput) {
            addItemInput.addEventListener('keydown', e => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    addChecklistItem(taskId);
                }
            });
        }
        
        // Gestion du modal de shortcode
        if (shortcodeButton && shortcodeModal) {
            const modal = new bootstrap.Modal(shortcodeModal);
            shortcodeButton.addEventListener('click', () => modal.show());
            
            if (shortcodeSubmit && shortcodeInput) {
                shortcodeSubmit.addEventListener('click', () => {
                    const shortcode = shortcodeInput.value.trim();
                    if (shortcode) {
                        addChecklistItem(taskId, shortcode, true);
                        shortcodeInput.value = '';
                        modal.hide();
                    }
                });
            }
        }
    }
    
    // ==========================================================================
    // Gestion de la taille de l'historique de temps
    // ==========================================================================
    function initTimeSizeToggle() {
        if (toggleTimeSizeButton) {
            const timeHistory = document.querySelector('.time-history');
            toggleTimeSizeButton.addEventListener('click', function() {
                timeHistory.classList.toggle('expanded');
                const icon = this.querySelector('i');
                if (timeHistory.classList.contains('expanded')) {
                    icon.classList.replace('fa-expand-alt', 'fa-compress-alt');
                } else {
                    icon.classList.replace('fa-compress-alt', 'fa-expand-alt');
                }
            });
        }
    }
    
    // ==========================================================================
    // Gestion de la synchronisation des hauteurs (approche simplifiée)
    // ==========================================================================
    function initTimeHistoryHeight() {
        // Cette fonction est maintenant simplifiée - CSS gère l'alignement
        // On garde juste un observateur pour les changements de contenu
        const timeHistory = document.querySelector('.time-history');
        
        if (timeHistory) {
            // Observer les changements de contenu pour déclencher un reflow
            const contentObserver = new MutationObserver(() => {
                // Forcer un reflow pour que CSS recalcule les hauteurs
                timeHistory.offsetHeight;
            });
            
            contentObserver.observe(timeHistory, {
                childList: true,
                subtree: true
            });
        }
    }
    
    // ==========================================================================
    // Gestion du tri des éléments
    // ==========================================================================
    function initSortable() {
        const checklistItems = document.getElementById('checklist-items');
        if (checklistItems) {
            new Sortable(checklistItems, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: updateItemsOrder,
                handle: '.checklist-drag-handle',
                preventOnFilter: true,
                filter: '.checklist-checkbox, .btn-group'
            });
        }
    }
    
    // ==========================================================================
    // Gestionnaires d'événements
    // ==========================================================================
    function handleCheckboxChange() {
        const itemId = this.closest('.checklist-item').dataset.id;
        const copyButton = this.closest('.checklist-item').querySelector('.copy-to-time-btn');
        
        copyButton.classList.toggle('disabled', !this.checked);
        copyButton.disabled = !this.checked;
        
        toggleChecklistItem(taskId, itemId, this.checked);
    }
    
    function handleDeleteClick() {
        const itemId = this.closest('.checklist-item').dataset.id;
        deleteChecklistItem(taskId, itemId);
    }
    
    function handleCopyToTime() {
        const checklistItem = this.closest('.checklist-item');
        const content = checklistItem.querySelector('.checklist-content').textContent;
        const timeModal = new bootstrap.Modal(document.getElementById('timeEntryModal'));
        const descriptionInput = document.querySelector('#timeEntryModal textarea[name="description"]');
        
        timeModal.show();
        
        document.getElementById('timeEntryModal').addEventListener('shown.bs.modal', function() {
            descriptionInput.value = content;
            descriptionInput.focus();
        }, { once: true });
    }
    
    // Exposer les gestionnaires d'événements pour qu'ils puissent être réutilisés
    window.checklistEventHandlers = {
        handleCheckboxChange,
        handleDeleteClick,
        handleCopyToTime,
        makeContentEditable
    };
    
    // Plus besoin d'exposer une fonction de mise à jour de hauteur
    // CSS gère maintenant l'alignement naturellement
    
    // ==========================================================================
    // Opérations CRUD
    // ==========================================================================
    async function addChecklistItem(taskId, content = null, isShortcode = false) {
        if (!content && addItemInput) {
            content = addItemInput.value.trim();
        }
        
        if (!content) return;
        
        const data = await utils.fetchWithCsrf(`/tasks/${taskId}/checklist`, {
            method: 'POST',
            body: JSON.stringify({
                content: content,
                is_shortcode: isShortcode,
                csrf_token: CONFIG.csrfToken
            })
        });

        if (data.success) {
            if (isShortcode) {
                window.location.reload();
            } else {
                updateChecklist(data.checklist);
                if (addItemInput) {
                    addItemInput.value = '';
                }
            }
        } else {
            showError(data.error || 'Erreur lors de l\'ajout de l\'élément');
        }
    }
    
    async function toggleChecklistItem(taskId, itemId, isChecked = null) {
        try {
            const data = await utils.fetchWithCsrf(`/tasks/${taskId}/checklist/${itemId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    is_checked: isChecked,
                    csrf_token: CONFIG.csrfToken
                })
            });

            if (data.success) {
                // Mettre à jour l'affichage avec les données du serveur
                updateChecklist(data.checklist);
            } else {
                console.error('Erreur lors de la mise à jour:', data.error);
                showError(data.error || 'Erreur lors de la mise à jour de l\'élément');
            }
        } catch (error) {
            console.error('Erreur réseau:', error);
            showError('Erreur de connexion lors de la mise à jour');
        }
    }
    
    async function deleteChecklistItem(taskId, itemId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
            return;
        }

        const data = await utils.fetchWithCsrf(`/tasks/${taskId}/checklist/${itemId}`, {
            method: 'DELETE',
            body: JSON.stringify({
                csrf_token: CONFIG.csrfToken
            })
        });

        if (data.success) {
            updateChecklist(data.checklist);
        }
    }
    
    async function updateChecklistItemContent(taskId, itemId, content) {
        const data = await utils.fetchWithCsrf(`/tasks/${taskId}/checklist/${itemId}`, {
            method: 'PUT',
            body: JSON.stringify({
                content: content,
                csrf_token: CONFIG.csrfToken
            })
        });

        if (data.success) {
            updateChecklist(data.checklist);
        }
    }
    
    function updateItemsOrder() {
        const items = Array.from(document.querySelectorAll('.checklist-item'));
        const itemsData = items.map((item, index) => ({
            id: item.dataset.id,
            position: index
        }));
        
        reorderChecklist(taskId, itemsData);
    }
    
    function updateChecklist(checklist) {
        const checklistItems = document.getElementById('checklist-items');
        if (!checklistItems) return;
        
        // Vérifier que checklist est défini et est un tableau
        if (!checklist || !Array.isArray(checklist)) {
            console.error('Checklist invalide reçue:', checklist);
            return;
        }
        
        checklistItems.innerHTML = '';
        
        checklist.forEach(item => {
            addItemToList(item);
        });
    }
    
    // ==========================================================================
    // Utilitaires
    // ==========================================================================
    function addItemToList(item) {
        const checklistItems = document.getElementById('checklist-items');
        if (!checklistItems) return;
        
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
        
        // Ajouter les écouteurs d'événements
        const checkbox = itemElement.querySelector('.checklist-checkbox');
        const deleteButton = itemElement.querySelector('.delete-checklist-item');
        const copyButton = itemElement.querySelector('.copy-to-time-btn');
        const contentSpan = itemElement.querySelector('.checklist-content');
        
        checkbox.addEventListener('change', handleCheckboxChange);
        deleteButton.addEventListener('click', handleDeleteClick);
        copyButton.addEventListener('click', handleCopyToTime);
        contentSpan.addEventListener('dblclick', () => makeContentEditable(contentSpan));
    }
    
    function makeContentEditable(element) {
        const currentContent = element.textContent;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentContent;
        input.className = 'form-control form-control-sm';
        
        element.textContent = '';
        element.appendChild(input);
        input.focus();
        
        input.addEventListener('blur', function() {
            const newContent = this.value.trim();
            if (newContent && newContent !== currentContent) {
                const itemId = element.closest('.checklist-item').dataset.id;
                // Pour l'édition de contenu, on envoie le nouveau contenu au lieu de l'état de la checkbox
                updateChecklistItemContent(taskId, itemId, newContent);
                element.textContent = newContent;
            } else {
                element.textContent = currentContent;
            }
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            } else if (e.key === 'Escape') {
                element.textContent = currentContent;
            }
        });
    }
    
    function reorderChecklist(taskId, items) {
        fetch(`/tasks/${taskId}/checklist/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': CONFIG.csrfToken
            },
            body: JSON.stringify({ items: items })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mettre à jour l'affichage avec les données du serveur
                updateChecklist(data.checklist);
            } else {
                showError(data.error || 'Erreur lors de la réorganisation des éléments');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showError('Erreur lors de la réorganisation des éléments');
        });
    }
    
    function showError(message) {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            alertContainer.appendChild(alert);
            
            setTimeout(() => alert.remove(), 5000);
        }
    }

    // Gestion des réponses aux commentaires
    document.querySelectorAll('.reply-button').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
        });
    });

    // Gestionnaire pour le bouton d'annulation de réponse
    document.querySelectorAll('.cancel-reply-btn').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            replyForm.style.display = 'none';
        });
    });
}); 