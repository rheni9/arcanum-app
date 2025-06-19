/**
 * @file messageForm.js
 * @description
 * Entry point for the Message Form module.
 * Initializes form validation logic
 * after the DOM content has fully loaded.
 */

import { bindMessageForm } from "./core/handlers.js";

/**
 * Initializes message form validation when the DOM content is fully loaded.
 *
 * @listens DOMContentLoaded
 */
document.addEventListener("DOMContentLoaded", () => {
  console.debug("[messageForm] DOMContentLoaded");
  bindMessageForm();
});

