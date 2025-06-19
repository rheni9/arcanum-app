/**
 * @file clickables.js
 * @description
 * Handles clickable elements that redirect based on `data-href` attributes.
 * Commonly used for making table rows or cards behave like links.
 */

/**
 * Binds click handlers to all elements with class `clickable-row`.
 * Redirects to the URL defined in the `data-href` attribute.
 */
export function bindClickableRows() {
  document.querySelectorAll(".clickable-row").forEach((row) => {
    row.addEventListener("click", () => {
      if (event.target.tagName.toLowerCase() === 'a') return;
      const href = row.dataset.href;
      if (href) {
        window.location.href = href;
      }
    });
  });
}
