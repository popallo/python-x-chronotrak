// Fonction pour récupérer le temps restant
async function fetchRemainingCredit(taskSlug) {
    try {
        const response = await fetch(`/api/tasks/${taskSlug}/remaining-credit`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la récupération du crédit restant');
        }
        
        const data = await response.json();
        return data.remaining_credit;
    } catch (error) {
        console.error('Erreur:', error);
        return null;
    }
}

// Fonction pour formater le temps
function formatTime(hours) {
    // Si hours est null ou undefined, retourner '0 min'
    if (hours === null || hours === undefined) {
        return '0 min';
    }
    
    // Convertir en minutes totales
    const totalMinutes = Math.round(hours * 60);
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    
    // Formater le temps
    if (h > 0) {
        return `${h}h${m > 0 ? ` ${m}min` : ''}`;
    }
    return `${m}min`;
}

// Fonction pour mettre à jour l'interface après l'ajout de temps
async function updateTimeInterface(data) {
    // Mettre à jour le temps total
    const timeBadge = document.querySelector('.badge[title="Temps total passé sur la tâche"]');
    if (timeBadge) {
        timeBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(data.task.actual_time)}`;
    }
    
    // Mettre à jour le crédit restant directement depuis les données reçues
    if (data.task.remaining_credit !== null && data.task.remaining_credit !== undefined) {
        const oldBadge = document.getElementById('remaining-credit-badge');
        if (oldBadge) {
            // Créer un nouveau badge
            const newBadge = document.createElement('span');
            newBadge.id = 'remaining-credit-badge';
            newBadge.className = `badge ${data.task.remaining_credit < 2 ? 'bg-danger' : 
                                 data.task.remaining_credit < 5 ? 'bg-warning' : 
                                 'bg-success'} text-white d-flex align-items-center`;
            newBadge.setAttribute('data-bs-toggle', 'tooltip');
            newBadge.setAttribute('title', 'Crédit restant du projet');
            newBadge.innerHTML = `<i class="fas fa-clock me-1"></i>${formatTime(data.task.remaining_credit)}`;
            
            // Remplacer l'ancien badge par le nouveau
            oldBadge.parentNode.replaceChild(newBadge, oldBadge);
            
            // Réinitialiser le tooltip Bootstrap
            const tooltip = bootstrap.Tooltip.getInstance(newBadge);
            if (tooltip) {
                tooltip.dispose();
            }
            new bootstrap.Tooltip(newBadge);

            // Mettre à jour aussi l'alerte dans le modal si elle existe
            const creditAlert = document.querySelector('#timeEntryModal .alert');
            if (creditAlert) {
                const alertClass = data.task.remaining_credit < 2 ? 'alert-danger' : 
                                 data.task.remaining_credit < 5 ? 'alert-warning' : 
                                 'alert-success';
                creditAlert.className = `alert ${alertClass} mb-4 no-auto-close`;
                const creditText = creditAlert.querySelector('strong');
                if (creditText) {
                    creditText.textContent = formatTime(data.task.remaining_credit);
                    creditText.className = `${data.task.remaining_credit < 2 ? 'text-danger' : 
                                          data.task.remaining_credit < 5 ? 'text-warning' : 
                                          'text-success'} ms-2`;
                }
            }
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
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur réseau');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Retirer le focus du bouton submit avant de fermer le modal
                document.activeElement.blur();
                
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