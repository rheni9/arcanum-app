/**
 * @file filterForm.js
 * @description
 * Entry point for the Filter Form module.
 * Initializes form validation and date input visibility toggle
 * after the DOM content has fully loaded.
 */

import { bindFilterForm } from "./core/handlers.js";

/**
 * Initializes filter form validation and end date toggle logic
 * when the DOM content is fully loaded.
 *
 * Binds form validation, sets initial visibility of the end date input,
 * and attaches listener to update visibility on date mode change.
 *
 * @listens DOMContentLoaded
 */
document.addEventListener("DOMContentLoaded", () => {
  console.debug("[filterForm] DOMContentLoaded");
  
  bindFilterForm();
  toggleEndDateVisibility();

  const modeSelect = document.querySelector(".date-mode-select");
  if (modeSelect) {
    modeSelect.addEventListener("change", toggleEndDateVisibility);
  }
});

/**
 * Toggles visibility of the end date input based on the selected date mode.
 *
 * Shows the end date input only if the mode is 'between',
 * otherwise hides and clears its value.
 */
function toggleEndDateVisibility() {
  const mode = document.querySelector(".date-mode-select");
  const endInput = document.getElementById("end_date");
  if (!mode || !endInput) return;

  // toggle class 'hidden' instead of style
  if (mode.value === "between") {
    endInput.classList.remove("hidden");
  } else {
    endInput.classList.add("hidden");
    endInput.value = "";  // optionally clear the value if not used
  }
}

