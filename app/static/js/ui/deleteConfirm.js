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
          message = `Are you sure you want to delete the chat “${label}”? This cannot be undone.`;
        } else if (count === 1) {
          message = `Are you sure you want to delete the chat “${label}” with 1 message? This cannot be undone.`;
        } else {
          message = `Are you sure you want to delete the chat “${label}” with ${count} messages? This cannot be undone.`;
        }
      } else if (type === "chat-avatar") {
        message = `Are you sure you want to delete the avatar for chat “${label}”? This cannot be undone.`;
      } else if (type === "message") {
        message = `Are you sure you want to delete the message “${label}”? This cannot be undone.`;
      } else if (type === "screenshot") {
        message = `Are you sure you want to delete the screenshot for message “${label}”? This cannot be undone.`;
      } else if (type === "media") {
        message = `Are you sure you want to delete the media file “${label}”? This cannot be undone.`;
      } else {
        message = `Are you sure you want to delete “${label}”? This cannot be undone.`;
      }
      showModal("Confirm Deletion", message, () => {
        if (form) form.submit();
      });
    });
  });
}
