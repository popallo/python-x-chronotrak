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
    `;

    // Ajouter les gestionnaires d'événements
    const deleteForm = div.querySelector('.delete-comment-form');
    if (deleteForm) {
        deleteForm.addEventListener('submit', handleDeleteSubmit);
    }

    const replyButton = div.querySelector('.reply-button');
    if (replyButton) {
        replyButton.addEventListener('click', handleReplyButtonClick);
    }

    return div;
}

// Gestionnaire de clic sur le bouton d'édition
function handleEditButtonClick(e) {
    const commentId = e.currentTarget.dataset.commentId;
    const commentElement = document.getElementById(`comment-${commentId}`);
    const contentElement = commentElement.querySelector('.comment-content');
    const editForm = document.getElementById(`edit-form-${commentId}`);
    
    if (editForm) {
        // Afficher le formulaire d'édition
        contentElement.style.display = 'none';
        editForm.style.display = 'block';
        
        // Remplir le contenu actuel
        const textarea = editForm.querySelector('textarea');
        if (textarea) {
            textarea.value = contentElement.textContent.trim();
        }
        
        // Gérer l'annulation
        const cancelButton = editForm.querySelector('.cancel-edit-btn');
        if (cancelButton) {
            cancelButton.onclick = () => {
                contentElement.style.display = 'block';
                editForm.style.display = 'none';
            };
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

                // Mettre à jour le compteur
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

// Gestionnaire de clic sur le bouton de réponse
function handleReplyButtonClick(e) {
    const button = e.target;
    const commentId = button.dataset.commentId;
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    
    if (replyForm) {
        replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser le formulaire de commentaire principal
    const commentForm = document.querySelector('form[action*="add_comment"]');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmit);
    }

    // Initialiser les formulaires de suppression existants
    document.querySelectorAll('.delete-comment-form').forEach(form => {
        form.addEventListener('submit', handleDeleteSubmit);
    });

    // Initialiser les boutons de réponse existants
    document.querySelectorAll('.reply-button').forEach(button => {
        button.addEventListener('click', handleReplyButtonClick);
    });
}); 