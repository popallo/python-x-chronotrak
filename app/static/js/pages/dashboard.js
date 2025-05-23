/**
 * Script spécifique au tableau de bord
 */

document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggleCardsCollapse');
    if (!toggleButton) return;
    
    const cards = document.querySelectorAll('.card');
    const collapseElements = document.querySelectorAll('.collapse');
    
    // Initialiser les éléments collapse avec Bootstrap
    collapseElements.forEach(collapse => {
        new bootstrap.Collapse(collapse, {
            toggle: false
        });
    });

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

        const bsCollapse = bootstrap.Collapse.getInstance(collapseElement);
        if (bsCollapse) {
            if (shouldExpand) {
                bsCollapse.show();
            } else {
                bsCollapse.hide();
            }
        }
    }

    // Ajouter des styles CSS pour l'animation
    const style = document.createElement('style');
    style.textContent = `
        .collapse {
            transition: all 0.3s ease-in-out;
        }
        .collapse:not(.show) {
            display: none;
        }
        .card {
            transition: all 0.3s ease-in-out;
        }
        .card-body {
            transition: all 0.3s ease-in-out;
        }
    `;
    document.head.appendChild(style);

    // Vérifier l'état initial des cartes
    updateButtonState();

    // Gérer le clic sur le bouton
    toggleButton.addEventListener('click', function() {
        const allExpanded = Array.from(cards).every(isCardExpanded);
        const shouldExpand = !allExpanded;
        
        cards.forEach(card => toggleCard(card, shouldExpand));
        updateButtonState();
    });

    // Ajouter des gestionnaires d'événements pour les transitions
    collapseElements.forEach(collapse => {
        collapse.addEventListener('show.bs.collapse', function() {
            this.closest('.card').classList.add('expanding');
        });
        
        collapse.addEventListener('shown.bs.collapse', function() {
            this.closest('.card').classList.remove('expanding');
        });
        
        collapse.addEventListener('hide.bs.collapse', function() {
            this.closest('.card').classList.add('collapsing');
        });
        
        collapse.addEventListener('hidden.bs.collapse', function() {
            this.closest('.card').classList.remove('collapsing');
        });
    });
});