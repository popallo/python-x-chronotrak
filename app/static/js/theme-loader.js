(function() {
    // 1. Déterminer le thème immédiatement AVANT que le DOM soit rendu
    const darkMode = localStorage.getItem('darkMode');
    const html = document.documentElement;
    
    // 2. Appliquer le thème immédiatement pour éviter le flash
    if (darkMode === 'enabled') {
        html.classList.add('dark-mode');
        html.setAttribute('data-bs-theme', 'dark');
    } else {
        html.setAttribute('data-bs-theme', 'light');
    }
    
    // 3. Marquer le thème comme chargé pour rendre le contenu visible
    html.classList.add('theme-loaded');
    
    // 4. Fallback de sécurité - s'assurer que le contenu est visible
    setTimeout(function() {
        html.classList.add('theme-loaded');
    }, 50);
})();