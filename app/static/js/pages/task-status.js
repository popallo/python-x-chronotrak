import { CONFIG, utils } from '../utils.js';

// Fonction pour mettre à jour l'interface après le changement de statut
function updateStatusInterface(data) {
    // Mettre à jour les boutons de statut
    const statusButtons = document.querySelectorAll('.status-btn');
    statusButtons.forEach(btn => {
        const status = btn.dataset.status;
        btn.classList.remove('btn-info', 'btn-warning', 'btn-success', 'btn-outline-info', 'btn-outline-warning', 'btn-outline-success');
        
        if (status === data.status) {
            if (status === 'à faire') btn.classList.add('btn-info');
            else if (status === 'en cours') btn.classList.add('btn-warning');
            else if (status === 'terminé') btn.classList.add('btn-success');
        } else {
            if (status === 'à faire') btn.classList.add('btn-outline-info');
            else if (status === 'en cours') btn.classList.add('btn-outline-warning');
            else if (status === 'terminé') btn.classList.add('btn-outline-success');
        }
    });
    
    // Mettre à jour la date de fin si la tâche est terminée
    const completionDateElement = document.querySelector('.completion-date');
    if (completionDateElement) {
        if (data.completed_at) {
            completionDateElement.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle me-2 text-muted"></i>
                    <span>Terminée le ${data.completed_at}</span>
                </div>
            `;
        } else {
            completionDateElement.innerHTML = '';
        }
    }
    
    // Afficher le message de succès
    showToast('success', 'Statut mis à jour avec succès');
}

// Fonction pour afficher un toast
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Ajouter une icône en fonction du type de message
    let icon = '';
    switch(type) {
        case 'success':
            icon = '<i class="fas fa-check-circle me-2"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
            break;
        case 'danger':
            icon = '<i class="fas fa-times-circle me-2"></i>';
            break;
    }
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${icon}${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {
        delay: type === 'warning' ? 5000 : 3000 // Les avertissements restent plus longtemps
    });
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

async function handleStatusUpdate(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    const data = await utils.fetchWithCsrf('/tasks/update_status', {
        method: 'POST',
        body: JSON.stringify({
            task_id: formData.get('task_id'),
            status: formData.get('status'),
            csrf_token: CONFIG.csrfToken
        })
    });

    if (data.success) {
        updateTaskStatus(data.task_id, data.status);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    const statusButtons = document.querySelectorAll('.status-btn');
    if (!statusButtons.length) return;
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.taskId;
            const newStatus = this.dataset.status;
            
            // Désactiver tous les boutons pendant la requête
            statusButtons.forEach(btn => btn.disabled = true);
            
            // Ajouter une classe pour indiquer le traitement
            this.classList.add('processing');
            
            fetch('/tasks/update_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({
                    task_id: taskId,
                    status: newStatus
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateStatusInterface(data);
                } else {
                    showToast('danger', data.error || 'Une erreur est survenue');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showToast('danger', 'Une erreur est survenue lors de la mise à jour du statut');
            })
            .finally(() => {
                // Réactiver les boutons et supprimer le marqueur de traitement
                statusButtons.forEach(btn => btn.disabled = false);
                this.classList.remove('processing');
            });
        });
    });
}); 