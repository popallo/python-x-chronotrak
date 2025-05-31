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
                <form method="POST" action="/comments/${data.comment.id}/reply">
                    <div class="mb-2">
                        <textarea class="form-control" name="content" rows="2" placeholder="Écrivez votre réponse..."></textarea>
                    </div>
                    <div class="d-flex justify-content-end gap-2">
                        <button type="button" class="btn btn-sm btn-outline-light cancel-reply-btn" data-comment-id="${data.comment.id}">Annuler</button>
                        <button type="submit" class="btn btn-sm btn-light">Répondre</button>
                    </div>
                </form>
            </div>
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
    const commentForm = document.querySelector('form[action*="/add_comment"]');
    if (!commentForm) return;
    
    commentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = {
            content: formData.get('content'),
            notify_all: formData.get('notify_all') === 'on',
            mentions: formData.get('mentions'),
            csrf_token: formData.get('csrf_token')
        };
        
        fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': data.csrf_token
            },
            body: JSON.stringify(data)
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