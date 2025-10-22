// Fonction utilitaire pour afficher les toasts
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
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
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Fonction pour créer un élément de commentaire
function createCommentElement(comment) {
    const div = document.createElement('div');
    div.className = `comment-item ${comment.is_own_comment ? 'own-comment' : ''}`;
    div.id = `comment-${comment.id}`;
    
    div.innerHTML = `
        <div class="comment-header">
            <span class="comment-author">${comment.user_name}</span>
            <div class="d-flex align-items-center">
                <span class="comment-time">${comment.created_at}</span>
                <div class="d-inline-block ms-2">
                    <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                    <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                            data-comment-id="${comment.id}" title="Modifier">
                        <i class="fas fa-edit"></i>
                    </button>
                    <form action="/tasks/comment/${comment.id}/delete" method="POST" class="d-inline delete-comment-form">
                        <input type="hidden" name="csrf_token" value="${window.csrfToken}">
                        <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                            <i class="fas fa-trash"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
        <div class="comment-content">${comment.content}</div>
        <button type="button" class="reply-button" data-comment-id="${comment.id}">
            <i class="fas fa-reply me-1"></i>Répondre
        </button>
        <form id="edit-form-${comment.id}" method="POST" action="/tasks/comment/${comment.id}/edit" class="edit-comment-form" style="display: none;">
            <input type="hidden" name="csrf_token" value="${window.csrfToken}">
            <div class="mb-2">
                <textarea class="form-control" name="content" rows="2"></textarea>
            </div>
            <div class="d-flex justify-content-end gap-2">
                <button type="button" class="btn btn-sm btn-outline-light cancel-edit-btn" data-comment-id="${comment.id}">Annuler</button>
                <button type="submit" class="btn btn-sm btn-light">Modifier</button>
            </div>
        </form>
    `;

    // Les gestionnaires d'événements sont maintenant gérés par la délégation d'événements
    // dans la fonction d'initialisation, donc pas besoin de les attacher ici

    return div;
}

// Gestionnaire de clic sur le bouton d'édition
function handleEditButtonClick(e) {
    const button = e.target.closest('.edit-comment-btn');
    const commentId = button.dataset.commentId;
    const commentElement = document.getElementById(`comment-${commentId}`) || document.getElementById(`reply-${commentId}`);
    const contentElement = commentElement.querySelector('.comment-content');
    const editForm = document.getElementById(`edit-form-${commentId}`);
    
    if (editForm && contentElement) {
        // Afficher le formulaire d'édition
        contentElement.style.display = 'none';
        editForm.style.display = 'block';
        
        // Remplir le contenu actuel
        const textarea = editForm.querySelector('textarea');
        if (textarea) {
            textarea.value = contentElement.textContent.trim();
        }
    }
}

// Gestionnaire de soumission de formulaire de commentaire
async function handleCommentSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': window.csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de l\'ajout du commentaire');
        }

        const data = await response.json();
        if (data.success) {
            // Ajouter le nouveau commentaire à la liste
            let commentList = document.querySelector('.comment-list');
            if (!commentList) {
                // Si c'est le premier commentaire, créer la liste
                const cardBody = form.closest('.card-body');
                cardBody.querySelector('p.text-muted')?.remove();
                commentList = document.createElement('div');
                commentList.className = 'comment-list';
                cardBody.appendChild(commentList);
            }

            // Créer et ajouter le commentaire
            const commentElement = createCommentElement(data.comment);
            commentList.insertBefore(commentElement, commentList.firstChild);

            // Réinitialiser le formulaire
            form.reset();
            const commentInput = form.querySelector('.comment-input');
            if (commentInput) {
                commentInput.value = '';
            }

            // Mettre à jour le compteur
            const badge = document.querySelector('.card-header .badge');
            if (badge) {
                const currentCount = parseInt(badge.textContent);
                badge.textContent = currentCount + 1;
            }

            showToast('Commentaire ajouté avec succès', 'success');
        } else {
            throw new Error(data.error || 'Erreur lors de l\'ajout du commentaire');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message, 'error');
    }
}

// Gestionnaire de suppression de commentaire
async function handleDeleteSubmit(e) {
    e.preventDefault();
    const form = e.target;

    if (!confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ?')) {
        return;
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRF-Token': window.csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erreur lors de la suppression du commentaire');
        }

        const data = await response.json();
        if (data.success) {
            // Supprimer l'élément du DOM
            const commentElement = form.closest('.comment-item, .comment-reply');
            if (commentElement) {
                commentElement.remove();

                // Mettre à jour le compteur seulement pour les commentaires principaux
                if (commentElement.classList.contains('comment-item')) {
                    const badge = document.querySelector('.card-header .badge');
                    if (badge) {
                        const currentCount = parseInt(badge.textContent);
                        badge.textContent = Math.max(0, currentCount - 1);
                    }

                    // Si c'était le dernier commentaire, afficher le message "Aucun commentaire"
                    const commentList = document.querySelector('.comment-list');
                    if (commentList && !commentList.children.length) {
                        commentList.remove();
                        const cardBody = document.querySelector('.card-body');
                        const noCommentMessage = document.createElement('p');
                        noCommentMessage.className = 'text-muted';
                        noCommentMessage.textContent = 'Aucun commentaire pour le moment.';
                        cardBody.appendChild(noCommentMessage);
                    }
                }

                showToast('Commentaire supprimé avec succès', 'success');
            }
        } else {
            throw new Error(data.error || 'Erreur lors de la suppression du commentaire');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message, 'error');
    }
}

// Gestionnaire de soumission du formulaire d'édition
async function handleEditSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': window.csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la modification du commentaire');
        }

        const data = await response.json();
        if (data.success) {
            // Mettre à jour le contenu du commentaire
            const commentId = form.id.replace('edit-form-', '');
            const commentElement = document.getElementById(`comment-${commentId}`) || document.getElementById(`reply-${commentId}`);
            const contentElement = commentElement.querySelector('.comment-content');
            
            if (contentElement) {
                contentElement.textContent = data.comment.content;
            }

            // Masquer le formulaire d'édition et afficher le contenu
            form.style.display = 'none';
            contentElement.style.display = 'block';

            showToast('Commentaire modifié avec succès', 'success');
        } else {
            throw new Error(data.error || 'Erreur lors de la modification du commentaire');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message, 'error');
    }
}

// Gestionnaire de clic sur le bouton de réponse
function handleReplyButtonClick(e) {
    const button = e.target.closest('.reply-button');
    const commentId = button.dataset.commentId;
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    
    if (replyForm) {
        replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
        
        // Gérer l'annulation
        const cancelButton = replyForm.querySelector('.cancel-reply-btn');
        if (cancelButton) {
            cancelButton.onclick = () => {
                replyForm.style.display = 'none';
                replyForm.reset();
            };
        }
    }
}

// Gestionnaire de soumission de formulaire de réponse
async function handleReplySubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': window.csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de l\'ajout de la réponse');
        }

        const data = await response.json();
        if (data.success) {
            // Ajouter la nouvelle réponse à la liste
            // Extraire l'ID du commentaire parent depuis l'URL de l'action
            const urlParts = form.action.split('/');
            const commentId = urlParts[urlParts.length - 2]; // Avant-dernière partie de l'URL (avant "reply")
            
            const commentElement = document.getElementById(`comment-${commentId}`);
            
            if (!commentElement) {
                throw new Error('Élément de commentaire non trouvé');
            }
            
            let repliesContainer = commentElement.querySelector('.comment-replies');
            
            if (!repliesContainer) {
                // Créer le conteneur de réponses s'il n'existe pas
                repliesContainer = document.createElement('div');
                repliesContainer.className = 'comment-replies';
                commentElement.appendChild(repliesContainer);
            }

            // Créer et ajouter la réponse
            const replyElement = createReplyElement(data.comment);
            repliesContainer.appendChild(replyElement);

            // Masquer le formulaire et le réinitialiser
            form.style.display = 'none';
            form.reset();

            showToast('Réponse ajoutée avec succès', 'success');
        } else {
            throw new Error(data.error || 'Erreur lors de l\'ajout de la réponse');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast(error.message, 'error');
    }
}

// Fonction pour créer un élément de réponse
function createReplyElement(reply) {
    const div = document.createElement('div');
    div.className = `comment-reply ${reply.is_own_comment ? 'own-comment' : ''}`;
    div.id = `reply-${reply.id}`;
    
    div.innerHTML = `
        <div class="comment-header">
            <span class="comment-author">${reply.user_name}</span>
            <div class="d-flex align-items-center">
                <span class="comment-time">${reply.created_at}</span>
                ${reply.is_own_comment ? `
                    <div class="d-inline-block ms-2">
                        <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                        <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                data-comment-id="${reply.id}" title="Modifier">
                            <i class="fas fa-edit"></i>
                        </button>
                        <form action="/tasks/comment/${reply.id}/delete" method="POST" class="d-inline delete-comment-form">
                            <input type="hidden" name="csrf_token" value="${window.csrfToken}">
                            <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                                <i class="fas fa-trash"></i>
                            </button>
                        </form>
                    </div>
                ` : ''}
            </div>
        </div>
        <div class="comment-content">${reply.content}</div>
        <form id="edit-form-${reply.id}" method="POST" action="/tasks/comment/${reply.id}/edit" class="edit-comment-form" style="display: none;">
            <input type="hidden" name="csrf_token" value="${window.csrfToken}">
            <div class="mb-2">
                <textarea class="form-control" name="content" rows="2"></textarea>
            </div>
            <div class="d-flex justify-content-end gap-2">
                <button type="button" class="btn btn-sm btn-outline-light cancel-edit-btn" data-comment-id="${reply.id}">Annuler</button>
                <button type="submit" class="btn btn-sm btn-light">Modifier</button>
            </div>
        </form>
    `;

    return div;
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser le formulaire de commentaire principal
    const commentForm = document.querySelector('form[action*="add_comment"]');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmit);
    }

    // Utiliser la délégation d'événements pour les formulaires de suppression
    // Cela fonctionne même pour les éléments ajoutés dynamiquement
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('delete-comment-form')) {
            handleDeleteSubmit(e);
        }
    });

    // Utiliser la délégation d'événements pour les boutons de réponse
    document.addEventListener('click', function(e) {
        if (e.target.closest('.reply-button')) {
            handleReplyButtonClick(e);
        }
    });

    // Utiliser la délégation d'événements pour les boutons d'édition
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-comment-btn')) {
            handleEditButtonClick(e);
        }
    });

    // Utiliser la délégation d'événements pour les formulaires d'édition
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('edit-comment-form')) {
            handleEditSubmit(e);
        }
    });

    // Utiliser la délégation d'événements pour les formulaires de réponse
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('reply-form')) {
            handleReplySubmit(e);
        }
    });

    // Utiliser la délégation d'événements pour les boutons d'annulation d'édition
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('cancel-edit-btn')) {
            const commentId = e.target.dataset.commentId;
            const commentElement = document.getElementById(`comment-${commentId}`) || document.getElementById(`reply-${commentId}`);
            const contentElement = commentElement.querySelector('.comment-content');
            const editForm = document.getElementById(`edit-form-${commentId}`);
            
            if (editForm && contentElement) {
                contentElement.style.display = 'block';
                editForm.style.display = 'none';
            }
        }
    });
}); 