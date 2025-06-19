/**
 * @file toggles.js
 * @description
 * Manages dependency logic for toggle switches in Arcanum forms.
 * Specifically disables dependent checkboxes when parent is inactive.
 */

/**
 * Initializes toggle logic for chat form.
 * Disables "is_member" and "is_public" if "is_active" is unchecked.
 */
export function initChatToggles() {
  const activeToggle = document.querySelector("#is_active");
  const memberToggle = document.querySelector("#is_member");
  const publicToggle = document.querySelector("#is_public");

  // Ensure all toggles exist and are input elements of type checkbox
  if (
    !(activeToggle instanceof HTMLInputElement) ||
    !(memberToggle instanceof HTMLInputElement) ||
    !(publicToggle instanceof HTMLInputElement)
  ) return;

  /**
   * Updates toggle dependencies based on active state.
   */
  const updateToggles = () => {
    const isActive = activeToggle.checked;

    memberToggle.disabled = !isActive;
    publicToggle.disabled = !isActive;

    // Optionally uncheck dependent toggles when disabled
    if (!isActive) {
      memberToggle.checked = false;
      publicToggle.checked = false;
    }
  };

  // Initial state
  updateToggles();

  // On toggle
  activeToggle.addEventListener("change", updateToggles);
}
