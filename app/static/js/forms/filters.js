/**
 * @file filters.js
 * @description
 * Dynamic behavior for filter/search forms in Arcanum.
 * Handles input visibility, form validation, feedback messages,
 * and result container toggling.
 */

/**
 * Toggle visibility of the end date input
 * based on the selected date mode.
 */
export function toggleEndDateVisibility() {
  const mode = document.querySelector(".date-mode-select");
  const endDate = document.getElementById("end_date");

  if (!mode || !endDate) return;

  endDate.style.display = (mode.value === "between")
    ? "inline-block"
    : "none";
}

/**
 * Reset conflicting inputs:
 * - If search query is filled, clear date inputs.
 * - If date filters are filled, clear the search query.
 *
 * @param {HTMLFormElement} form - The active filter/search form.
 * @param {string} action - The action type ('search' or 'filter').
 */
export function resetConflictingFilters(form, action) {
  const query = form.query?.value.trim();
  const start = form.start_date?.value.trim();
  const end = form.end_date?.value.trim();

  if (action === "search" && query) {
    form.start_date.value = "";
    form.end_date.value = "";
  }

  if (action === "filter" && (start || end)) {
    form.query.value = "";
  }
}

/**
 * Insert an inline feedback message below the filter form.
 *
 * @param {HTMLFormElement} form - The active form element.
 * @param {string} message - Text content of the message.
 */
function insertInlineMessage(form, message) {
  const container = form.closest(".chat-filters-bar");

  // Remove existing box first
  const existing = container?.parentNode.querySelector(
    ".filter-summary-box[data-js='inline-msg']"
  );
  if (existing) existing.remove();

  // Create and insert new one
  const box = document.createElement("div");
  box.className = "filter-summary-box no-results";
  box.dataset.js = "inline-msg";
  box.innerHTML = `<p class="filter-summary no-results">${message}</p>`;
  container.insertAdjacentElement("afterend", box);
}


/**
 * Remove any previously inserted inline feedback message.
 *
 * @param {HTMLFormElement} form - The active form element.
 */
function removeInlineMessage(form) {
  const container = form.closest(".chat-filters-bar");
  const existing = container?.parentNode.querySelector(
    ".filter-summary-box[data-js='inline-msg']"
  );
  if (existing) existing.remove();
}

/**
 * Hide all previous result containers and summary boxes.
 * Used when form validation fails.
 */
export function hidePreviousResults() {
  const chatResults = document.querySelector(".chat-messages-table");
  if (chatResults) chatResults.classList.add("hidden");

  const globalResults = document.getElementById("results-table-container");
  if (globalResults) globalResults.classList.add("hidden");

  document.querySelectorAll(".filter-summary-box").forEach((box) => {
    box.classList.add("hidden");
  });
}

/**
 * Reveal previously hidden result containers and summary boxes.
 * Can be used after a valid search/filter, if needed.
 */
export function showPreviousResults() {
  document
    .querySelectorAll(
      ".chat-messages-table, #results-table-container, .filter-summary-box"
    )
    .forEach((el) => el.classList.remove("hidden"));
}

/**
 * Validate the filter/search form before submission.
 * Displays appropriate messages and prevents invalid submissions.
 *
 * @param {SubmitEvent} e - The form submit event.
 */
export function validateFilterForm(e) {
  const form = e.target;
  const submitter = document.activeElement;
  const action = submitter?.name === "action" ? submitter.value : "";

  removeInlineMessage(form);

  const queryField = form.query;
  const startField = form.start_date;
  const endField = form.end_date;
  const modeField = form.date_mode;

  const query = queryField?.value.trim();
  const start = startField?.value.trim();
  const end = endField?.value.trim();
  const mode = modeField?.value;

  [queryField, startField, endField].forEach(field => {
    field?.classList.remove("input-error");
  });

  // if (!query && !start && !end) {
  //   e.preventDefault();
  //   hidePreviousResults();
  //   insertInlineMessage(form, "JS: Please enter a search query or select a date filter.");
  //   return;
  // }

  if (action === "search") {
    if (!query) {
      e.preventDefault();
      queryField?.classList.add("input-error");
      hidePreviousResults();
      insertInlineMessage(form, "JS: Please enter a search query.");
      return;
    }

    startField.value = "";
    endField.value = "";
    return;
  }

  if (action === "filter") {
    if (!mode) {
      e.preventDefault();
      hidePreviousResults();
      insertInlineMessage(form, "JS: Please select a date filter mode.");
      return;
    }

    if (mode === "between") {
      if (!start && !end) {
        e.preventDefault();
        startField?.classList.add("input-error");
        endField?.classList.add("input-error");
        hidePreviousResults();
        insertInlineMessage(form, "JS: Please provide both start and end dates.");
        return;
      }
      if (!start) {
        e.preventDefault();
        startField?.classList.add("input-error");
        hidePreviousResults();
        insertInlineMessage(form, "JS: Start date is required.");
        return;
      }
      if (!end) {
        e.preventDefault();
        endField?.classList.add("input-error");
        hidePreviousResults();
        insertInlineMessage(form, "JS: End date is required.");
        return;
      }
      if (start > end) {
        e.preventDefault();
        startField?.classList.add("input-error");
        endField?.classList.add("input-error");
        hidePreviousResults();
        insertInlineMessage(form, "JS: Start date must be before or equal to end date.");
        return;
      }
    } else {
      if (!start) {
        e.preventDefault();
        startField?.classList.add("input-error");
        hidePreviousResults();
        insertInlineMessage(form, "JS: Please provide a valid start date.");
        return;
      }
    }

    queryField.value = "";
    return;
  }

  // Fallback
  e.preventDefault();
  hidePreviousResults();
  insertInlineMessage(form, "Unknown action. Please try again.");
}

// export function validateFilterForm(e) {
//   const form = e.target;
//   const submitter = document.activeElement;
//   const action = submitter?.name === "action" ? submitter.value : "";

//   removeInlineMessage(form);

//   const query = form.query?.value.trim();
//   const start = form.start_date?.value.trim();
//   const end = form.end_date?.value.trim();
//   const mode = form.date_mode?.value;

//   if (!query && !start && !end) {
//     e.preventDefault();
//     hidePreviousResults();
//     insertInlineMessage(
//       form,
//       "Please enter a search query or select a date filter."
//     );
//     return;
//   }

//   if (action === "search") {
//     if (!query) {
//       e.preventDefault();
//       hidePreviousResults();
//       insertInlineMessage(form, "Please enter a search query.");
//       return;
//     }

//     form.start_date.value = "";
//     form.end_date.value = "";
//     return;
//   }

//   if (action === "filter") {
//     if (mode === "between") {
//       if (!start && !end) {
//         e.preventDefault();
//         hidePreviousResults();
//         insertInlineMessage(
//           form,
//           "Please provide both start and end dates."
//         );
//         return;
//       } else if (!start) {
//         e.preventDefault();
//         hidePreviousResults();
//         insertInlineMessage(form, "Start date is required.");
//         return;
//       } else if (!end) {
//         e.preventDefault();
//         hidePreviousResults();
//         insertInlineMessage(form, "End date is required.");
//         return;
//       } else if (start > end) {
//         e.preventDefault();
//         hidePreviousResults();
//         insertInlineMessage(
//           form,
//           "Start date must be before or equal to end date."
//         );
//         return;
//       }
//     } else {
//       if (!start) {
//         e.preventDefault();
//         hidePreviousResults();
//         insertInlineMessage(form, "Please provide a valid start date.");
//         return;
//       }
//     }

//     form.query.value = "";
//     return;
//   }

//   // Unknown action fallback
//   e.preventDefault();
//   hidePreviousResults();
//   insertInlineMessage(form, "Unknown action. Please try again.");
// }

/**
 * Bind dynamic behaviors to all forms with class 'chat-filter-form':
 * - Validates inputs before submission.
 * - Toggles end date input visibility based on selected mode.
 */
export function bindFilterForms() {
  document.querySelectorAll("form.chat-filter-form").forEach((form) => {
    // form.addEventListener("submit", validateFilterForm);
    toggleEndDateVisibility();

    const mode = form.querySelector(".date-mode-select");
    if (mode) {
      mode.addEventListener("change", toggleEndDateVisibility);
    }
  });
}
