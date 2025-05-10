/**
 * @file ajax.js
 * @description
 * Provides helper functions for performing AJAX requests and manipulating HTML.
 * Includes utilities for fetch with headers, HTML parsing, and safe DOM replacement.
 */

/**
 * Fetch a URL and return a parsed HTML document.
 * @param {string} url
 * @returns {Promise<Document>}
 */
export async function ajaxFetchHtml(url) {
  const response = await fetch(url, {
    headers: { "X-Requested-With": "XMLHttpRequest" },
    credentials: "same-origin"
  });
  const text = await response.text();
  return new DOMParser().parseFromString(text, "text/html");
}

/**
 * Replace an existing element by ID with a new one from given HTML.
 * @param {string} id
 * @param {Document|string} source
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
