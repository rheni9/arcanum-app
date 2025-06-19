/**
 * @file bindings.js
 * @description
 * Rebinds all interactive UI behaviors after dynamic content updates.
 * Ensures proper functioning of sort handlers and clickable elements
 * when content is replaced via AJAX.
 */

import {
  bindChatSortHandlers,
  bindMessageSortHandlers,
  attachSortHandlers
} from "./ui/sorting.js";
import { bindClickableRows } from "./ui/clickables.js";

/**
 * Rebinds event listeners for dynamic UI components.
 * Should be called after inserting or replacing HTML fragments via AJAX,
 * to restore sorting, click navigation, and other UI functionality.
 */
export function rebindAfterAjax() {
  bindClickableRows();
  bindChatSortHandlers();

  if (document.getElementById("messages-table-container")) {
    bindMessageSortHandlers();
  } else {
    attachSortHandlers();
  }
}
