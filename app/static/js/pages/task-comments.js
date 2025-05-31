// Fonction pour mettre à jour l'interface après l'ajout d'un commentaire
function updateCommentsInterface(data) {
    const commentList = document.querySelector('.comment-list');
    if (!commentList) return;
    
    const commentHtml = `
        <div class="comment-item ${data.comment.is_own_comment ? 'own-comment' : ''}" id="comment-${data.comment.id}">
            <div class="comment-header">
                <span class="comment-author">${data.comment.user_name}</span>
                <div class="d-flex align-items-center">
                    <span class="comment-time">${data.comment.created_at}</span>
                    <div class="d-inline-block ms-2">
                        <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                        <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                data-comment-id="${data.comment.id}" title="Modifier">
                            <i class="fas fa-edit"></i>
                        </button>
                        <form action="/comments/${data.comment.id}/delete" method="POST" class="d-inline">
                            <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                                <i class="fas fa-trash"></i>
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="comment-content">
                ${data.comment.content}
            </div>
            <button type="button" class="reply-button" data-comment-id="${data.comment.id}">
                <i class="fas fa-reply me-1"></i>Répondre
            </button>
            <div class="comment-reply-form" id="reply-form-${data.comment.id}" style="display: none;">
                <form method="POST" action="/comments/${data.comment.id}/reply" class="reply-form">
                    <input type="hidden" name="csrf_token" value="${window.csrfToken}">
                    <div class="mb-2">
                        <textarea class="form-control" name="content" rows="2" placeholder="Écrivez votre réponse..."></textarea>
                    </div>
                    <div class="d-flex justify-content-end gap-2">
                        <button type="button" class="btn btn-sm btn-outline-light cancel-reply-btn" data-comment-id="${data.comment.id}">Annuler</button>
                        <button type="submit" class="btn btn-sm btn-light">Répondre</button>
                    </div>
                </form>
            </div>
            <div class="comment-replies" id="replies-${data.comment.id}"></div>
        </div>
    `;
    
    // Si c'est le premier commentaire, remplacer le message "Aucun commentaire"
    if (commentList.querySelector('.text-muted')) {
        commentList.innerHTML = commentHtml;
    } else {
        commentList.insertAdjacentHTML('afterbegin', commentHtml);
    }
    
    // Mettre à jour le compteur de commentaires
    const commentCount = document.querySelector('.card-header .badge');
    if (commentCount) {
        const currentCount = parseInt(commentCount.textContent) || 0;
        commentCount.textContent = currentCount + 1;
    }
    
    // Réinitialiser les événements pour le nouveau commentaire
    const newComment = document.getElementById(`comment-${data.comment.id}`);
    if (newComment) {
        // Réinitialiser le bouton de réponse
        const replyButton = newComment.querySelector('.reply-button');
        if (replyButton) {
            replyButton.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const replyForm = document.getElementById(`reply-form-${commentId}`);
                replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            });
        }

        // Réinitialiser le bouton d'annulation
        const cancelButton = newComment.querySelector('.cancel-reply-btn');
        if (cancelButton) {
            cancelButton.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const replyForm = document.getElementById(`reply-form-${commentId}`);
                replyForm.style.display = 'none';
            });
        }

        // Réinitialiser le formulaire de réponse
        const replyForm = newComment.querySelector('.reply-form');
        if (replyForm) {
            replyForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                
                fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.csrfToken
                    },
                    body: JSON.stringify({
                        content: formData.get('content'),
                        csrf_token: window.csrfToken
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Réinitialiser le formulaire
                        this.reset();
                        
                        // Masquer le formulaire
                        this.closest('.comment-reply-form').style.display = 'none';
                        
                        // Ajouter la réponse
                        const repliesContainer = document.getElementById(`replies-${data.comment.parent_id}`);
                        if (repliesContainer) {
                            const replyHtml = `
                                <div class="comment-reply ${data.comment.is_own_comment ? 'own-comment' : ''}" id="reply-${data.comment.id}">
                                    <div class="comment-header">
                                        <span class="comment-author">${data.comment.user_name}</span>
                                        <div class="d-flex align-items-center">
                                            <span class="comment-time">${data.comment.created_at}</span>
                                            <div class="d-inline-block ms-2">
                                                <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                                                <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                                        data-comment-id="${data.comment.id}" title="Modifier">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                <form action="/comments/${data.comment.id}/delete" method="POST" class="d-inline">
                                                    <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                                                        <i class="fas fa-trash"></i>
                                                    </button>
                                                </form>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="comment-content">
                                        ${data.comment.content}
                                    </div>
                                </div>
                            `;
                            repliesContainer.insertAdjacentHTML('beforeend', replyHtml);
                        }
                        
                        // Afficher le message de succès
                        if (data.message) {
                            showToast('success', data.message);
                        }
                    } else {
                        if (data.errors) {
                            // Afficher les erreurs de validation
                            Object.entries(data.errors).forEach(([field, error]) => {
                                showToast('danger', error);
                            });
                        } else {
                            showToast('danger', data.error || 'Une erreur est survenue');
                        }
                    }
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    showToast('danger', 'Une erreur est survenue lors de l\'ajout de la réponse');
                });
            });
        }
    }
    
    // Afficher le message de succès
    if (data.message) {
        showToast('success', data.message);
    }
}

// Fonction pour afficher un toast
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
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
    
    // Supprimer le toast après qu'il soit caché
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
    // Initialiser les formulaires de réponse existants
    document.querySelectorAll('.reply-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.csrfToken
                },
                body: JSON.stringify({
                    content: formData.get('content'),
                    csrf_token: window.csrfToken
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Réinitialiser le formulaire
                    this.reset();
                    
                    // Masquer le formulaire
                    this.closest('.comment-reply-form').style.display = 'none';
                    
                    // Ajouter la réponse
                    const repliesContainer = document.getElementById(`replies-${data.comment.parent_id}`);
                    if (repliesContainer) {
                        const replyHtml = `
                            <div class="comment-reply ${data.comment.is_own_comment ? 'own-comment' : ''}" id="reply-${data.comment.id}">
                                <div class="comment-header">
                                    <span class="comment-author">${data.comment.user_name}</span>
                                    <div class="d-flex align-items-center">
                                        <span class="comment-time">${data.comment.created_at}</span>
                                        <div class="d-inline-block ms-2">
                                            <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                                            <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                                    data-comment-id="${data.comment.id}" title="Modifier">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <form action="/comments/${data.comment.id}/delete" method="POST" class="d-inline">
                                                <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                                <div class="comment-content">
                                    ${data.comment.content}
                                </div>
                            </div>
                        `;
                        repliesContainer.insertAdjacentHTML('beforeend', replyHtml);
                    }
                    
                    // Afficher le message de succès
                    if (data.message) {
                        showToast('success', data.message);
                    }
                } else {
                    if (data.errors) {
                        // Afficher les erreurs de validation
                        Object.entries(data.errors).forEach(([field, error]) => {
                            showToast('danger', error);
                        });
                    } else {
                        showToast('danger', data.error || 'Une erreur est survenue');
                    }
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showToast('danger', 'Une erreur est survenue lors de l\'ajout de la réponse');
            });
        });
    });

    // Initialiser les boutons de réponse existants
    document.querySelectorAll('.reply-button').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
        });
    });

    // Initialiser les boutons d'annulation existants
    document.querySelectorAll('.cancel-reply-btn').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            replyForm.style.display = 'none';
        });
    });

    // Initialiser le formulaire de commentaire principal
    const commentForm = document.querySelector('form[action*="/add_comment"]');
    if (!commentForm) return;
    
    commentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.csrfToken
            },
            body: JSON.stringify({
                content: formData.get('content'),
                notify_all: formData.get('notify_all') === 'on',
                mentions: formData.get('mentions'),
                csrf_token: window.csrfToken
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Réinitialiser le formulaire
                this.reset();
                
                // Mettre à jour l'interface
                updateCommentsInterface(data);
            } else {
                if (data.errors) {
                    // Afficher les erreurs de validation
                    Object.entries(data.errors).forEach(([field, error]) => {
                        showToast('danger', error);
                    });
                } else {
                    showToast('danger', data.error || 'Une erreur est survenue');
                }
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('danger', 'Une erreur est survenue lors de l\'ajout du commentaire');
        });
    });
}); 