/**
 * Script spécifique au tableau de bord
 */

document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggleCardsCollapse');
    if (!toggleButton) return;
    
    const cards = document.querySelectorAll('.card');
    
    // Fonction pour vérifier si une carte est développée
    function isCardExpanded(card) {
        const collapseElement = card.querySelector('.collapse');
        return collapseElement && collapseElement.classList.contains('show');
    }

    // Fonction pour mettre à jour le texte et l'icône du bouton
    function updateButtonState() {
        const allExpanded = Array.from(cards).every(isCardExpanded);
        toggleButton.innerHTML = allExpanded 
            ? '<i class="fas fa-compress-alt me-1"></i>Replier toutes les cartes'
            : '<i class="fas fa-expand-alt me-1"></i>Développer toutes les cartes';
    }

    // Fonction pour basculer l'état d'une carte
    function toggleCard(card, shouldExpand) {
        const collapseElement = card.querySelector('.collapse');
        if (!collapseElement) return;

        if (shouldExpand) {
            collapseElement.classList.add('show');
        } else {
            collapseElement.classList.remove('show');
        }
    }

    // Vérifier l'état initial des cartes
    updateButtonState();

    // Gérer le clic sur le bouton
    toggleButton.addEventListener('click', function() {
        const allExpanded = Array.from(cards).every(isCardExpanded);
        const shouldExpand = !allExpanded;
        
        cards.forEach(card => toggleCard(card, shouldExpand));
        updateButtonState();
    });
});