/**
 * @file modalConfirm.js
 * @description
 * Displays a reusable modal confirmation dialog.
 * Accepts dynamic title, message, and an onConfirm callback function.
 * Manages lifecycle and event listeners for confirmation modals.
 */

let currentHandler = null;
let lastFocusedElement = null;

/**
 * Shows a confirmation modal with the given content and callback.
 * Initializes event listeners for confirm, cancel, and overlay click.
 *
 * @param {string} title - The modal header text.
 * @param {string} message - The message body content.
 * @param {Function} onConfirm - Callback to execute on confirmation.
 */
export function showModal(title, message, onConfirm) {
  const modal = document.getElementById("confirm-modal");
  const titleEl = document.getElementById("modal-title");
  const bodyEl = document.getElementById("modal-body");
  const confirmBtn = document.getElementById("modal-confirm");
  const cancelBtn = document.getElementById("modal-cancel");
  const overlay = modal.querySelector(".modal-overlay");

  if (!modal || !titleEl || !bodyEl || !confirmBtn || !cancelBtn || !overlay) {
    console.warn("[MODAL] Required modal elements not found in DOM.");
    return;
  }

  lastFocusedElement = document.activeElement;

  titleEl.textContent = title;
  bodyEl.textContent = message;
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");

  const cleanup = () => {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    confirmBtn.removeEventListener("click", handler);
    cancelBtn.removeEventListener("click", cleanup);
    overlay.removeEventListener("click", cleanup);
    currentHandler = null;

    if (document.activeElement && modal.contains(document.activeElement)) {
      document.activeElement.blur();
    }

    if (lastFocusedElement) {
      lastFocusedElement.focus();
    }
  };

  const handler = () => {
    cleanup();
    if (typeof onConfirm === "function") {
      onConfirm();
    }
  };

  confirmBtn.addEventListener("click", handler);
  cancelBtn.addEventListener("click", cleanup);
  overlay.addEventListener("click", cleanup);

  currentHandler = handler;
}
