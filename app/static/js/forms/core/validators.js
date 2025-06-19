/**
 * @file validators.js
 * @description
 * Concrete validation functions for Arcanum forms.
 * Includes validation for text fields, URLs, dates, times, IDs,
 * search queries, and date filter ranges with inline messaging.
 */

import {
  isEmpty,
  highlightError,
  clearError
} from "../core/baseUtils.js";
import {
  insertInlineMessage,
  removeInlineMessage,
  removeGlobalMessage,
  insertBelowGroup,
  removeGroupMessage
} from "../core/formMessages.js";
import {
  isDateValid,
  isTimeValid,
  isPastOrNow,
} from "../core/dateUtils.js";
import {
  validateBetween,
  validateSingleDate,
  validateModeSelected,
} from "./filterValidation.js";

/* ============================================================================
   Text & ID Validation
============================================================================ */

/**
 * Validates a required text field (e.g. name).
 *
 * @param {HTMLInputElement} input - The field to check.
 * @param {boolean} required - Whether the field must not be empty.
 * @returns {boolean} True if valid.
 */
export function validateText(input, required = false) {
  clearError(input);
  removeInlineMessage(input);

  if (required && isEmpty(input.value)) {
    highlightError(input);
    insertInlineMessage(input, "This field is required.");
    return false;
  }
  return true;
}

/**
 * Validates that an ID field (e.g. chat_id, msg_id) contains only digits.
 *
 * @param {HTMLInputElement} input - The input element to validate.
 * @param {string} [label="ID"] - Optional label for error messages.
 * @returns {boolean} Whether the input is valid.
 */
export function validateIdField(input, label = "ID") {
  clearError(input);
  removeInlineMessage(input);

  const val = input.value.trim();
  if (val !== "" && !/^\d+$/.test(val)) {
    highlightError(input);
    insertInlineMessage(input, `${label} must be a positive integer.`);
    return false;
  }
  return true;
}

/* ============================================================================
   URL Validation
============================================================================ */

/**
 * Validates an optional URL field.
 *
 * @param {HTMLInputElement} input - The link input.
 * @returns {boolean} True if valid or empty.
 */
export function validateUrl(input) {
  clearError(input);
  removeInlineMessage(input);

  if (isEmpty(input.value)) return true;

  let url;
  try {
    url = new URL(input.value);
  } catch {
    highlightError(input);
    insertInlineMessage(input, "Enter a valid URL (must begin with http:// or https://).");
    return false;
  }

  if (!/^https?:\/\//.test(url.href)) {
    highlightError(input);
    insertInlineMessage(input, "URL must begin with http:// or https://");
    return false;
  }
  return true;
}

/* ============================================================================
   Date & Time Validation
============================================================================ */

/**
 * Validates a date field.
 *
 * @param {HTMLInputElement} input - The date input.
 * @returns {boolean} True if valid.
 */
export function validateDate(input) {
  clearError(input);
  removeInlineMessage(input);

  const value = input.value.trim();
  if (isEmpty(value)) return true;

  const result = isDateValid(value);

  if (!result.valid) {
    highlightError(input);
    if (result.reason === "format") {
      insertInlineMessage(input, "Invalid date format.");
    } else if (result.reason === "calendar") {
      insertInlineMessage(input, "Date does not exist.");
    } else {
      insertInlineMessage(input, "Invalid date.");
    }
    return false;
  }

  return true;
}

/**
 * Validates a time field.
 *
 * @param {HTMLInputElement} input - The time input.
 * @returns {boolean} True if valid.
 */
export function validateTime(input) {
  clearError(input);
  removeInlineMessage(input);

  if (!isTimeValid(input.value)) {
    highlightError(input);
    insertInlineMessage(input, "Enter a valid time (HH:MM or HH:MM:SS).");
    return false;
  }
  return true;
}

/**
 * Validates a required date input.
 *
 * @param {HTMLInputElement} input - The date input element.
 * @returns {boolean} True if valid.
 */
export function validateRequiredDate(input) {
  clearError(input);
  removeInlineMessage(input);

  const value = input.value.trim();
  if (isEmpty(value)) {
    highlightError(input);
    insertInlineMessage(input, "Date is required.");
    return false;
  }

  const result = isDateValid(value);
  if (!result.valid) {
    highlightError(input);
    if (result.reason === "format") {
      insertInlineMessage(input, "Invalid date format.");
    } else if (result.reason === "calendar") {
      insertInlineMessage(input, "Date does not exist.");
    } else {
      insertInlineMessage(input, "Invalid date.");
    }
    return false;
  }

  return true;
}

/**
 * Validates a required time input.
 *
 * @param {HTMLInputElement} input - The time input element.
 * @returns {boolean} True if valid.
 */
export function validateRequiredTime(input) {
  clearError(input);
  removeInlineMessage(input);

  if (isEmpty(input.value)) {
    highlightError(input);
    insertInlineMessage(input, "Time is required.");
    return false;
  }

  if (!isTimeValid(input.value)) {
    highlightError(input);
    insertInlineMessage(input, "Enter a valid time (HH:MM or HH:MM:SS).");
    return false;
  }

  return true;
}

/**
 * Validates that the combined date/time is not in the future.
 * Inserts a shared inline error below both fields if invalid.
 *
 * @param {HTMLInputElement} dateInput - The date input element.
 * @param {HTMLInputElement} timeInput - The time input element.
 * @param {HTMLFormElement} form - The form element.
 * @returns {boolean} True if date/time is past or now.
 * @throws {none} Validation errors are shown inline, no exceptions thrown.
 */
export function validatePastOrNow(dateInput, timeInput, form) {
  removeInlineMessage(dateInput);
  removeInlineMessage(timeInput);

  const result = isDateValid(dateInput.value);
  if (!result.valid) {
    removeGroupMessage("future-timestamp");
    return true;
  }

  const normalized = result.normalized;

  if (timeInput && !isEmpty(timeInput.value) && !isTimeValid(timeInput.value)) {
    removeGroupMessage("future-timestamp");
    return true;
  }

  if (!isPastOrNow(normalized, timeInput?.value || null)) {
    highlightError(dateInput);
    highlightError(timeInput);

    const group = form.querySelector(".form-datetime-row");
    insertBelowGroup(group, "Date/time cannot be in the future.", "future-timestamp");

    return false;
  }

  removeGroupMessage("future-timestamp");

  return true;
}

/**
 * Validates that a date input is not in the future (optional fields).
 *
 * @param {HTMLInputElement} input - The date input element.
 * @returns {boolean} True if valid or empty.
 */
export function validateNotFutureDate(input) {
  clearError(input);
  removeInlineMessage(input);

  const value = input.value.trim();
  if (isEmpty(value)) return true;

  const result = isDateValid(value);
  if (!result.valid) return true;

  const normalized = result.normalized;
  if (!isPastOrNow(normalized)) {
    highlightError(input);
    insertInlineMessage(input, "Date cannot be in the future.");
    return false;
  }

  return true;
}

/* ============================================================================
   Filter Range Validation
============================================================================ */

/**
 * Validates a search query strictly (required or #tag).
 *
 * @param {HTMLInputElement} input - The search input element.
 * @param {boolean} [strictEmpty=false] - Whether to treat empty input as invalid even when not focused.
 * @returns {boolean} True if valid.
 */
export function validateSearchQueryStrict(input, strictEmpty = false) {
  clearError(input);
  removeInlineMessage(input);

  const raw = input.value || "";
  const trimmed = raw.trim();

  if (!trimmed) {
    if (strictEmpty || document.activeElement === input) {
      highlightError(input);
      insertInlineMessage(input, "Please enter a search query.");
      return false;
    } else {
      return true;
    }
  }

  if (trimmed === "#") {
    highlightError(input);
    insertInlineMessage(input, "Please enter a tag after '#'.");
    return false;
  }

  if (trimmed.length > 30) {
    highlightError(input);
    insertInlineMessage(input, "Search query is too long.");
    return false;
  }

  return true;
}

/**
 * Validates the entire filter form with inline messages.
 *
 * @param {HTMLFormElement} form - The filter form element.
 * @param {string|null} action - The action string (expects 'filter').
 * @returns {boolean} True if form is valid.
 */
export function validateFilterFormStrict(form, action = null) {
  if (action !== "filter") return true;

  const modeSelect = form.querySelector('[name="date_mode"]');
  const startInput = form.querySelector('[name="start_date"]');
  const endInput = form.querySelector('[name="end_date"]');

  removeInlineMessage(modeSelect);
  removeInlineMessage(startInput);
  removeInlineMessage(endInput);
  removeGlobalMessage("date-range");

  if (!validateModeSelected(modeSelect, form)) {
    return false;
  }

  const mode = modeSelect.value;

  if (mode === "between") {
    return validateBetween(startInput, endInput, form);
  }

  return validateSingleDate(startInput);
}
