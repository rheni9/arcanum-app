/**
 * @file modalConfirm.js
 * @description
 * UI utility for displaying a reusable modal confirmation dialog.
 * Accepts dynamic title, message, and a callback on confirmation.
 */

/**
 * Show a modal confirmation dialog.
 *
 * @param {string} title - Title text shown in the modal header.
 * @param {string} message - Message content shown in the modal body.
 * @param {Function} onConfirm - Function to execute if user confirms.
 */
let currentHandler = null;

export function showModal(title, message, onConfirm) {
  const modal = document.getElementById("confirm-modal");
  const titleEl = document.getElementById("modal-title");
  const bodyEl = document.getElementById("modal-body");
  const confirmBtn = document.getElementById("modal-confirm");
  const cancelBtn = document.getElementById("modal-cancel");
  const overlay = modal.querySelector(".modal-overlay");

  if (!modal || !titleEl || !bodyEl || !confirmBtn || !cancelBtn) {
    console.warn("[Modal] Required elements not found in DOM.");
    return;
  }

  titleEl.textContent = title;
  bodyEl.textContent = message;
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");

  const handler = () => {
    cleanup();
    if (typeof onConfirm === "function") onConfirm();
  };

  const handleOverlayClick = () => {
    cleanup();
  };

  const cleanup = () => {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    confirmBtn.removeEventListener("click", handler);
    cancelBtn.removeEventListener("click", cleanup);
    overlay.removeEventListener("click", handleOverlayClick);
    currentHandler = null;
  };

  confirmBtn.addEventListener("click", handler);
  cancelBtn.addEventListener("click", cleanup);
  overlay.addEventListener("click", handleOverlayClick);

  currentHandler = handler;
}
