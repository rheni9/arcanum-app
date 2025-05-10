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
export function showConfirmModal(title, message, onConfirm) {
  const modal = document.getElementById("confirm-modal");
  const titleEl = document.getElementById("confirm-title");
  const messageEl = document.getElementById("confirm-message");
  const yesBtn = document.getElementById("confirm-yes");
  const noBtn = document.getElementById("confirm-no");

  titleEl.textContent = title;
  messageEl.textContent = message;
  modal.classList.remove("hidden");

  const cleanup = () => {
    modal.classList.add("hidden");
    yesBtn.removeEventListener("click", onYes);
    noBtn.removeEventListener("click", onNo);
  };

  const onYes = () => {
    cleanup();
    onConfirm();
  };
  
  const onNo = cleanup;

  yesBtn.addEventListener("click", onYes);
  noBtn.addEventListener("click", onNo);
}
  