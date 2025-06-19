/**
 * @file base.js
 * @description
 * Entry point for Arcanum frontend behavior.
 * Initializes all core UI features and event bindings.
 */

import { bindAuth } from "./auth.js";
import { bindDeleteConfirmations } from "./ui/deleteConfirm.js";
import { bindClickableRows } from "./ui/clickables.js";
import { rebindAfterAjax } from "./bindings.js";

/**
 * Initialize all global UI behaviors after DOM is fully loaded.
 */
document.addEventListener("DOMContentLoaded", () => {
  bindAuth();
  bindDeleteConfirmations();
  bindClickableRows();
  rebindAfterAjax();
});
