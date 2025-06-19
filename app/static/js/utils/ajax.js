/**
 * @file ajax.js
 * @description
 * Provides helper functions for performing AJAX requests and manipulating HTML.
 * Includes utilities for fetch with headers, HTML parsing, and safe DOM replacement.
 */

import { csrfFetch } from "./csrf_fetch.js";

/**
 * Performs a secure HTML fetch via AJAX.
 * Injects CSRF token and returns a parsed HTML document.
 *
 * @param {string} url - The URL to fetch the HTML from.
 * @returns {Promise<Document>} - Parsed HTML document.
 */
export async function ajaxFetchHtml(url) {
  const response = await csrfFetch(url, {
    headers: { "X-Requested-With": "XMLHttpRequest" }
  });
  const text = await response.text();
  return new DOMParser().parseFromString(text, "text/html");
}

/**
 * Replaces a DOM element by its ID using new HTML content.
 * Accepts either a full HTML Document or a string.
 *
 * @param {string} id - ID of the existing element to replace.
 * @param {Document|string} source - Parsed HTML document or raw HTML string.
 */
export function replaceElementById(id, source) {
  const existing = document.getElementById(id);
  if (!existing) return;

  const doc = typeof source === "string"
    ? new DOMParser().parseFromString(source, "text/html")
    : source;

    const replacement = doc.getElementById(id);
  if (replacement) {
    existing.replaceWith(replacement);
  } else {
    console.warn(`[ajax] Replacement #${id} not found in AJAX response`);
  }
}
