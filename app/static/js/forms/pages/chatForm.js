/**
 * @file chatForm.js
 * @description
 * Entry point for the Chat Form module.
 * Initializes form validation and toggle switch logic
 * after the DOM content has fully loaded.
 */

import { bindChatForm } from "../core/handlers.js";
import { initChatToggles } from "../core/toggles.js";

/**
 * Initializes chat form validation and toggle logic
 * when the DOM content is fully loaded.
 *
 * @listens DOMContentLoaded
 */
document.addEventListener("DOMContentLoaded", () => {
  console.debug("[chatForm] DOMContentLoaded");
  bindChatForm();
  initChatToggles();
});
