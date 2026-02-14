/**
 * Affichage de la description complète de la tâche dans une modale
 */

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('taskDescriptionModal');
    const contentEl = document.getElementById('taskFullDescriptionText');

    if (!modal || !contentEl) {
        return;
    }

    document.querySelectorAll('.task-info-description-more').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
        });
    });

    modal.addEventListener('show.bs.modal', function(event) {
        const trigger = event.relatedTarget;
        if (!trigger) return;

        const raw = trigger.getAttribute('data-full-description');
        if (raw) {
            contentEl.innerHTML = formatDescription(raw);
        }
    });

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDescription(text) {
        if (!text) return '';
        return escapeHtml(text)
            .replace(/\n/g, '<br>')
            .replace(/\r\n/g, '<br>')
            .replace(/\r/g, '<br>');
    }
});
