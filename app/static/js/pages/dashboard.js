/**
 * Script spécifique au tableau de bord
 */

import { resetAllCardPreferences } from './card_collapse.js';

function initDashboard() {
    // Initialiser le bouton de réinitialisation des cartes réduites
    const resetButton = document.getElementById('resetCardCollapse');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            resetAllCardPreferences();
        });
    }
    
    // Autres initialisations spécifiques au tableau de bord peuvent être ajoutées ici
}

// Exporter la fonction d'initialisation
export { initDashboard };