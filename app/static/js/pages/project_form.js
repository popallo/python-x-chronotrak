export function initProjectForm() {
    const timeTrackingCheckbox = document.getElementById('time_tracking_enabled');
    const creditField = document.getElementById('creditField');
    const creditInput = document.getElementById('initial_credit');

    function toggleCreditField() {
        if (timeTrackingCheckbox.checked) {
            creditField.style.display = 'block';
            creditInput.setAttribute('required', 'required');
        } else {
            creditField.style.display = 'none';
            creditInput.removeAttribute('required');
            creditInput.value = '0';
        }
    }

    // Ajouter l'écouteur d'événement
    timeTrackingCheckbox.addEventListener('change', toggleCreditField);

    // Exécuter au chargement de la page
    toggleCreditField();
}
