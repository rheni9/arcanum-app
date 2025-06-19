/**
 * @file filterValidation.js
 * @description
 * Validation utilities for date filters in Arcanum forms.
 * Includes strict date validation, inline error display,
 * and specific validations for 'between' and single-date modes.
 */

import { highlightError, clearHighlight } from "./baseUtils.js";
import {
  removeInlineMessage,
  insertInlineMessage,
  insertBelowGroup,
} from "./formMessages.js";
import { isDateValid, compareDates } from "./dateUtils.js";

/**
 * Strictly validates a single date string.
 *
 * @param {string} dateStr - Date string to validate.
 * @returns {boolean} True if the date string is valid; false if empty or invalid.
 */
export function isDateValidStrict(dateStr) {
  if (!dateStr) return false;
  const res = isDateValid(dateStr);
  return !!res && res.valid === true;
}

/**
 * Shows an inline error message for a given input element.
 *
 * @param {HTMLElement} input - The input element to show error for.
 * @param {string} message - The error message to display.
 */
export function showInlineError(input, message) {
  if (!input) return;  // safeguard against invalid input
  const wrapper = input.closest(".form-group")?.querySelector(".form-message-wrapper");
  if (wrapper) {
    removeInlineMessage(input, wrapper);
    insertInlineMessage(input, message, wrapper);
    highlightError(input);
  }
}

/**
 * Validates the 'between' date mode with start and end inputs.
 *
 * @param {HTMLInputElement} start - Start date input element.
 * @param {HTMLInputElement} end - End date input element.
 * @param {HTMLElement} form - The form element containing inputs.
 * @returns {boolean} True if validation passes.
 */
export function validateBetween(start, end, form) {
  const startVal = start.value.trim();
  const endVal = end.value.trim();
  const endVisible = end.offsetParent !== null;

  const startValid = isDateValidStrict(startVal);
  const endValid = endVisible ? isDateValidStrict(endVal) : true;

  if (!startValid && !endValid) {
    showInlineError(start, "Please provide valid start and end dates.");
    showInlineError(end, "Please provide valid start and end dates.");
    return false;
  }

  if (!startValid && endValid) {
    showInlineError(start, "Please provide a valid start date.");
    return false;
  }

  if (startValid && endVisible && !endValid) {
    showInlineError(end, "Please provide a valid end date.");
    return false;
  }

  if (startValid) {
    removeInlineMessage(start);
    clearHighlight(start);
  }
  if (endValid) {
    removeInlineMessage(end);
    clearHighlight(end);
  }

  if (startValid && endValid && !compareDates(startVal, endVal)) {
    highlightError(start);
    highlightError(end);
    const group = form.querySelector(".date-fields-group");
    insertBelowGroup(group, "Start date must be before or equal to end date.", "date-range");
    return false;
  }

  return true;
}

/**
 * Validates single-date modes ('on', 'before', 'after').
 *
 * @param {HTMLInputElement} start - Date input element.
 * @returns {boolean} True if valid.
 */
export function validateSingleDate(start) {
  const startVal = start.value.trim();

  if (!isDateValidStrict(startVal)) {
    showInlineError(start, "Please provide a valid date.");
    return false;
  } else {
    removeInlineMessage(start);
    clearHighlight(start);
  }

  return true;
}

/**
 * Validates that a date filter mode is selected.
 *
 * @param {HTMLSelectElement} modeSelect - The select element for date mode.
 * @param {HTMLElement} form - The form element.
 * @returns {boolean} True if a mode is selected.
 */
export function validateModeSelected(modeSelect, form) {
  const modeValue = modeSelect.value;
  if (!modeValue) {
    const group = form.querySelector(".date-fields-group");
    const wrapper = group?.querySelector(".form-message-wrapper");
    if (wrapper) {
      wrapper.innerHTML = "";
      const msg = document.createElement("div");
      msg.className = "form-inline-message error";
      msg.textContent = "Please select a date filter mode.";
      wrapper.appendChild(msg);
    }
    return false;
  }
  return true;
}
