(function() {
    // 1. Déterminer le thème immédiatement
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.documentElement.classList.add('dark-mode');
    }
    
    // 2. Marquer le thème comme chargé pour rendre le contenu visible
    function markThemeAsLoaded() {
        document.documentElement.classList.add('theme-loaded');
    }
    
    // Exécuter immédiatement si le DOM est déjà chargé
    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        markThemeAsLoaded();
    } else {
        // Sinon attendre que le DOM soit chargé
        document.addEventListener('DOMContentLoaded', markThemeAsLoaded);
    }
    
    // 3. En cas de problème, afficher le contenu après un délai
    setTimeout(markThemeAsLoaded, 300);
})();