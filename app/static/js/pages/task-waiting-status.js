/**
 * Mise à jour AJAX du sous-statut d'attente (boutons sous le statut kanban).
 */

function showWaitingToast(type, message) {
    const toastContainer = document.getElementById("toast-container") || createWaitingToastContainer();
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
}

function createWaitingToastContainer() {
    const container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container position-fixed bottom-0 end-0 p-3";
    document.body.appendChild(container);
    return container;
}

function initWaitingTooltips(root) {
    root.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
        const existing = bootstrap.Tooltip.getInstance(el);
        if (existing) {
            existing.dispose();
        }
        new bootstrap.Tooltip(el, {
            customClass: "waiting-status-tooltip",
            trigger: "hover focus",
        });
    });
}

function setActiveWaitingButton(buttons, activeValue) {
    buttons.forEach((btn) => {
        const value = btn.dataset.waitingStatus ?? "";
        btn.classList.toggle("is-active", value === activeValue);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".waiting-status-toggle");
    if (!toggle) return;

    const buttons = toggle.querySelectorAll(".waiting-status-btn");
    if (!buttons.length) return;

    initWaitingTooltips(toggle);

    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.content : "";
    const taskId = toggle.dataset.taskId;

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const waitingStatus = button.dataset.waitingStatus ?? "";
            const previousActive = toggle.querySelector(".waiting-status-btn.is-active");
            const previousValue = previousActive ? (previousActive.dataset.waitingStatus ?? "") : "";

            if (waitingStatus === previousValue) {
                return;
            }

            buttons.forEach((btn) => {
                btn.disabled = true;
            });
            button.classList.add("is-processing");

            fetch("/tasks/update_waiting_status", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": csrfToken,
                },
                body: JSON.stringify({
                    task_id: Number(taskId),
                    waiting_status: waitingStatus,
                }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        setActiveWaitingButton(buttons, data.waiting_status || "");
                        showWaitingToast("success", "Sous-statut d'attente mis à jour");
                    } else {
                        setActiveWaitingButton(buttons, previousValue);
                        showWaitingToast("danger", data.error || "Une erreur est survenue");
                    }
                })
                .catch((error) => {
                    console.error("Erreur waiting_status:", error);
                    setActiveWaitingButton(buttons, previousValue);
                    showWaitingToast("danger", "Impossible de mettre à jour le sous-statut d'attente");
                })
                .finally(() => {
                    buttons.forEach((btn) => {
                        btn.disabled = false;
                    });
                    button.classList.remove("is-processing");
                });
        });
    });
});
