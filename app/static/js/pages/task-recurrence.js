import { utils } from '../utils.js';

function todayIsoDate() {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

function setText(el, text) {
    if (!el) return;
    el.textContent = text || '';
}

function toggle(el, show) {
    if (!el) return;
    el.classList.toggle('d-none', !show);
}

function getSelectedWeekdays() {
    return Array.from(document.querySelectorAll('.recurrence-weekday'))
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.value, 10))
        .filter(v => !Number.isNaN(v));
}

function setSelectedWeekdays(days) {
    const set = new Set((days || []).map(d => parseInt(d, 10)));
    document.querySelectorAll('.recurrence-weekday').forEach(cb => {
        cb.checked = set.has(parseInt(cb.value, 10));
    });
}

function refreshSections() {
    const frequencyEl = document.getElementById('recurrence-frequency');
    const endTypeEl = document.getElementById('recurrence-end-type');
    const weekdaysSection = document.getElementById('recurrence-weekdays-section');
    const businessDaysSection = document.getElementById('recurrence-business-days-section');
    const endDateWrapper = document.getElementById('recurrence-end-date-wrapper');
    const countWrapper = document.getElementById('recurrence-count-wrapper');

    const frequency = frequencyEl ? frequencyEl.value : 'daily';
    const endType = endTypeEl ? endTypeEl.value : 'never';

    toggle(weekdaysSection, frequency === 'weekly');
    toggle(businessDaysSection, frequency === 'daily');

    toggle(endDateWrapper, endType === 'until');
    toggle(countWrapper, endType === 'count');
}

async function loadRecurrence(taskSlug) {
    const data = await utils.fetchWithCsrf(`/tasks/${taskSlug}/recurrence`, {
        method: 'GET'
    });

    if (!data.success) {
        utils.handleApiResponse(data);
        return;
    }

    const frequencyEl = document.getElementById('recurrence-frequency');
    const intervalEl = document.getElementById('recurrence-interval');
    const startDateEl = document.getElementById('recurrence-start-date');
    const endTypeEl = document.getElementById('recurrence-end-type');
    const endDateEl = document.getElementById('recurrence-end-date');
    const countEl = document.getElementById('recurrence-count');
    const businessDaysOnlyEl = document.getElementById('recurrence-business-days-only');

    if (data.has_recurrence && data.recurrence) {
        if (frequencyEl) frequencyEl.value = data.recurrence.frequency || 'daily';
        if (intervalEl) intervalEl.value = data.recurrence.interval || 1;
        if (startDateEl) startDateEl.value = data.recurrence.start_date || todayIsoDate();

        // End selection
        if (data.recurrence.end_date) {
            if (endTypeEl) endTypeEl.value = 'until';
            if (endDateEl) endDateEl.value = data.recurrence.end_date;
            if (countEl) countEl.value = '';
        } else if (data.recurrence.count) {
            if (endTypeEl) endTypeEl.value = 'count';
            if (countEl) countEl.value = data.recurrence.count;
            if (endDateEl) endDateEl.value = '';
        } else {
            if (endTypeEl) endTypeEl.value = 'never';
            if (endDateEl) endDateEl.value = '';
            if (countEl) countEl.value = '';
        }

        // Weekly days
        if (data.recurrence.byweekday) {
            const days = data.recurrence.byweekday.split(',').map(s => parseInt(s.trim(), 10));
            setSelectedWeekdays(days);
        } else {
            setSelectedWeekdays([]);
        }

        // Business days
        if (businessDaysOnlyEl) businessDaysOnlyEl.checked = !!data.recurrence.business_days_only;
    } else {
        // Defaults for new recurrence
        if (frequencyEl) frequencyEl.value = 'daily';
        if (intervalEl) intervalEl.value = 1;
        if (startDateEl) startDateEl.value = todayIsoDate();
        if (endTypeEl) endTypeEl.value = 'never';
        if (endDateEl) endDateEl.value = '';
        if (countEl) countEl.value = '';
        setSelectedWeekdays([]);
        if (businessDaysOnlyEl) businessDaysOnlyEl.checked = false;
    }

    refreshSections();
}

function updateRecurrenceSummaryUI(data) {
    const summaryEl = document.getElementById('recurrence-summary-text');
    const nextEl = document.getElementById('recurrence-next-text');
    const deleteBtn = document.getElementById('recurrence-delete-btn');

    setText(summaryEl, data.summary || 'Aucune');
    if (data.next_date) {
        setText(nextEl, `(Prochaine : ${data.next_date})`);
    } else {
        setText(nextEl, '');
    }

    if (deleteBtn) {
        deleteBtn.disabled = !data.has_recurrence;
    }
}

async function saveRecurrence(taskSlug) {
    const frequencyEl = document.getElementById('recurrence-frequency');
    const intervalEl = document.getElementById('recurrence-interval');
    const startDateEl = document.getElementById('recurrence-start-date');
    const endTypeEl = document.getElementById('recurrence-end-type');
    const endDateEl = document.getElementById('recurrence-end-date');
    const countEl = document.getElementById('recurrence-count');
    const businessDaysOnlyEl = document.getElementById('recurrence-business-days-only');

    const payload = {
        frequency: frequencyEl ? frequencyEl.value : 'daily',
        interval: intervalEl ? parseInt(intervalEl.value || '1', 10) : 1,
        start_date: startDateEl ? startDateEl.value : todayIsoDate(),
        end_type: endTypeEl ? endTypeEl.value : 'never',
        end_date: endDateEl ? endDateEl.value : null,
        count: countEl ? parseInt(countEl.value || '0', 10) : null,
        byweekday: getSelectedWeekdays(),
        business_days_only: businessDaysOnlyEl ? businessDaysOnlyEl.checked : false
    };

    const data = await utils.fetchWithCsrf(`/tasks/${taskSlug}/recurrence`, {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    if (!utils.handleApiResponse(data)) return null;
    return data;
}

async function deleteRecurrence(taskSlug) {
    const data = await utils.fetchWithCsrf(`/tasks/${taskSlug}/recurrence`, {
        method: 'DELETE'
    });

    if (!utils.handleApiResponse(data)) return null;
    return data;
}

document.addEventListener('DOMContentLoaded', () => {
    const editBtn = document.getElementById('recurrence-edit-btn');
    const deleteBtn = document.getElementById('recurrence-delete-btn');
    const saveBtn = document.getElementById('recurrence-save-btn');
    const modalEl = document.getElementById('recurrenceModal');
    const slugInput = document.getElementById('recurrence-task-slug');

    if (!modalEl || !slugInput) return;
    const taskSlug = slugInput.value;

    const modal = new bootstrap.Modal(modalEl);

    // Bind field change handlers
    const frequencyEl = document.getElementById('recurrence-frequency');
    const endTypeEl = document.getElementById('recurrence-end-type');
    if (frequencyEl) frequencyEl.addEventListener('change', refreshSections);
    if (endTypeEl) endTypeEl.addEventListener('change', refreshSections);

    if (editBtn) {
        editBtn.addEventListener('click', async () => {
            await loadRecurrence(taskSlug);
            modal.show();
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            saveBtn.disabled = true;
            const original = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            try {
                const data = await saveRecurrence(taskSlug);
                if (data) {
                    updateRecurrenceSummaryUI(data);
                    modal.hide();
                }
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerHTML = original;
            }
        });
    }

    if (deleteBtn) {
        deleteBtn.addEventListener('click', async () => {
            if (deleteBtn.disabled) return;
            const ok = window.confirm("Supprimer la récurrence ? Les occurrences futures seront supprimées.");
            if (!ok) return;

            deleteBtn.disabled = true;
            const original = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            try {
                const data = await deleteRecurrence(taskSlug);
                if (data) {
                    updateRecurrenceSummaryUI(data);
                }
            } finally {
                deleteBtn.innerHTML = original;
                // Le serveur renvoie has_recurrence=false, donc on laissera l'état final via updateRecurrenceSummaryUI
            }
        });
    }

    // Ensure date default
    const startDateEl = document.getElementById('recurrence-start-date');
    if (startDateEl && !startDateEl.value) startDateEl.value = todayIsoDate();

    refreshSections();
});
