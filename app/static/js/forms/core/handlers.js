/**
 * @file handlers.js
 * @description
 * Event handlers for input blur/submit validation for all Arcanum forms.
 */

import { isEmpty } from "../core/baseUtils.js";
import {
  validateText,
  validateUrl,
  validateDate,
  validateIdField,
  validatePastOrNow,
  validateNotFutureDate,
  validateRequiredDate,
  validateRequiredTime,
  validateSearchQueryStrict,
  validateFilterFormStrict
} from "./validators.js";
import {
  validateModeSelected,
  validateSingleDate,
  validateBetween
} from "./filterValidation.js";

/* ============================================================================
   Input Validation Binding
============================================================================ */

/**
 * Attaches blur and input event handlers for validation on specified inputs.
 *
 * @param {HTMLFormElement} form - The form element.
 * @param {Object<string, Function>} validators - Map of input names to validator functions.
 */
export function bindInputValidation(form, validators) {
  for (const [name, validator] of Object.entries(validators)) {
    const input = form.querySelector(`[name="${name}"]`);
    if (!input) continue;

    const handler = () => validator(input);
    input.addEventListener("blur", handler);
    input.addEventListener("input", handler);
  }
}

/* ============================================================================
   Submit Validation Binding
============================================================================ */

/**
 * Bind submit event to form that runs validation before submission.
 *
 * Prevents submission if validation fails.
 *
 * @param {HTMLFormElement} form - The form element.
 * @param {Function} validateAll - Callback function that runs all validations.
 */
export function bindSubmitValidation(form, validateAll) {
  form.addEventListener("submit", (e) => {
    if (!validateAll()) {
      e.preventDefault();
      e.stopPropagation();
    }
  });
}

/* ============================================================================
   Form-Specific Validators
============================================================================ */

/**
 * Binds validation for the Chat Form.
 */
export function bindChatForm() {
  const form = document.querySelector(".chat-form");
  if (!form) return;

  const validators = {
    name: (i) => validateText(i, true),
    type: () => true,
    link: validateUrl,
    chat_id: validateIdField,
    joined: (i) => {
      if (isEmpty(i.value)) return true;
      return validateDate(i) && validateNotFutureDate(i);
    }
  };

  bindInputValidation(form, validators);

  bindSubmitValidation(form, () => {
    const ok =
      validators.name(form.name) &&
      validators.link(form.link) &&
      validators.chat_id(form.chat_id) &&
      validators.joined(form.joined);
    return ok;
  });
}

/**
 * Binds validation for the Message Form.
 */
export function bindMessageForm() {
  const form = document.querySelector(".message-form");
  if (!form) return;

  const validators = {
    msg_id: (i) => validateIdField(i, "Message ID"),
    date: (i) => {
      return validateRequiredDate(i) &&
             validatePastOrNow(i, form.time, form);
    },
    time: (i) => {
      return validateRequiredTime(i) &&
             validatePastOrNow(form.date, i, form);
    },
    link: validateUrl,
    text: (i) => validateText(i, true)
  };

  bindInputValidation(form, validators);

  bindSubmitValidation(form, () => {
    const ok =
      validators.msg_id(form.msg_id) &&
      validators.date(form.date) &&
      validators.time(form.time) &&
      validators.link(form.link) &&
      validators.text(form.text);

    return ok;
  });
}

/**
 * Binds validation for Search Form (text only).
 */
export function bindSearchForm() {
  const form = document.querySelector(".search-form");
  if (!form) return;

  const input = form.querySelector('[name="query"]');
  if (!input) return;

  input.addEventListener("blur", () => validateSearchQueryStrict(input));
  input.addEventListener("input", () => validateSearchQueryStrict(input));

  form.addEventListener("submit", (e) => {
    if (!validateSearchQueryStrict(input, true)) {
      e.preventDefault();
      e.stopPropagation();
    }
  });
}

/**
 * Binds validation handlers for the Filter Form.
 */
export function bindFilterForm() {
  const form = document.querySelector(".filter-form");
  if (!form) return;

  const modeSelect = form.querySelector('[name="date_mode"]');
  const startInput = form.querySelector('[name="start_date"]');
  const endInput = form.querySelector('[name="end_date"]');

  bindInputValidation(form, {
    date_mode: (el) => validateModeSelected(el, form),
    start_date: (el) => {
      if (modeSelect.value === "between") {
        return validateBetween(startInput, endInput, form);
      } else {
        return validateSingleDate(el);
      }
    },
    end_date: (el) => {
      if (modeSelect.value === "between") {
        return validateBetween(startInput, endInput, form);
      }
      return true;
    }
  });

  const realActionInput = form.querySelector('input[name="real_action"]');
  form.querySelectorAll("button[name='action']").forEach((btn) => {
    btn.addEventListener("click", () => {
      realActionInput.value = btn.value;
    });
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    e.stopPropagation();

    const action = "filter";
    const isValid = validateFilterFormStrict(form, action);

    if (isValid) {
      form.submit();
    }
  });
}
