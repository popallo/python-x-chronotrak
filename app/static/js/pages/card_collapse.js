/**
 * Module de gestion du collapse des cartes du dashboard
 */

function initCardCollapse() {
    // Sélectionner toutes les cartes du dashboard qui ont un header et un body
    const dashboardCards = document.querySelectorAll('.card:has(.card-header):has(.card-body)');
    
    // Si aucune carte n'est trouvée, sortir
    if (!dashboardCards.length) return;
    
    // Pour chaque carte, ajouter le bouton de collapse s'il n'existe pas déjà
    dashboardCards.forEach(card => {
        const cardHeader = card.querySelector('.card-header');
        const cardBody = card.querySelector('.card-body');
        const cardId = card.id || `card-${Math.random().toString(36).substring(2, 9)}`;
        
        // S'assurer que la carte a un ID
        if (!card.id) {
            card.id = cardId;
        }
        
        // Vérifier si le bouton existe déjà
        if (!cardHeader.querySelector('.card-collapse-btn')) {
            // Créer le bouton de collapse
            const collapseBtn = document.createElement('button');
            collapseBtn.className = 'card-collapse-btn';
            collapseBtn.innerHTML = '<i class="fas fa-minus"></i>';
            collapseBtn.setAttribute('data-card-id', cardId);
            collapseBtn.setAttribute('title', 'Réduire/Développer');
            
            // Ajouter le bouton au header de la carte
            cardHeader.appendChild(collapseBtn);
            
            // Ajouter l'écouteur d'événement
            collapseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                toggleCardCollapse(cardId);
            });
        }
        
        // Restaurer l'état de la carte depuis les cookies
        const isCollapsed = getCookie(`card_${cardId}_collapsed`) === 'true';
        if (isCollapsed) {
            // Ajouter la classe sans animation puis mettre à jour l'icône
            cardBody.style.transition = 'none'; // Désactiver la transition temporairement
            cardBody.classList.add('collapsed');
            cardBody.style.maxHeight = '70px'; // Définir la hauteur d'aperçu
            
            // Réactiver la transition après un court délai
            setTimeout(() => {
                cardBody.style.transition = '';
            }, 50);
            
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
    
    if (cardBody) {
        // Si la carte est déjà réduite
        const isCurrentlyCollapsed = cardBody.classList.contains('collapsed');
        
        // Basculer la classe collapsed
        if (isCurrentlyCollapsed) {
            // Développer la carte
            const actualHeight = cardBody.scrollHeight;
            cardBody.style.maxHeight = `${actualHeight}px`;
            
            setTimeout(() => {
                cardBody.classList.remove('collapsed');
                // Après l'animation, supprimer la hauteur fixe pour permettre un redimensionnement automatique
                setTimeout(() => {
                    cardBody.style.maxHeight = '';
                }, 300);
            }, 10);
            
            collapseBtn.classList.replace('fa-plus', 'fa-minus');
            setCookie(`card_${cardId}_collapsed`, 'false', 30);
        } else {
            // Réduire la carte
            // D'abord, définir la hauteur actuelle pour l'animation
            const actualHeight = cardBody.scrollHeight;
            cardBody.style.maxHeight = `${actualHeight}px`;
            
            // Déclencher le reflow pour que la transition fonctionne
            cardBody.offsetHeight; 
            
            // Puis réduire à la hauteur d'aperçu (70px définie dans le CSS)
            cardBody.classList.add('collapsed');
            cardBody.style.maxHeight = '70px';
            
            collapseBtn.classList.replace('fa-minus', 'fa-plus');
            setCookie(`card_${cardId}_collapsed`, 'true', 30);
        }
    }
}

// Fonction pour définir un cookie
function setCookie(name, value, days) {
    let expires = '';
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
    }
    document.cookie = name + '=' + (value || '') + expires + '; path=/';
}

// Fonction pour récupérer un cookie
function getCookie(name) {
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

// Fonction pour supprimer un cookie
function eraseCookie(name) {
    document.cookie = name + '=; Max-Age=-99999999; path=/;';
}

// Fonction pour réinitialiser toutes les préférences de cartes réduites
function resetAllCardPreferences() {
    // Récupérer tous les cookies
    const allCookies = document.cookie.split(';');
    
    // Filtrer les cookies liés aux cartes
    const cardCookies = allCookies.filter(cookie => {
        const trimmedCookie = cookie.trim();
        return trimmedCookie.startsWith('card_') && trimmedCookie.includes('_collapsed');
    });
    
    // Supprimer chaque cookie
    cardCookies.forEach(cookie => {
        const cookieName = cookie.split('=')[0].trim();
        eraseCookie(cookieName);
    });
    
    // Développer toutes les cartes actuellement affichées
    const collapsedCards = document.querySelectorAll('.card-body.collapsed');
    collapsedCards.forEach(cardBody => {
        // Trouver l'ID de la carte parente
        const card = cardBody.closest('.card');
        if (card && card.id) {
            // Développer la carte sans animation
            cardBody.style.transition = 'none';
            cardBody.classList.remove('collapsed');
            cardBody.style.maxHeight = '';
            
            // Mettre à jour l'icône
            const icon = card.querySelector('.card-collapse-btn i');
            if (icon) {
                icon.classList.replace('fa-plus', 'fa-minus');
            }
            
            // Réactiver les transitions après un court délai
            setTimeout(() => {
                cardBody.style.transition = '';
            }, 50);
        }
    });
}

// Exporter les fonctions
export { initCardCollapse, toggleCardCollapse, resetAllCardPreferences };