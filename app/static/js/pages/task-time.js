// Fonction pour formater le temps
function formatTime(hours) {
    const totalMinutes = Math.round(hours * 60);
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    
    if (h > 0) {
        return `${h}h${m > 0 ? ` ${m}min` : ''}`;
    }
    return `${m}min`;
}

// Fonction pour mettre à jour l'interface après l'ajout de temps
function updateTimeInterface(data) {
    // Mettre à jour le temps total
    const timeBadge = document.querySelector('.badge[title="Temps total passé sur la tâche"]');
    if (timeBadge) {
        timeBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(data.task.actual_time)}`;
    }
    
    // Mettre à jour le crédit restant si activé
    const creditBadge = document.querySelector('.badge[title="Crédit restant du projet"]');
    if (creditBadge && data.task.remaining_credit !== null) {
        creditBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(data.task.remaining_credit)}`;
        
        // Mettre à jour la classe de couleur
        creditBadge.className = 'badge text-white d-flex align-items-center';
        if (data.task.remaining_credit < 2) {
            creditBadge.classList.add('bg-danger');
        } else if (data.task.remaining_credit < 5) {
            creditBadge.classList.add('bg-warning');
        } else {
            creditBadge.classList.add('bg-success');
        }
    }
    
    // Ajouter la nouvelle entrée de temps à la liste
    const timeList = document.querySelector('.time-history .list-group');
    if (timeList) {
        const timeEntry = data.time_entry;
        const entryHtml = `
            <div class="list-group-item py-1 px-2 time-entry-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-minus me-1 text-danger"></i>
                        <span class="text-danger">
                            ${formatTime(timeEntry.hours)}
                        </span>
                    </div>
                    <small class="text-muted">${timeEntry.created_at}</small>
                </div>
                <small class="text-muted d-block">${timeEntry.user_name}</small>
                ${timeEntry.description ? `<small class="text-muted d-block mt-1">${timeEntry.description}</small>` : ''}
            </div>
        `;
        
        // Si la liste est vide, remplacer le message "Aucun temps enregistré"
        if (timeList.querySelector('.text-muted.small')) {
            timeList.innerHTML = entryHtml;
        } else {
            timeList.insertAdjacentHTML('afterbegin', entryHtml);
        }
    }
    
    // Afficher les messages de succès/alerte
    if (data.message) {
        showToast('success', data.message);
    }
    if (data.warning) {
        showToast('warning', data.warning);
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
    const timeForm = document.querySelector('#timeEntryModal form');
    if (!timeForm) return;
    
    timeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = {
            hours: parseFloat(formData.get('hours')),
            description: formData.get('description'),
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
                // Fermer le modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('timeEntryModal'));
                modal.hide();
                
                // Réinitialiser le formulaire
                this.reset();
                
                // Mettre à jour l'interface
                updateTimeInterface(data);
            } else {
                showToast('danger', data.error || 'Une erreur est survenue');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('danger', 'Une erreur est survenue lors de l\'enregistrement du temps');
        });
    });
}); 