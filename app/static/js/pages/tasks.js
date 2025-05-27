/**
 * Script pour la gestion des tâches
 */

// Gestionnaire pour les boutons de changement de statut
function initStatusToggle() {
    const statusButtons = document.querySelectorAll('.status-btn');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Vérifier si le bouton est déjà le statut actif
            if (this.classList.contains('btn-info') || 
                this.classList.contains('btn-warning') || 
                this.classList.contains('btn-success')) {
                // Ce statut est déjà sélectionné, ne rien faire
                event.preventDefault();
                return false;
            }
            
            // Empêcher les actions si le bouton est déjà occupé
            if (this.classList.contains('processing') || 
                this.innerHTML.includes('fa-spinner')) {
                event.preventDefault();
                return false;
            }
            
            // Marquer le bouton comme en cours de traitement
            this.classList.add('processing');
            
            const taskId = this.dataset.taskId;
            const newStatus = this.dataset.status;
            const currentButton = this;
            
            // Désactiver tous les boutons pendant le traitement
            statusButtons.forEach(btn => {
                btn.disabled = true;
            });
            
            // Afficher un indicateur de chargement
            currentButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // Appel AJAX pour mettre à jour le statut
            fetch('/tasks/update_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task_id: parseInt(taskId),
                    status: newStatus
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    updateTaskStatusUI(statusButtons, newStatus, currentButton);
                } else {
                    console.error('Erreur:', data.error);
                    alert('Erreur lors de la mise à jour du statut: ' + data.error);
                    resetButton(currentButton);
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Une erreur est survenue lors de la mise à jour');
                resetButton(currentButton);
            })
            .finally(() => {
                // Réactiver les boutons et supprimer le marqueur de traitement
                statusButtons.forEach(btn => {
                    btn.disabled = false;
                });
                currentButton.classList.remove('processing');
            });
        });
    });
}

// Met à jour l'interface utilisateur après changement de statut
function updateTaskStatusUI(statusButtons, newStatus, currentButton) {
    // Mettre à jour visuellement les boutons
    statusButtons.forEach(btn => {
        if (btn.dataset.status === newStatus) {
            btn.classList.remove('btn-outline-info', 'btn-outline-warning', 'btn-outline-success');
            if (newStatus === 'à faire') btn.classList.add('btn-info');
            else if (newStatus === 'en cours') btn.classList.add('btn-warning');
            else if (newStatus === 'terminé') btn.classList.add('btn-success');
        } else {
            btn.classList.remove('btn-info', 'btn-warning', 'btn-success');
            if (btn.dataset.status === 'à faire') btn.classList.add('btn-outline-info');
            else if (btn.dataset.status === 'en cours') btn.classList.add('btn-outline-warning');
            else if (btn.dataset.status === 'terminé') btn.classList.add('btn-outline-success');
        }
        btn.innerHTML = btn.dataset.status === 'à faire' ? 'À faire' : 
                        btn.dataset.status === 'en cours' ? 'En cours' : 'Terminé';
    });
    
    // Mettre à jour le badge de statut
    const statusBadge = document.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.className = `badge status-badge ${newStatus}`;
        statusBadge.textContent = newStatus;
    }
    
    // Ajouter un message de succès temporaire
    const statusMsg = document.createElement('div');
    statusMsg.className = 'alert alert-success mt-2 status-update-msg';
    statusMsg.innerHTML = `<i class="fas fa-check me-2"></i>Statut mis à jour avec succès!`;
    document.querySelector('.status-toggle').appendChild(statusMsg);
    
    // Supprimer le message après quelques secondes
    setTimeout(() => {
        statusMsg.remove();
    }, 3000);
    
    // Gérer la date de fin
    updateCompletionDate(newStatus);
}

// Met à jour la date de complétion dans l'UI
function updateCompletionDate(newStatus) {
    // Trouver la section où se trouve ou devrait se trouver la date de fin
    const infoColumn = document.querySelector('.col-md-6:last-child');
    if (!infoColumn) return;
    
    // Position où insérer/mettre à jour la date (après la ligne "Créée le")
    const createdDateElem = Array.from(infoColumn.querySelectorAll('p'))
        .find(p => p.textContent.includes('Créée le'));
    
    if (!createdDateElem) return; // Sortir si on ne trouve pas de référence
    
    // Supprimer d'abord tous les éléments de date de complétion existants
    const existingCompletedDates = infoColumn.querySelectorAll('.completed-date');
    existingCompletedDates.forEach(elem => elem.remove());
    
    // Pour les éléments générés par le serveur (sans classe spécifique)
    const serverCompletedDates = Array.from(infoColumn.querySelectorAll('p'))
        .filter(p => p.textContent.includes('Terminée le') && !p.classList.contains('completed-date'));
    serverCompletedDates.forEach(elem => elem.remove());
    
    // Si le statut est "terminé", ajouter un nouvel élément
    if (newStatus === 'terminé') {
        const now = new Date();
        const formattedDate = now.toLocaleDateString('fr-FR', {day: '2-digit', month: '2-digit', year: 'numeric'});
        
        // Créer un nouvel élément avec une classe spécifique
        const completedDateElem = document.createElement('p');
        completedDateElem.className = 'completed-date';
        completedDateElem.innerHTML = `<strong>Terminée le :</strong> ${formattedDate}`;
        
        // Insérer après la date de création
        createdDateElem.after(completedDateElem);
    }
}

// Réinitialiser le texte du bouton (en cas d'erreur)
function resetButton(button) {
    button.innerHTML = button.dataset.status === 'à faire' ? 'À faire' : 
                      button.dataset.status === 'en cours' ? 'En cours' : 'Terminé';
    button.disabled = false;
}

// Initialisation de la gestion des commentaires
function initCommentManagement() {
    // Boutons d'édition
    const editButtons = document.querySelectorAll('.edit-comment-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const commentContent = document.querySelector(`#comment-${commentId} .comment-content`);
            const editForm = document.querySelector(`#edit-form-${commentId}`);
            
            // Masquer le contenu et afficher le formulaire
            commentContent.style.display = 'none';
            editForm.style.display = 'block';
        });
    });
    
    // Boutons d'annulation
    const cancelButtons = document.querySelectorAll('.cancel-edit-btn');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const commentContent = document.querySelector(`#comment-${commentId} .comment-content`);
            const editForm = document.querySelector(`#edit-form-${commentId}`);
            
            // Réafficher le contenu et masquer le formulaire
            commentContent.style.display = 'block';
            editForm.style.display = 'none';
        });
    });
    
    // Timer pour les commentaires
    updateCommentTimers();
}

// Met à jour les minuteurs d'édition des commentaires
function updateCommentTimers() {
    document.querySelectorAll('.edit-timer').forEach(timer => {
        if (timer) {
            const minutesText = timer.textContent.trim();
            let minutes = parseInt(minutesText);
            
            if (!isNaN(minutes) && minutes > 0) {
                // Mettre à jour le timer chaque minute
                const intervalId = setInterval(() => {
                    minutes--;
                    if (minutes <= 0) {
                        // Temps écoulé, supprimer les éléments d'édition
                        const editButton = timer.closest('.comment-header').querySelector('.edit-comment-btn');
                        if (editButton) editButton.remove();
                        timer.remove();
                        
                        // Fermer le formulaire d'édition si ouvert
                        const commentItem = timer.closest('.comment-item');
                        const commentId = commentItem.id.split('-')[1];
                        const editForm = document.querySelector(`#edit-form-${commentId}`);
                        if (editForm && editForm.style.display !== 'none') {
                            const commentContent = commentItem.querySelector('.comment-content');
                            commentContent.style.display = 'block';
                            editForm.style.display = 'none';
                        }
                        
                        clearInterval(intervalId);
                    } else {
                        timer.textContent = `${minutes} min`;
                    }
                }, 60000); // Toutes les minutes
            }
        }
    });
}

function initCommentMentions() {
    const commentInput = document.querySelector('.comment-input');
    if (!commentInput) return;

    const projectId = commentInput.getAttribute('data-project-id');
    if (!projectId) {
        console.error('Project ID not found on comment input');
        return;
    }

    let mentionableUsers = [];
    let mentionDropdown = null;

    // Positionner le dropdown
    function positionDropdown(match) {
        if (!mentionDropdown) return;

        const inputRect = commentInput.getBoundingClientRect();
        const inputStyle = window.getComputedStyle(commentInput);
        const lineHeight = parseInt(inputStyle.lineHeight);
        const fontSize = parseInt(inputStyle.fontSize);
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Calculer la position du curseur
        const textBeforeCursor = commentInput.value.substring(0, match.index);
        const lines = textBeforeCursor.split('\n');
        const currentLineNumber = lines.length - 1;
        const currentLineText = lines[currentLineNumber];
        
        // Position horizontale basée sur la position du @
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        context.font = inputStyle.font;
        const textWidth = context.measureText(currentLineText).width;
        
        // Calculer la position exacte
        const left = inputRect.left + Math.min(textWidth, inputRect.width - mentionDropdown.offsetWidth);
        const top = inputRect.top + scrollTop + ((currentLineNumber + 1) * lineHeight);

        // Positionner le dropdown
        mentionDropdown.style.position = 'absolute';
        mentionDropdown.style.left = `${left}px`;
        mentionDropdown.style.top = `${top}px`;
        
        // S'assurer que le dropdown est visible dans la fenêtre
        const viewportHeight = window.innerHeight;
        const dropdownHeight = mentionDropdown.offsetHeight;
        const dropdownBottom = top + dropdownHeight - scrollTop;

        if (dropdownBottom > viewportHeight) {
            // Si le dropdown dépasse en bas, le placer au-dessus du curseur
            mentionDropdown.style.top = `${top - dropdownHeight - 5}px`;
        }
    }

    // Créer le dropdown pour les mentions
    function createMentionDropdown() {
        if (document.querySelector('.mention-dropdown')) {
            document.querySelector('.mention-dropdown').remove();
        }
        const dropdown = document.createElement('div');
        dropdown.className = 'mention-dropdown';
        dropdown.style.display = 'none';
        document.body.appendChild(dropdown);
        return dropdown;
    }

    // Charger les utilisateurs mentionnables
    async function loadMentionableUsers() {
        try {
            const response = await fetch(`/api/projects/${projectId}/mentionable-users`);
            if (!response.ok) throw new Error('Erreur lors du chargement des utilisateurs');
            mentionableUsers = await response.json();
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    // Gérer la saisie dans le champ de commentaire
    commentInput.addEventListener('input', function(e) {
        const cursorPosition = this.selectionStart;
        const textBeforeCursor = this.value.substring(0, cursorPosition);
        const match = textBeforeCursor.match(/@(\w*)$/);

        if (match) {
            const searchTerm = match[1].toLowerCase();
            const filteredUsers = mentionableUsers.filter(user => 
                user.name.toLowerCase().includes(searchTerm) ||
                user.email.toLowerCase().includes(searchTerm)
            );

            if (filteredUsers.length > 0) {
                if (!mentionDropdown) {
                    mentionDropdown = createMentionDropdown();
                }
                
                mentionDropdown.innerHTML = filteredUsers.map(user => `
                    <div class="mention-item" data-user-id="${user.id}">
                        <strong>${user.name}</strong>
                        <small class="text-muted d-block">${user.email}</small>
                    </div>
                `).join('');

                mentionDropdown.style.display = 'block';
                positionDropdown(match);

                // Gérer le clic sur un utilisateur
                mentionDropdown.querySelectorAll('.mention-item').forEach(item => {
                    item.addEventListener('click', function() {
                        const userId = this.dataset.userId;
                        const userName = this.querySelector('strong').textContent;
                        insertMention(userName, userId, match);
                        hideMentionDropdown();
                    });
                });
            } else {
                hideMentionDropdown();
            }
        } else {
            hideMentionDropdown();
        }
    });

    // Cacher le dropdown des mentions
    function hideMentionDropdown() {
        if (mentionDropdown) {
            mentionDropdown.style.display = 'none';
        }
    }

    // Insérer la mention dans le texte
    function insertMention(userName, userId, match) {
        const startPos = match.index;
        const endPos = commentInput.selectionStart;
        const beforeMention = commentInput.value.substring(0, startPos);
        const afterMention = commentInput.value.substring(endPos);
        
        const newText = `${beforeMention}@${userName}${afterMention}`;
        commentInput.value = newText;
        
        // Mettre à jour la liste des mentions
        const mentionsInput = commentInput.closest('form').querySelector('input[name="mentions"]');
        const mentions = JSON.parse(mentionsInput.value || '[]');
        mentions.push({ id: userId, name: userName });
        mentionsInput.value = JSON.stringify(mentions);
        
        // Placer le curseur après la mention
        const newCursorPos = startPos + userName.length + 1;
        commentInput.setSelectionRange(newCursorPos, newCursorPos);
    }

    // Gérer les clics en dehors du dropdown pour le fermer
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.mention-dropdown') && !e.target.closest('.comment-input')) {
            hideMentionDropdown();
        }
    });

    // Initialiser
    loadMentionableUsers();
    mentionDropdown = createMentionDropdown();

    // Nettoyer lors de la soumission du formulaire
    commentInput.closest('form').addEventListener('submit', function() {
        hideMentionDropdown();
    });
}

// Initialiser la page des tâches
export function initTasksPage() {
    if (document.querySelector('.status-btn')) {
        initStatusToggle();
    }
    
    if (document.querySelector('.edit-comment-btn')) {
        initCommentManagement();
    }

    if (document.querySelector('.comment-input')) {
        initCommentMentions();
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize tooltip for delete button separately
    const deleteBtn = document.querySelector('.delete-task-btn');
    if (deleteBtn) {
        new bootstrap.Tooltip(deleteBtn, {
            trigger: 'hover'
        });
    }
}