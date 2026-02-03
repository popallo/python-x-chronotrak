/**
 * Script spécifique au tableau de bord
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Initialisation de Sortable pour les colonnes
document.addEventListener('DOMContentLoaded', () => {
    const columns = document.querySelectorAll('.dashboard-column');

    // Créer une instance de Sortable pour chaque colonne
    columns.forEach(column => {
        new Sortable(column, {
            group: 'dashboard-cards', // Permet le déplacement entre les colonnes
            animation: 150,
            ghostClass: 'card-ghost', // Classe CSS pour l'élément fantôme pendant le drag
            dragClass: 'card-drag', // Classe CSS pour l'élément en cours de déplacement
            handle: '.card-header', // Permet de déplacer la carte en attrapant l'en-tête
            onEnd: function(evt) {
                // Sauvegarder la nouvelle position dans le localStorage
                saveCardsOrder();
            }
        });
    });
});

// Fonction pour sauvegarder l'ordre des cartes
function saveCardsOrder() {
    const columns = document.querySelectorAll('.dashboard-column');
    const order = Array.from(columns).map(column => {
        return Array.from(column.children).map(card => card.id);
    });

    localStorage.setItem('dashboardCardsOrder', JSON.stringify(order));
}

// Fonction pour restaurer l'ordre des cartes
function restoreCardsOrder() {
    const savedOrder = localStorage.getItem('dashboardCardsOrder');
    if (!savedOrder) return;

    const order = JSON.parse(savedOrder);
    const columns = document.querySelectorAll('.dashboard-column');

    order.forEach((columnOrder, columnIndex) => {
        const column = columns[columnIndex];
        if (!column) return;

        columnOrder.forEach(cardId => {
            const card = document.getElementById(cardId);
            if (card) column.appendChild(card);
        });
    });
}

// Restaurer l'ordre au chargement de la page
document.addEventListener('DOMContentLoaded', restoreCardsOrder);
