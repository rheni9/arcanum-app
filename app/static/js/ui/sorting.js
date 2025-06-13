/**
 * @file sorting.js
 * @description
 * Handles sortable table headers with AJAX reloading and scroll persistence.
 * Supports both flat and grouped table structures.
 */

import { ajaxFetchHtml, replaceElementById } from "../utils/ajax.js";
import { rebindAfterAjax } from "../bindings.js";

/**
 * Bind sorting handlers for the main chat list table.
 * Applies AJAX reload with scroll position preservation.
 */
export function bindChatSortHandlers() {
  const headers = document.querySelectorAll(".chats-table th.sortable");

  headers.forEach((header) => {
    header.addEventListener("click", async () => {
      const sortBy = header.getAttribute("data-sort");
      const url = new URL(window.location.href);
      const currentSort = url.searchParams.get("sort");
      const currentOrder = url.searchParams.get("order") || "asc";

      const newOrder = (currentSort === sortBy && currentOrder === "asc") ? "desc" : "asc";

      url.searchParams.set("sort", sortBy);
      url.searchParams.set("order", newOrder);
      url.searchParams.set("t", Date.now());

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
          console.warn("Container or replacement not found");
        }
      } catch (err) {
        console.error("Sorting AJAX failed:", err);
      }
    });
  });
}

/**
 * Bind sorting handlers for message tables (used in single chat or search view).
 * Sorts by clicking on column headers with class "sortable".
 */
export function bindMessageSortHandlers() {
  const headers = document.querySelectorAll(".messages-table th.sortable");

  headers.forEach((header) => {
    header.onclick = async () => {
      const sortField = header.dataset.sort;
      if (!sortField) {
        console.warn("[message sort] Missing data-sort on header:", header);
        return;
      }

      const url = new URL(window.location.href);
      const currentSort = url.searchParams.get("sort");
      const currentOrder = url.searchParams.get("order") || "asc";
      const newOrder = (currentSort === sortField && currentOrder === "asc") ? "desc" : "asc";

      url.searchParams.set("sort", sortField);
      url.searchParams.set("order", newOrder);
      url.searchParams.set("t", Date.now());  // cache-buster

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
          console.warn("[message sort] Container or replacement not found");
        }
      } catch (err) {
        console.error("[message sort] AJAX failed:", err);
      }
    };
  });
}

/**
 * Bind sorting handlers for each messages table grouped by chat.
 * Sort is applied individually per chat via AJAX.
 */
export function attachSortHandlers() {
  document.querySelectorAll(".messages-table th.sortable").forEach(header => {
    const chatSlug = header.dataset.chat;
    const sortField = header.dataset.sort;

    // Skip - if there is no group chat
    if (!chatSlug || !sortField) return;

    header.onclick = async () => {
      const containerId = `container-${chatSlug}`;
      const container = document.getElementById(containerId);
      const arrow = header.querySelector(".sort-arrow");

      if (!container) {
        console.warn("[grouped sort] Container not found:", containerId);
        return;
      }

      const currentOrder = arrow?.textContent?.includes("▲") ? "asc" : "desc";
      const newOrder = currentOrder === "asc" ? "desc" : "asc";

      const url = new URL(window.location.href);
      const params = new URLSearchParams(url.search);

      params.set("chat", chatSlug);
      params.set("sort", sortField);
      params.set("order", newOrder);
      params.set("t", Date.now());  // cache-buster

      url.search = params.toString();

      console.log(`[grouped sort] Chat=${chatSlug}, Sort=${sortField}, Order=${newOrder}`);

      try {
        const doc = await ajaxFetchHtml(url.toString());
        const newContainer = doc.getElementById(containerId);

        if (newContainer) {
          container.replaceWith(newContainer);
          rebindAfterAjax();
        } else {
          console.warn(`[grouped sort] Replacement #${containerId} not found`);
        }
      } catch (err) {
        console.error("[grouped sort] AJAX request failed:", err);
      }
    };
  });
}
