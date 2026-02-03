/**
 * Script pour gérer l'interface des préférences de notification
 */

function initNotificationPreferences() {
    const enabledSwitch = document.getElementById('email_notifications_enabled');
    const optionsDiv = document.getElementById('notification-options');

    if (!enabledSwitch || !optionsDiv) return;

    function toggleOptions() {
        const optionsInputs = optionsDiv.querySelectorAll('input');
        if (enabledSwitch.checked) {
            optionsDiv.classList.remove('opacity-50');
            optionsInputs.forEach(input => {
                input.disabled = false;
            });
        } else {
            optionsDiv.classList.add('opacity-50');
            optionsInputs.forEach(input => {
                input.disabled = true;
            });
        }
    }

    // État initial
    toggleOptions();

    // Écouteur d'événement
    enabledSwitch.addEventListener('change', toggleOptions);
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initNotificationPreferences();
});

export { initNotificationPreferences };
