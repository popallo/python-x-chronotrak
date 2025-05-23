/**
 * Gestion des checklists pour les tâches
 */
document.addEventListener('DOMContentLoaded', function() {
    const checklistContainer = document.getElementById('checklist-container');
    if (!checklistContainer) return;
    
    const taskId = checklistContainer.dataset.taskId;
    const addItemForm = document.getElementById('add-checklist-item-form');
    const addItemInput = document.getElementById('add-checklist-item-input');
    const shortcodeButton = document.getElementById('add-checklist-shortcode-button');
    const shortcodeModal = document.getElementById('shortcode-modal');
    const shortcodeInput = document.getElementById('shortcode-input');
    const shortcodeSubmit = document.getElementById('shortcode-submit');
    
    // Initialiser les écouteurs d'événements pour les cases à cocher existantes
    document.querySelectorAll('.checklist-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const itemId = this.closest('.checklist-item').dataset.id;
            const copyButton = this.closest('.checklist-item').querySelector('.copy-to-time-btn');
            
            // Mettre à jour l'état du bouton de copie
            if (this.checked) {
                copyButton.classList.remove('disabled');
                copyButton.disabled = false;
            } else {
                copyButton.classList.add('disabled');
                copyButton.disabled = true;
            }
            
            updateChecklistItem(itemId, { is_checked: this.checked });
        });
    });
    
    // Initialiser les écouteurs d'événements pour les boutons de suppression existants
    document.querySelectorAll('.delete-checklist-item').forEach(function(button) {
        button.addEventListener('click', function() {
            const itemId = this.closest('.checklist-item').dataset.id;
            deleteChecklistItem(itemId, this.closest('.checklist-item'));
        });
    });
    
    // Initialiser les écouteurs d'événements pour le contenu éditable existant
    document.querySelectorAll('.checklist-content').forEach(function(content) {
        content.addEventListener('dblclick', function() {
            makeContentEditable(this);
        });
    });
    
    // Initialiser les écouteurs d'événements pour les boutons de copie vers le temps
    document.querySelectorAll('.copy-to-time-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const content = this.closest('.checklist-item').querySelector('.checklist-content').textContent;
            const timeDescription = document.querySelector('#description');
            if (timeDescription) {
                timeDescription.value = content;
                timeDescription.focus();
                timeDescription.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    });
    
    // Initialiser Sortable pour le réarrangement des éléments
    const checklistItems = document.getElementById('checklist-items');
    if (checklistItems) {
        new Sortable(checklistItems, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: function(evt) {
                updateItemsOrder();
            }
        });
    }
    
    // Ajouter un élément à la checklist
    if (addItemForm) {
        addItemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addChecklistItem();
        });
        
        // Gérer la touche Entrée
        addItemInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addChecklistItem();
            }
        });
    }
    
    // Gérer le modal de shortcode
    if (shortcodeButton && shortcodeModal) {
        const modal = new bootstrap.Modal(shortcodeModal);
        
        shortcodeButton.addEventListener('click', function() {
            modal.show();
        });
        
        // Soumettre le shortcode
        if (shortcodeSubmit && shortcodeInput) {
            shortcodeSubmit.addEventListener('click', function() {
                const shortcode = shortcodeInput.value.trim();
                if (shortcode) {
                    addChecklistItem(shortcode, true);
                    shortcodeInput.value = '';
                    modal.hide();
                }
            });
        }
    }
    
    // Fonction pour ajouter un élément à la checklist
    function addChecklistItem(content = null, isShortcode = false) {
        if (!content && addItemInput) {
            content = addItemInput.value.trim();
        }
        
        if (!content) return;
        
        const data = {
            content: content,
            is_shortcode: isShortcode
        };
        
        fetch(`/tasks/${taskId}/checklist`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isShortcode) {
                    // Recharger la page pour afficher tous les éléments créés par le shortcode
                    window.location.reload();
                } else {
                    // Ajouter l'élément à la liste
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
    
    // Fonction pour ajouter un élément à la liste
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
        
        checkbox.addEventListener('change', function() {
            // Mettre à jour l'état du bouton de copie
            if (this.checked) {
                copyButton.classList.remove('disabled');
                copyButton.disabled = false;
            } else {
                copyButton.classList.add('disabled');
                copyButton.disabled = true;
            }
            
            updateChecklistItem(item.id, { is_checked: this.checked });
        });
        
        deleteButton.addEventListener('click', function() {
            deleteChecklistItem(item.id, itemElement);
        });
        
        copyButton.addEventListener('click', function() {
            const timeDescription = document.querySelector('#description');
            if (timeDescription) {
                timeDescription.value = contentSpan.textContent;
                timeDescription.focus();
                timeDescription.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
        
        // Rendre le contenu éditable
        contentSpan.addEventListener('dblclick', function() {
            makeContentEditable(contentSpan);
        });
    }
    
    // Fonction pour mettre à jour un élément de la checklist
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
    
    // Fonction pour supprimer un élément de la checklist
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
    
    // Fonction pour mettre à jour l'ordre des éléments
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
    
    // Fonction pour rendre le contenu éditable
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
    
    // Fonction pour récupérer le token CSRF
    function getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (!metaTag) {
            console.error('CSRF token meta tag not found');
            return '';
        }
        return metaTag.getAttribute('content');
    }
    
    // Fonction pour afficher une erreur
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
            
            // Supprimer l'alerte après 5 secondes
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
    }
}); 