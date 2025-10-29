/**
 * Gestion intelligente de l'affichage de la description complète du projet
 */

document.addEventListener('DOMContentLoaded', function() {
    const descriptionModal = document.getElementById('descriptionModal');
    const fullDescriptionText = document.getElementById('fullDescriptionText');
    const descriptionElements = document.querySelectorAll('.description-text');
    
    if (!descriptionModal || !fullDescriptionText || !descriptionElements.length) {
        return;
    }
    
    // Gérer l'ouverture du modal
    descriptionElements.forEach(element => {
        const fullDescription = element.getAttribute('data-full-description');
        const displayedText = element.textContent.trim();
        
        // Vérifier si la description est déjà complète
        const isDescriptionComplete = isDescriptionFullyDisplayed(fullDescription, displayedText);
        
        if (!isDescriptionComplete) {
            // Description tronquée - activer le clic
            element.addEventListener('click', function() {
                if (fullDescription) {
                    // Afficher la description complète avec formatage
                    fullDescriptionText.innerHTML = formatDescription(fullDescription);
                }
            });
            
            // Ajouter les styles et attributs pour indiquer que c'est cliquable
            element.style.textDecoration = 'underline';
            element.style.textDecorationStyle = 'dotted';
            element.style.cursor = 'pointer';
            element.title = 'Cliquer pour voir la description complète';
            element.setAttribute('data-bs-toggle', 'modal');
            element.setAttribute('data-bs-target', '#descriptionModal');
        } else {
            // Description complète - pas de clic nécessaire
            element.style.cursor = 'default';
            element.title = 'Description complète';
            element.removeAttribute('data-bs-toggle');
            element.removeAttribute('data-bs-target');
        }
    });
    
    // Fonction pour vérifier si la description est déjà complète
    function isDescriptionFullyDisplayed(fullDescription, displayedText) {
        if (!fullDescription || !displayedText) return false;
        
        // Nettoyer les deux textes pour la comparaison
        const cleanFull = fullDescription.trim();
        const cleanDisplayed = displayedText.replace(/\.\.\.$/, '').trim();
        
        // Vérifier si le texte affiché correspond au texte complet
        return cleanFull === cleanDisplayed || cleanFull.length <= 100;
    }
    
    // Fonction pour formater la description (gérer les retours à la ligne)
    function formatDescription(text) {
        if (!text) return '';
        
        // Remplacer les retours à la ligne par des <br>
        return text
            .replace(/\n/g, '<br>')
            .replace(/\r\n/g, '<br>')
            .replace(/\r/g, '<br>');
    }
});
