/**
 * @file base.js
 * @description
 * Entry point for Arcanum frontend behavior.
 * Initializes all core UI features and event bindings.
 */

import { bindFilterForms } from "./forms/filters.js";
import { bindActiveMemberDependency } from "./forms/state.js";
import { bindDeleteConfirmations } from "./ui/confirmations.js";
import { bindClickableRows } from "./ui/clickables.js";
import { rebindAfterAjax } from "./bindings.js";

/**
 * Initialize all global UI behaviors after DOM is ready.
 */
document.addEventListener("DOMContentLoaded", () => {
  bindFilterForms();
  bindActiveMemberDependency();
  bindDeleteConfirmations();  
  bindClickableRows();
  rebindAfterAjax();
});
