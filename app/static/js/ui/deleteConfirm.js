/**
 * @file deleteConfirm.js
 * @description
 * Binds confirmation logic to delete actions using a shared modal.
 * Handles contextual messaging for chats, messages, and generic items.
 */

import { showModal } from "./modalConfirm.js";

/**
 * Binds confirmation dialogs to buttons with the `[data-confirm]` attribute.
 * On click, shows a modal with a context-aware message.
 * Executes form submission only after confirmation.
 */
export function bindDeleteConfirmations() {
  const buttons = document.querySelectorAll("[data-confirm]");

  buttons.forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();

      const form = button.closest("form");
      const type = button.dataset.type;
      const label = button.dataset.label || "item";
      const count = parseInt(button.dataset.msgcount || "0", 10);

      let message = "";

      if (type === "chat") {
        if (count === 0) {
          message = `Delete chat “${label}”? This cannot be undone.`;
        } else if (count === 1) {
          message = `Delete chat “${label}” with 1 message? This cannot be undone.`;
        } else {
          message = `Delete chat “${label}” with ${count} messages? This cannot be undone.`;
        }
      } else if (type === "message") {
        message = `Delete message “${label}”? This cannot be undone.`;
      } else {
        message = `Are you sure you want to delete “${label}”?`;
      }

      showModal("Confirm Deletion", message, () => {
        if (form) form.submit();
      });
    });
  });
}
