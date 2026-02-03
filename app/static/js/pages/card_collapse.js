/**
 * Module de gestion du collapse des cartes du dashboard
 */

function initCardCollapse() {
    // Sélectionner toutes les cartes sauf celles du dashboard
    const cards = document.querySelectorAll('.card:has(.card-header):has(.card-body):not(.no-collapse):not(.dashboard-card)');

    cards.forEach(card => {
        const cardId = card.id || `card-${Math.random().toString(36).substr(2, 9)}`;
        card.id = cardId;

        const cardHeader = card.querySelector('.card-header');
        const cardBody = card.querySelector('.card-body');

        // Pour chaque carte, ajouter le bouton de collapse s'il n'existe pas déjà
        if (!cardHeader.querySelector('.card-collapse-btn')) {
            // Créer le bouton de collapse
            const collapseBtn = document.createElement('button');
            collapseBtn.className = 'card-collapse-btn';
            collapseBtn.innerHTML = '<i class="fas fa-minus"></i>';
            collapseBtn.setAttribute('data-card-id', cardId);
            collapseBtn.setAttribute('title', 'Réduire/Développer');

            // Ajouter le bouton à l'en-tête de la carte
            cardHeader.appendChild(collapseBtn);

            // Ajouter l'événement de clic
            collapseBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleCardCollapse(cardId);
            });
        }

        // Vérifier l'état initial de la carte
        const isCollapsed = getCookie(`card_${cardId}_collapsed`) === 'true';
        if (isCollapsed) {
            // Appliquer l'état collapsed
            cardBody.classList.add('collapsed');

            // Mettre à jour l'icône
            const icon = cardHeader.querySelector('.card-collapse-btn i');
            if (icon) {
                icon.classList.replace('fa-minus', 'fa-plus');
            }
        }
    });
}

// Fonction pour basculer l'état de collapse d'une carte
function toggleCardCollapse(cardId) {
    const card = document.getElementById(cardId);
    if (!card) return;

    const cardBody = card.querySelector('.card-body');
    const collapseBtn = card.querySelector('.card-collapse-btn i');

    const isCurrentlyCollapsed = cardBody.classList.contains('collapsed');

    // Basculer la classe collapsed
    if (isCurrentlyCollapsed) {
        // Développer la carte
        cardBody.classList.remove('collapsed');

        // Mettre à jour l'icône
        if (collapseBtn) {
            collapseBtn.classList.replace('fa-plus', 'fa-minus');
        }

        // Sauvegarder la préférence
        setCookie(`card_${cardId}_collapsed`, 'false', 30);
    } else {
        // Réduire la carte
        cardBody.classList.add('collapsed');

        // Mettre à jour l'icône
        if (collapseBtn) {
            collapseBtn.classList.replace('fa-minus', 'fa-plus');
        }

        // Sauvegarder la préférence
        setCookie(`card_${cardId}_collapsed`, 'true', 30);
    }
}

// Fonction utilitaire pour définir un cookie
function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;
    document.cookie = `${name}=${value};${expires};path=/`;
}

// Fonction utilitaire pour récupérer un cookie
function getCookie(name) {
    const nameEQ = `${name}=`;
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

// Fonction pour réinitialiser toutes les préférences de collapse
function resetAllCardPreferences() {
    // Supprimer tous les cookies liés au collapse des cartes
    const cookies = document.cookie.split(';');
    cookies.forEach(cookie => {
        const trimmedCookie = cookie.trim();
        if (trimmedCookie.startsWith('card_') && trimmedCookie.includes('_collapsed')) {
            const cookieName = trimmedCookie.split('=')[0].trim();
            document.cookie = `${cookieName}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
        }
    });

    // Réinitialiser l'état visuel de toutes les cartes
    const collapsedCards = document.querySelectorAll('.card-body.collapsed');
    collapsedCards.forEach(cardBody => {
        const card = cardBody.closest('.card');
        if (card) {
            cardBody.classList.remove('collapsed');

            // Mettre à jour l'icône
            const icon = card.querySelector('.card-collapse-btn i');
            if (icon) {
                icon.classList.replace('fa-plus', 'fa-minus');
            }
        }
    });
}

export { initCardCollapse, toggleCardCollapse, resetAllCardPreferences };
