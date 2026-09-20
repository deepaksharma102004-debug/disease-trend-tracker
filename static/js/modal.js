function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add("show");
    document.body.style.overflow = "hidden";
    modal.dispatchEvent(new Event("show.bs.modal"));

    let backdrop = document.getElementById(id + "_backdrop");
    if (!backdrop) {
        backdrop = document.createElement("div");
        backdrop.className = "modal-backdrop";
        backdrop.id = id + "_backdrop";
        backdrop.onclick = () => closeModal(id);
        document.body.appendChild(backdrop);
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove("show");
    document.body.style.overflow = "";
    const backdrop = document.getElementById(id + "_backdrop");
    if (backdrop) backdrop.remove();
}

// Auto-wire any button with data-bs-toggle="modal" / data-bs-dismiss="modal"
document.addEventListener("click", (e) => {
    const opener = e.target.closest("[data-bs-toggle='modal']");
    if (opener) {
        const targetId = opener.getAttribute("data-bs-target")?.replace("#", "");
        if (targetId) openModal(targetId);
    }
    const closer = e.target.closest("[data-bs-dismiss='modal']");
    if (closer) {
        const modal = closer.closest(".modal");
        if (modal) closeModal(modal.id);
    }
});