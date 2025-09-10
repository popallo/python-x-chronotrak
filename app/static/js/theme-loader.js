(function() {
    // 1. Déterminer le thème immédiatement AVANT que le DOM soit rendu
    const darkMode = localStorage.getItem('darkMode');
    if (darkMode === 'enabled') {
        document.documentElement.classList.add('dark-mode');
    }
    
    // 2. Marquer le thème comme chargé pour rendre le contenu visible
    function markThemeAsLoaded() {
        document.documentElement.classList.add('theme-loaded');
    }
    
    // 3. Appliquer le thème immédiatement
    markThemeAsLoaded();
    
    // 4. En cas de problème, s'assurer que le contenu est visible
    setTimeout(markThemeAsLoaded, 100);
})();