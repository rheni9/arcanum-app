/**
 * @file baseUtils.js
 * @description
 * Basic utility functions for blank string checks and input field highlighting
 * used across Arcanum form validation modules.
 */

/**
 * Checks whether a string is empty or consists only of whitespace.
 *
 * @param {string} value - The input string to check.
 * @returns {boolean} True if the input is blank or whitespace-only.
 */
export function isEmpty(value) {
  return value.trim().length === 0;
}

/**
 * Adds error highlighting to an input field by adding
 * the 'input-error' CSS class.
 *
 * @param {HTMLElement} input - The input element to highlight.
 */
export function highlightError(input) {
  input.classList.add("input-error");
}

/**
 * Removes error highlighting from an input field by removing
 * the 'input-error' CSS class.
 *
 * @param {HTMLElement} input - The input element to clear highlighting from.
 */
export function clearHighlight(input) {
  if (!input) return;
  input.classList.remove("input-error");
}

/**
 * Removes error highlighting from an input field by removing
 * the 'input-error' CSS class.
 *
 * @param {HTMLElement} input - The input element to clear.
 */
export function clearError(input) {
  input.classList.remove("input-error");
}

/**
 * Trims whitespace from both ends of a string.
 * Utility wrapper for String.prototype.trim().
 *
 * @param {string} str - The input string.
 * @returns {string} The trimmed string.
 */
export function trim(str) {
  return str.trim();
}
