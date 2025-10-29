/**
 * Gestion de l'affichage de la description complète du projet
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
        element.addEventListener('click', function() {
            const fullDescription = this.getAttribute('data-full-description');
            if (fullDescription) {
                // Afficher la description complète avec formatage
                fullDescriptionText.innerHTML = formatDescription(fullDescription);
            }
        });
    });
    
    // Fonction pour formater la description (gérer les retours à la ligne)
    function formatDescription(text) {
        if (!text) return '';
        
        // Remplacer les retours à la ligne par des <br>
        return text
            .replace(/\n/g, '<br>')
            .replace(/\r\n/g, '<br>')
            .replace(/\r/g, '<br>');
    }
    
    // Ajouter un style pour indiquer que c'est cliquable
    descriptionElements.forEach(element => {
        element.style.textDecoration = 'underline';
        element.style.textDecorationStyle = 'dotted';
        element.title = 'Cliquer pour voir la description complète';
    });
});
