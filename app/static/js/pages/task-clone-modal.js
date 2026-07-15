document.addEventListener("DOMContentLoaded", function () {
    const modalEl = document.getElementById("cloneTaskModal");
    const wrapper = document.getElementById("cloneChecklistWrapper");
    const emptyNote = document.getElementById("cloneChecklistEmptyNote");
    const checkbox = document.getElementById("cloneChecklist");
    const hidden = document.getElementById("cloneChecklistHidden");
    if (!modalEl || !wrapper || !emptyNote || !checkbox || !hidden) {
        return;
    }

    const syncHiddenWithCheckbox = () => {
        hidden.value = checkbox.checked ? "1" : "0";
    };

    modalEl.addEventListener("show.bs.modal", function () {
        const hasChecklistItems = document.querySelectorAll("#checklist-items .checklist-item").length > 0;

        if (hasChecklistItems) {
            wrapper.classList.remove("d-none");
            emptyNote.classList.add("d-none");
            checkbox.checked = true;
            syncHiddenWithCheckbox();
        } else {
            wrapper.classList.add("d-none");
            emptyNote.classList.remove("d-none");
            hidden.value = "0";
        }
    });

    checkbox.addEventListener("change", syncHiddenWithCheckbox);
    syncHiddenWithCheckbox();
});
