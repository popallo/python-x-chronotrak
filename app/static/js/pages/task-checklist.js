/**
 * Gestion des checklists pour les tâches
 */
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

    // Initialisation des écouteurs d'événements
    initChecklistEventListeners();
    initSortable();
    initTimeHistoryHeight();
    initChecklistSizeToggle();
    
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
                addChecklistItem();
            });
        }
        
        // Gestion de la touche Entrée
        if (addItemInput) {
            addItemInput.addEventListener('keydown', e => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    addChecklistItem();
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
                        addChecklistItem(shortcode, true);
                        shortcodeInput.value = '';
                        modal.hide();
                    }
                });
            }
        }
    }
    
    // ==========================================================================
    // Gestion de la hauteur de l'historique de temps
    // ==========================================================================
    function initTimeHistoryHeight() {
        const timeHistory = document.querySelector('.time-history');
        
        function updateTimeHistoryHeight() {
            if (checklistContainer && timeHistory) {
                const checklistHeight = checklistContainer.offsetHeight;
                timeHistory.style.height = `${checklistHeight}px`;
                timeHistory.style.maxHeight = 'none';
            }
        }

        updateTimeHistoryHeight();

        // Observer les changements de classe pour détecter l'expansion/réduction
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    // Attendre la fin de la transition CSS (300ms)
                    setTimeout(updateTimeHistoryHeight, 300);
                }
            });
        });

        observer.observe(checklistContainer, {
            attributes: true,
            attributeFilter: ['class']
        });

        // Observer les changements de contenu
        const contentObserver = new MutationObserver(updateTimeHistoryHeight);
        contentObserver.observe(checklistContainer, {
            childList: true,
            subtree: true
        });

        window.addEventListener('resize', updateTimeHistoryHeight);
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
                onEnd: updateItemsOrder
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
        
        updateChecklistItem(itemId, { is_checked: this.checked });
    }
    
    function handleDeleteClick() {
        const itemId = this.closest('.checklist-item').dataset.id;
        deleteChecklistItem(itemId, this.closest('.checklist-item'));
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
    
    // ==========================================================================
    // Opérations CRUD
    // ==========================================================================
    function addChecklistItem(content = null, isShortcode = false) {
        if (!content && addItemInput) {
            content = addItemInput.value.trim();
        }
        
        if (!content) return;
        
        fetch(`/tasks/${taskId}/checklist`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify({
                content: content,
                is_shortcode: isShortcode
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isShortcode) {
                    window.location.reload();
                } else {
                    addItemToList(data.item);
                    if (addItemInput) {
                        addItemInput.value = '';
                    }
                }
            } else {
                showError(data.error || 'Erreur lors de l\'ajout de l\'élément');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showError('Erreur lors de l\'ajout de l\'élément');
        });
    }
    
    function updateChecklistItem(itemId, data) {
        fetch(`/tasks/${taskId}/checklist/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                showError(data.error || 'Erreur lors de la mise à jour de l\'élément');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showError('Erreur lors de la mise à jour de l\'élément');
        });
    }
    
    function deleteChecklistItem(itemId, element) {
        fetch(`/tasks/${taskId}/checklist/${itemId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-Token': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                element.remove();
            } else {
                showError(data.error || 'Erreur lors de la suppression de l\'élément');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showError('Erreur lors de la suppression de l\'élément');
        });
    }
    
    function updateItemsOrder() {
        const items = Array.from(document.querySelectorAll('.checklist-item'));
        const itemsData = items.map((item, index) => ({
            id: item.dataset.id,
            position: index
        }));
        
        fetch(`/tasks/${taskId}/checklist/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify({ items: itemsData })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                showError(data.error || 'Erreur lors de la réorganisation des éléments');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showError('Erreur lors de la réorganisation des éléments');
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
        
        itemElement.innerHTML = `
            <div class="form-check">
                <input class="form-check-input checklist-checkbox" type="checkbox" id="checklist-item-${item.id}" ${item.is_checked ? 'checked' : ''}>
                <label class="form-check-label" for="checklist-item-${item.id}">
                    <span class="checklist-content">${item.content}</span>
                </label>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-outline-primary copy-to-time-btn ${!item.is_checked ? 'disabled' : ''}" title="Copier dans le formulaire de temps" ${!item.is_checked ? 'disabled' : ''}>
                        <i class="fas fa-clock"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger delete-checklist-item" title="Supprimer">
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
                updateChecklistItem(itemId, { content: newContent });
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
    
    function getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
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
}); 