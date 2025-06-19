/**
 * @file formAutofocus.js
 * @description
 * Automatically focuses the first enabled and visible form field (input, textarea, select)
 * on all forms present in the document.
 */

/**
 * Sets focus to the first focusable field in each form on the page.
 */
export function autoFocusFirstField() {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    const first = form.querySelector(
      "input:not([type=hidden]):not([disabled]), textarea:not([disabled]), select:not([disabled])"
    );
    if (first) first.focus();
  });
}

// Run autofocus on DOMContentLoaded
document.addEventListener("DOMContentLoaded", autoFocusFirstField);
