document.addEventListener('DOMContentLoaded', function() {
    const nav = document.querySelector('.prismatic-nav');
    let lastScrollTop = 0;
    let scrollTimeout;
    let isScrolling = false;
    const SCROLL_THRESHOLD = 100;
    let isMenuVisible = false;

    // Créer l'indicateur de scroll
    const scrollIndicator = document.createElement('div');
    scrollIndicator.className = 'scroll-indicator';
    document.body.appendChild(scrollIndicator);

    // Fonction pour gérer le scroll
    function handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollPercentage = (scrollTop / (documentHeight - windowHeight)) * 100;
        
        // Mettre à jour l'indicateur de scroll
        scrollIndicator.style.width = `${scrollPercentage}%`;
        scrollIndicator.classList.add('visible');
        
        // Déterminer la direction du scroll
        const scrollingDown = scrollTop > lastScrollTop;
        
        // Gérer l'état du menu
        if (scrollTop > SCROLL_THRESHOLD) {
            nav.classList.add('scrolled');
            
            // Afficher le menu si on scrolle vers le haut
            if (!scrollingDown && !isMenuVisible) {
                showMenu();
            }
            // Cacher le menu si on scrolle vers le bas
            else if (scrollingDown && isMenuVisible) {
                hideMenu();
            }
        } else {
            nav.classList.remove('scrolled');
            showMenu();
        }

        // Mettre à jour la dernière position de scroll
        lastScrollTop = scrollTop;

        // Gérer l'indicateur de scroll
        if (!isScrolling) {
            isScrolling = true;
            clearTimeout(scrollTimeout);
            
            scrollTimeout = setTimeout(() => {
                isScrolling = false;
                setTimeout(() => {
                    scrollIndicator.classList.remove('visible');
                }, 1000);
            }, 150);
        }
    }

    // Fonction pour afficher le menu
    function showMenu() {
        isMenuVisible = true;
        nav.classList.add('visible');
        // Ajouter un délai avant de retirer la classe visible
        clearTimeout(nav.hideTimeout);
        nav.hideTimeout = setTimeout(() => {
            if (window.pageYOffset > SCROLL_THRESHOLD) {
                nav.classList.remove('visible');
                isMenuVisible = false;
            }
        }, 2000);
    }

    // Fonction pour cacher le menu
    function hideMenu() {
        isMenuVisible = false;
        nav.classList.remove('visible');
    }

    // Ajouter l'écouteur d'événement de scroll avec debounce
    let scrollTimeoutId;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeoutId);
        scrollTimeoutId = setTimeout(handleScroll, 10);
    }, { passive: true });

    // Gérer le hover sur le menu
    nav.addEventListener('mouseenter', function() {
        if (window.pageYOffset > SCROLL_THRESHOLD) {
            showMenu();
        }
    });

    // Gérer la sortie du hover
    nav.addEventListener('mouseleave', function() {
        if (window.pageYOffset > SCROLL_THRESHOLD) {
            hideMenu();
        }
    });

    // Empêcher le menu de se cacher pendant le clic
    nav.addEventListener('mousedown', function(e) {
        if (e.target.closest('.dropdown-menu')) {
            e.stopPropagation();
        }
    });

    // Initialiser l'état du menu
    handleScroll();
}); 