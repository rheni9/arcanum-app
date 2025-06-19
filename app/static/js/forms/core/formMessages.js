import { isEmpty } from "./baseUtils.js";

/* ============================================================================
   Inline Error Messages
============================================================================ */

/**
 * Inserts an inline error message after a given input element.
 *
 * If a message already exists within the target wrapper, it will be replaced.
 *
 * @param {HTMLElement} input - The input element to attach the message to.
 * @param {string} msg - The error message to display.
 * @param {HTMLElement} [refEl=null] - Optional reference element to insert after.
 */
export function insertInlineMessage(input, msg, refEl = null) {
  if (!input || !msg) return;

  let target = null;

  if (refEl instanceof HTMLElement) {
    target = refEl;
  } else {
    const group = input.closest(".form-group");
    if (group) {
      target = group.querySelector(".form-message-wrapper");
    }
    if (!target) {
      target = input.parentElement;
    }
  }

  if (target.classList.contains("form-message-wrapper")) {
    target.querySelectorAll(".form-inline-message").forEach(el => el.remove());
  }

  const message = document.createElement("div");
  message.className = "form-inline-message error";
  message.textContent = msg;

  target.insertAdjacentElement("beforeend", message);
  input.dataset.hasInlineError = "true";
}

/**
 * Removes an existing inline message for the input element.
 *
 * @param {HTMLElement} input - The input element whose message should be removed.
 * @param {HTMLElement} [refEl=null] - Optional reference element or container.
 */
export function removeInlineMessage(input, refEl = null) {
  if (!input) return;

  const target =
    refEl instanceof HTMLElement
      ? refEl
      : input.closest(".form-group")?.querySelector(".form-message-wrapper");

  if (target) {
    target.querySelectorAll(".form-inline-message").forEach(el => el.remove());
  } else {
    const next = input.nextElementSibling;
    if (next && next.classList.contains("form-inline-message")) {
      next.remove();
    }
  }

  delete input.dataset.hasInlineError;
}

/* ============================================================================
   Global Form Messages
============================================================================ */

/**
 * Inserts a global message block into the form.
 *
 * If a message with the same ID exists, it will be updated.
 *
 * @param {HTMLFormElement} form - The form to insert the message into.
 * @param {string} msg - The message content.
 * @param {string} id - The unique ID for the message block.
 */
export function insertGlobalMessage(form, msg, id) {
  if (!form || !msg || isEmpty(id)) return;

  removeGlobalMessage(id);

  const wrapper = document.createElement("div");
  wrapper.className = "form-global-message error";
  wrapper.id = id;
  wrapper.textContent = msg;

  form.prepend(wrapper);
}

/**
 * Removes a global message by its ID.
 *
 * @param {string} id - The ID of the global message to remove.
 */
export function removeGlobalMessage(id) {
  if (isEmpty(id)) return;

  const existing = document.getElementById(id);
  if (existing) existing.remove();
}

/* ============================================================================ 
   Group-Level Messages 
============================================================================ */

/**
 * Inserts a message below a container element, e.g., a row with multiple fields.
 *
 * @param {HTMLElement} container - The DOM element below which to insert the message.
 * @param {string} message - The message to insert.
 * @param {string|null} [id=null] - Unique message ID to prevent duplicates.
 */
export function insertBelowGroup(container, message, id = null) {
  removeGroupMessage(id);

  const msg = document.createElement("div");
  msg.className = "form-global-message error";
  msg.textContent = message;
  if (id) msg.dataset.messageId = id;

  const wrapper = container.querySelector(".form-message-wrapper");
  if (wrapper) {
    wrapper.innerHTML = "";
    wrapper.append(msg);
  } else {
    container.after(msg);
  }
}

/**
 * Removes a group-level message by its data-message-id.
 *
 * @param {string} id - The message ID to remove.
 */
export function removeGroupMessage(id) {
  if (isEmpty(id)) return;

  const existing = document.querySelector(`[data-message-id="${id}"]`);
  if (existing) existing.remove();
}
