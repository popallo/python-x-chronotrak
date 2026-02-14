/**
 * Pièces jointes de la tâche : upload AJAX, suppression avec confirmation, mise à jour de la liste.
 */
import { CONFIG, utils } from "../utils.js";

function getTaskSlug() {
    const el = document.getElementById("task-attachments-container");
    return el ? el.getAttribute("data-task-slug") : null;
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} o`;
    return `${(bytes / 1024).toFixed(1)} Ko`;
}

function renderAttachmentItem(att, taskSlug) {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex align-items-center py-1 px-2 task-attachment-item";
    li.setAttribute("data-attachment-id", att.id);
    li.innerHTML = `
        <a href="/tasks/${encodeURIComponent(taskSlug)}/attachments/${encodeURIComponent(att.id)}" class="text-decoration-none flex-grow-1 text-truncate me-2" title="Télécharger ${att.name.replace(/"/g, "&quot;")}">
            <i class="fas fa-file-alt me-1 text-muted"></i>
            <span class="task-attachment-name">${att.name.replace(/</g, "&lt;")}</span>
            <small class="text-muted">(${formatSize(att.size)})</small>
        </a>
        <button type="button" class="btn btn-sm btn-outline-danger py-0 px-1 delete-attachment-btn" title="Supprimer" data-attachment-id="${att.id}">
            <i class="fas fa-times"></i>
        </button>
    `;
    return li;
}

function renderList(attachments, taskSlug) {
    const list = document.getElementById("task-attachments-list");
    const empty = document.getElementById("task-attachments-empty");
    const countBadge = document.getElementById("attachments-count");
    if (!list) return;

    list.querySelectorAll(".task-attachment-item").forEach((el) => el.remove());
    if (empty) empty.remove();

    if (attachments.length === 0) {
        const li = document.createElement("li");
        li.id = "task-attachments-empty";
        li.className = "list-group-item text-muted small py-1 px-2";
        li.textContent = "Aucune pièce jointe";
        list.appendChild(li);
    } else {
        attachments.forEach((att) => {
            list.appendChild(renderAttachmentItem(att, taskSlug));
        });
        bindDeleteButtons();
    }

    if (countBadge) countBadge.textContent = attachments.length;
}

async function refreshList() {
    const taskSlug = getTaskSlug();
    if (!taskSlug) return;
    try {
        const data = await utils.fetchWithCsrf(`/tasks/${taskSlug}/attachments`, { method: "GET" });
        if (data.success && Array.isArray(data.attachments)) {
            renderList(data.attachments, taskSlug);
        }
    } catch (e) {
        console.warn("Refresh attachments list failed", e);
    }
}

function bindDeleteButtons() {
    document.querySelectorAll(".delete-attachment-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const id = btn.getAttribute("data-attachment-id");
            const taskSlug = getTaskSlug();
            if (!id || !taskSlug || !window.confirm("Supprimer cette pièce jointe ?")) return;

            const data = await utils.fetchWithCsrf(`/tasks/${encodeURIComponent(taskSlug)}/attachments/${encodeURIComponent(id)}`, {
                method: "DELETE",
                headers: { "X-CSRF-Token": CONFIG.csrfToken }
            });
            if (data && data.success) {
                utils.showToast("success", "Pièce jointe supprimée.");
                await refreshList();
            } else {
                utils.showToast("danger", (data && data.error) || "Erreur lors de la suppression.");
            }
        });
    });
}

function initTaskAttachments() {
    const uploadForm = document.getElementById("task-attachments-upload-form");
    const input = document.getElementById("task-attachments-input");
    const zone = document.getElementById("pj-upload-zone");
    if (!uploadForm || !input) return;

    bindDeleteButtons();

    if (zone) {
        zone.addEventListener("click", (e) => { e.preventDefault(); input.click(); });
        zone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
    }

    input.addEventListener("change", () => {
        if (input.files && input.files.length > 0) uploadForm.requestSubmit();
    });

    if (zone) {
        zone.addEventListener("dragover", (e) => { e.preventDefault(); e.stopPropagation(); zone.classList.add("is-dragover"); });
        zone.addEventListener("dragleave", (e) => { e.preventDefault(); zone.classList.remove("is-dragover"); });
        zone.addEventListener("drop", (e) => {
            e.preventDefault();
            e.stopPropagation();
            zone.classList.remove("is-dragover");
            if (e.dataTransfer.files && e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                uploadForm.requestSubmit();
            }
        });
    }

    uploadForm.addEventListener("submit", async (e) => {
        if (!input.files || input.files.length === 0) {
            e.preventDefault();
            utils.showToast("warning", "Sélectionnez au moins un fichier.");
            return;
        }

        const taskSlug = getTaskSlug();
        if (!taskSlug) return;

        e.preventDefault();

        const formData = new FormData();
        formData.append("csrf_token", CONFIG.csrfToken);
        for (let i = 0; i < input.files.length; i++) {
            formData.append("files", input.files[i]);
        }

        const submitBtn = document.getElementById("task-attachments-submit");
        const zoneEl = document.getElementById("pj-upload-zone");
        if (submitBtn) submitBtn.disabled = true;
        if (zoneEl) zoneEl.classList.add("is-uploading");

        try {
            const response = await fetch(uploadForm.action, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                headers: {
                    "X-CSRF-Token": CONFIG.csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                }
            });
            const data = await response.json().catch(() => ({}));

            if (data.success) {
                if (data.uploaded && data.uploaded.length) {
                    utils.showToast("success", `${data.uploaded.length} fichier(s) ajouté(s).`);
                }
                if (data.errors && data.errors.length) {
                    data.errors.slice(0, 2).forEach((err) => utils.showToast("warning", err));
                }
                input.value = "";
                await refreshList();
            } else {
                utils.showToast("danger", data.error || (data.details && data.details[0]) || "Erreur lors de l’envoi.");
            }
        } catch (err) {
            utils.showToast("danger", "Erreur lors de l’envoi.");
        } finally {
            if (submitBtn) submitBtn.disabled = false;
            if (zoneEl) zoneEl.classList.remove("is-uploading");
        }
    });
}

document.addEventListener("DOMContentLoaded", initTaskAttachments);
