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

// Initialiser la page des tâches
export function initTasksPage() {
    if (document.querySelector('.status-btn')) {
        initStatusToggle();
    }
    
    if (document.querySelector('.edit-comment-btn')) {
        initCommentManagement();
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