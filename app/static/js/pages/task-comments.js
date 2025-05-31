// Configuration globale
const CONFIG = {
    csrfToken: window.csrfToken,
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': window.csrfToken
    }
};

// Fonctions utilitaires
const utils = {
    showToast(type, message) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    },

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    },

    handleApiResponse(data) {
        if (data.success) {
            if (data.message) {
                this.showToast('success', data.message);
            }
            return true;
        } else {
            if (data.errors) {
                Object.entries(data.errors).forEach(([field, error]) => {
                    this.showToast('danger', error);
                });
            } else {
                this.showToast('danger', data.error || 'Une erreur est survenue');
            }
            return false;
        }
    }
};

// Gestionnaire de commentaires
const CommentManager = {
    // Templates HTML
    templates: {
        comment: (data) => `
            <div class="comment-item ${data.is_own_comment ? 'own-comment' : ''}" id="comment-${data.id}">
                <div class="comment-header">
                    <span class="comment-author">${data.user_name}</span>
                    <div class="d-flex align-items-center">
                        <span class="comment-time">${data.created_at}</span>
                        <div class="d-inline-block ms-2">
                            <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                            <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                    data-comment-id="${data.id}" title="Modifier">
                                <i class="fas fa-edit"></i>
                            </button>
                            <form action="/comments/${data.id}/delete" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="comment-content">${data.content}</div>
                <button type="button" class="reply-button" data-comment-id="${data.id}">
                    <i class="fas fa-reply me-1"></i>Répondre
                </button>
                <div class="comment-reply-form" id="reply-form-${data.id}" style="display: none;">
                    <form method="POST" action="/comments/${data.id}/reply" class="reply-form">
                        <input type="hidden" name="csrf_token" value="${CONFIG.csrfToken}">
                        <div class="mb-2">
                            <textarea class="form-control" name="content" rows="2" placeholder="Écrivez votre réponse..."></textarea>
                        </div>
                        <div class="d-flex justify-content-end gap-2">
                            <button type="button" class="btn btn-sm btn-outline-light cancel-reply-btn" data-comment-id="${data.id}">Annuler</button>
                            <button type="submit" class="btn btn-sm btn-light">Répondre</button>
                        </div>
                    </form>
                </div>
                <div class="comment-replies" id="replies-${data.id}"></div>
            </div>
        `,

        reply: (data) => `
            <div class="comment-reply ${data.is_own_comment ? 'own-comment' : ''}" id="reply-${data.id}">
                <div class="comment-header">
                    <span class="comment-author">${data.user_name}</span>
                    <div class="d-flex align-items-center">
                        <span class="comment-time">${data.created_at}</span>
                        <div class="d-inline-block ms-2">
                            <span class="edit-timer" title="Temps restant pour éditer">10 min</span>
                            <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                    data-comment-id="${data.id}" title="Modifier">
                                <i class="fas fa-edit"></i>
                            </button>
                            <form action="/comments/${data.id}/delete" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-sm btn-outline-secondary" title="Supprimer">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="comment-content">${data.content}</div>
            </div>
        `
    },

    // Méthodes
    updateInterface(data) {
        const commentList = document.querySelector('.comment-list');
        if (!commentList) return;

        // Ajouter le nouveau commentaire
        if (commentList.querySelector('.text-muted')) {
            commentList.innerHTML = this.templates.comment(data.comment);
        } else {
            commentList.insertAdjacentHTML('afterbegin', this.templates.comment(data.comment));
        }

        // Mettre à jour le compteur
        const commentCount = document.querySelector('.card-header .badge');
        if (commentCount) {
            const currentCount = parseInt(commentCount.textContent) || 0;
            commentCount.textContent = currentCount + 1;
        }

        // Initialiser les événements pour le nouveau commentaire
        this.initializeCommentEvents(document.getElementById(`comment-${data.comment.id}`));
        
        // Afficher le message de succès
        if (data.message) {
            utils.showToast('success', data.message);
        }
    },

    initializeCommentEvents(commentElement) {
        if (!commentElement) return;

        // Bouton de réponse
        const replyButton = commentElement.querySelector('.reply-button');
        if (replyButton) {
            replyButton.addEventListener('click', () => {
                const replyForm = document.getElementById(`reply-form-${replyButton.dataset.commentId}`);
                replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            });
        }

        // Bouton d'annulation
        const cancelButton = commentElement.querySelector('.cancel-reply-btn');
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                const replyForm = document.getElementById(`reply-form-${cancelButton.dataset.commentId}`);
                replyForm.style.display = 'none';
            });
        }

        // Formulaire de réponse
        const replyForm = commentElement.querySelector('.reply-form');
        if (replyForm) {
            replyForm.addEventListener('submit', this.handleReplySubmit.bind(this));
        }
    },

    async handleReplySubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: CONFIG.headers,
                body: JSON.stringify({
                    content: formData.get('content'),
                    csrf_token: CONFIG.csrfToken
                })
            });

            const data = await response.json();
            if (utils.handleApiResponse(data)) {
                form.reset();
                form.closest('.comment-reply-form').style.display = 'none';

                const repliesContainer = document.getElementById(`replies-${data.comment.parent_id}`);
                if (repliesContainer) {
                    repliesContainer.insertAdjacentHTML('beforeend', this.templates.reply(data.comment));
                }
            }
        } catch (error) {
            console.error('Erreur:', error);
            utils.showToast('danger', 'Une erreur est survenue lors de l\'ajout de la réponse');
        }
    },

    async handleCommentSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: CONFIG.headers,
                body: JSON.stringify({
                    content: formData.get('content'),
                    notify_all: formData.get('notify_all') === 'on',
                    mentions: formData.get('mentions'),
                    csrf_token: CONFIG.csrfToken
                })
            });

            const data = await response.json();
            if (utils.handleApiResponse(data)) {
                form.reset();
                this.updateInterface(data);
            }
        } catch (error) {
            console.error('Erreur:', error);
            utils.showToast('danger', 'Une erreur est survenue lors de l\'ajout du commentaire');
        }
    },

    initialize() {
        // Initialiser les formulaires de réponse existants
        document.querySelectorAll('.reply-form').forEach(form => {
            form.addEventListener('submit', this.handleReplySubmit.bind(this));
        });

        // Initialiser les boutons de réponse existants
        document.querySelectorAll('.reply-button').forEach(button => {
            button.addEventListener('click', () => {
                const replyForm = document.getElementById(`reply-form-${button.dataset.commentId}`);
                replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            });
        });

        // Initialiser les boutons d'annulation existants
        document.querySelectorAll('.cancel-reply-btn').forEach(button => {
            button.addEventListener('click', () => {
                const replyForm = document.getElementById(`reply-form-${button.dataset.commentId}`);
                replyForm.style.display = 'none';
            });
        });

        // Initialiser le formulaire de commentaire principal
        const commentForm = document.querySelector('form[action*="/add_comment"]');
        if (commentForm) {
            commentForm.addEventListener('submit', this.handleCommentSubmit.bind(this));
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => CommentManager.initialize()); 