/**
 * @file confirmations.js
 * @description
 * Handles delete confirmation prompts using a custom modal dialog.
 * Targets elements with the `data-confirm` attribute and intercepts clicks.
 */

import { showConfirmModal } from "./modalConfirm.js";

/**
 * Bind custom delete confirmation to elements with `data-confirm` attribute.
 * Shows a modal dialog with dynamic message before submitting the form.
 */
export function bindDeleteConfirmations() {
  document.querySelectorAll("[data-confirm]").forEach((btn) => {
    const form = btn.closest("form");
    if (!form) return;

    btn.addEventListener("click", (e) => {
      e.preventDefault();

      const count = parseInt(btn.dataset.msgcount || "0", 10);
      const type = btn.dataset.type || "item";
      const rawLabel = btn.dataset.label || "";
      const withEmoji = btn.dataset.emoji !== "false";

      const icon = withEmoji ? "⚠️ " : "";
      const noun = type === "chat" ? "chat" : "message";
      const label = rawLabel.trim() || `this ${noun}`;

      const msg = count > 0
        ? `${icon}Deleting “${label}” will remove its ${count} message${count !== 1 ? "s" : ""}.`
        : `${icon}Are you sure you want to delete “${label}”?`;

      showConfirmModal("Confirm Deletion", msg, () => form.submit());
    });
  });
}
