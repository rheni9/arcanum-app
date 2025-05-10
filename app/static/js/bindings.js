import {
  bindChatSortHandlers,
  bindMessageSortHandlers,
  attachSortHandlers
} from "./ui/sorting.js";
import { bindClickableRows } from "./ui/clickables.js";

/**
 * Rebind all interactive behaviors after dynamic content replacement.
 * Useful after AJAX updates or partial template rendering.
 */
export function rebindAfterAjax() {
  bindChatSortHandlers();
  bindMessageSortHandlers();
  attachSortHandlers();
  bindClickableRows();
}
