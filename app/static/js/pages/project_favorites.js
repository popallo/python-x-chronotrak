/**
 * Module pour la gestion des favoris de projets
 * Gère le drag & drop et les boutons de favoris
 */

import { utils } from '../utils.js';

/**
 * Initialise le système de favoris pour les projets
 */
function initProjectFavorites() {
    initializeDragAndDrop();
    initializeFavoriteButtons();
}

/**
 * Initialise le système de drag & drop
 */
function initializeDragAndDrop() {
    const projectCards = document.querySelectorAll('.project-card[draggable="true"]');
    const favoritesDropZone = document.getElementById('favorites-drop-zone');
    
    if (!favoritesDropZone) return;
    
    projectCards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });
    
    favoritesDropZone.addEventListener('dragover', handleDragOver);
    favoritesDropZone.addEventListener('dragleave', handleDragLeave);
    favoritesDropZone.addEventListener('drop', handleDrop);
    
    // Afficher la zone de drop quand on commence à glisser
    document.addEventListener('dragstart', function(e) {
        if (e.target.classList.contains('project-card')) {
            favoritesDropZone.style.display = 'block';
        }
    });
    
    // Masquer la zone de drop quand on arrête de glisser
    document.addEventListener('dragend', function(e) {
        if (e.target.classList.contains('project-card')) {
            favoritesDropZone.style.display = 'none';
            favoritesDropZone.classList.remove('drag-over');
        }
    });
}

/**
 * Initialise les boutons de favoris
 */
function initializeFavoriteButtons() {
    const favoriteButtons = document.querySelectorAll('.toggle-favorite');
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const projectSlug = this.dataset.projectSlug;
            toggleFavorite(projectSlug);
        });
    });
}

/**
 * Gère le début du glissement
 */
function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.target.outerHTML);
    e.dataTransfer.setData('project-slug', e.target.dataset.projectSlug);
}

/**
 * Gère la fin du glissement
 */
function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

/**
 * Gère le survol de la zone de drop
 */
function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    e.target.closest('.favorites-drop-zone').classList.add('drag-over');
}

/**
 * Gère la sortie de la zone de drop
 */
function handleDragLeave(e) {
    e.target.closest('.favorites-drop-zone').classList.remove('drag-over');
}

/**
 * Gère le dépôt dans la zone de favoris
 */
function handleDrop(e) {
    e.preventDefault();
    const dropZone = e.target.closest('.favorites-drop-zone');
    dropZone.classList.remove('drag-over');
    
    const projectSlug = e.dataTransfer.getData('project-slug');
    if (projectSlug) {
        toggleFavorite(projectSlug);
    }
}

/**
 * Bascule le statut favori d'un projet
 */
async function toggleFavorite(projectSlug) {
    try {
        const data = await utils.fetchWithCsrf(`/projects/${projectSlug}/toggle_favorite`, {
            method: 'POST'
        });
        
        if (data.success) {
            utils.showToast('success', data.message);
            
            // Recharger la page pour mettre à jour l'affichage
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            utils.showToast('error', data.error || 'Erreur lors de la mise à jour des favoris');
        }
    } catch (error) {
        console.error('Erreur:', error);
        utils.showToast('error', 'Erreur lors de la mise à jour des favoris');
    }
}

export { initProjectFavorites };
