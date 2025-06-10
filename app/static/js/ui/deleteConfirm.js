/**
 * Delete confirmation logic for Arcanum.
 *
 * Attaches to [data-confirm] buttons and shows confirmation modal
 * with context-aware messages before submitting the form.
 */

import { showModal } from "./modalConfirm.js";

export function bindDeleteConfirmations() {
  const buttons = document.querySelectorAll("[data-confirm]");

  buttons.forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault();

      const form = button.closest("form");
      const type = button.dataset.type;
      const label = button.dataset.label || "item";
      const count = parseInt(button.dataset.msgcount || "0", 10);

      let msg = "";
      if (type === "chat") {
        if (count === 0) {
          msg = `Delete chat “${label}”? This cannot be undone.`;
        } else if (count === 1) {
          msg = `Delete chat “${label}” with 1 message? This cannot be undone.`;
        } else {
          msg = `Delete chat “${label}” with ${count} messages? This cannot be undone.`;
        }
      } else if (type === "message") {
        msg = `Delete message “${label}”? This cannot be undone.`;
      } else {
        msg = `Are you sure you want to delete “${label}”?`;
      }

      showModal("Confirm Deletion", msg, () => form.submit());
    });
  });
}
