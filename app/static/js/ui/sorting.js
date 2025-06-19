/**
 * @file sorting.js
 * @description
 * Binds sorting handlers to sortable table headers.
 * Supports AJAX-based updates with scroll preservation for:
 * - chat list
 * - message tables (single or grouped)
 */

import { ajaxFetchHtml } from "../utils/ajax.js";
import { rebindAfterAjax } from "../bindings.js";

/**
 * Binds AJAX sorting for the main chats table.
 * Restores scroll position and updates history state.
 */
export function bindChatSortHandlers() {
  const headers = document.querySelectorAll(".chats-table th.sortable");

  headers.forEach((header) => {
    header.addEventListener("click", async () => {
      const sortBy = header.dataset.sort;
      const url = new URL(window.location.href);
      const currentSort = url.searchParams.get("sort");
      const currentOrder = url.searchParams.get("order") || "asc";
      const newOrder =
        currentSort === sortBy && currentOrder === "asc" ? "desc" : "asc";

      url.searchParams.set("sort", sortBy);
      url.searchParams.set("order", newOrder);
      url.searchParams.set("t", Date.now()); // prevent cache

      const scrollY = window.scrollY;

      try {
        const doc = await ajaxFetchHtml(url.toString());
        const container = document.getElementById("chats-table-container");
        const replacement = doc.getElementById("chats-table-container");

        if (container && replacement) {
          container.innerHTML = replacement.innerHTML;
          history.replaceState(null, "", url);
          rebindAfterAjax();
          window.scrollTo(0, scrollY);
        } else {
          console.warn("[chat sort] Replacement container not found.");
        }
      } catch (error) {
        console.error("[chat sort] AJAX request failed:", error);
      }
    });
  });
}

/**
 * Binds AJAX sorting for message tables. 
 * Typically used in single chat view.
 */
export function bindMessageSortHandlers() {
  const headers = document.querySelectorAll(".messages-table th.sortable");

  headers.forEach((header) => {
    header.addEventListener("click", async () => {
      const sortBy = header.dataset.sort;
      if (!sortBy) {
        console.warn("[message sort] Missing data-sort on header.");
        return;
      }

      const url = new URL(window.location.href);
      const currentSort = url.searchParams.get("sort");
      const currentOrder = url.searchParams.get("order") || "asc";
      const newOrder =
        currentSort === sortBy && currentOrder === "asc" ? "desc" : "asc";

      url.searchParams.set("sort", sortBy);
      url.searchParams.set("order", newOrder);
      url.searchParams.set("t", Date.now()); // prevent cache

      const scrollY = window.scrollY;

      try {
        const doc = await ajaxFetchHtml(url.toString());
        const container = document.getElementById("messages-table-container");
        const replacement = doc.getElementById("messages-table-container");

        if (container && replacement) {
          container.innerHTML = replacement.innerHTML;
          history.replaceState(null, "", url);
          rebindAfterAjax();
          window.scrollTo(0, scrollY);
        } else {
          console.warn("[message sort] Replacement container not found.");
        }
      } catch (error) {
        console.error("[message sort] AJAX request failed:", error);
      }
    });
  });
}

/**
 * Binds AJAX sorting to messages tables grouped by chat.
 * Sorting is performed per-chat and reloads only the affected section.
 */
export function attachSortHandlers() {
  const headers = document.querySelectorAll(".messages-table th.sortable");

  headers.forEach((header) => {
    const chatSlug = header.dataset.chat;
    const sortField = header.dataset.sort;

    // Skip - if there is no group chat
    if (!chatSlug || !sortField) return;

    header.addEventListener("click", async () => {
      const containerId = `container-${chatSlug}`;
      const container = document.getElementById(containerId);
      const arrow = header.querySelector(".sort-arrow");

      if (!container) {
        console.warn(`[grouped sort] Container #${containerId} not found.`);
        return;
      }

      const currentOrder = arrow?.textContent?.includes("▲") ? "asc" : "desc";
      const newOrder = currentOrder === "asc" ? "desc" : "asc";

      const url = new URL(window.location.href);
      const params = url.searchParams;

      params.set("chat", chatSlug);
      params.set("sort", sortField);
      params.set("order", newOrder);
      params.set("t", Date.now()); // prevent cache

      url.search = params.toString();

      try {
        const doc = await ajaxFetchHtml(url.toString());
        const replacement = doc.getElementById(containerId);

        if (replacement) {
          container.replaceWith(replacement);
          rebindAfterAjax();
        } else {
          console.warn(`[grouped sort] Replacement #${containerId} not found.`);
        }
      } catch (error) {
        console.error("[grouped sort] AJAX request failed:", error);
      }
    });
  });
}
