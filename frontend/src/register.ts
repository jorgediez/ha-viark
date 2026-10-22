/**
 * Define a custom element where Home Assistant's frontend will find it.
 *
 * The integration loads the card as an extra module, which runs while the
 * frontend is still booting. During boot the frontend replaces
 * `window.customElements` with a scoped-registry polyfill, a new registry that
 * knows nothing defined before it. A card defined first lands in the browser's
 * own registry, and the dashboard shows it as a configuration error. Whether
 * that happens depends on which script the browser runs first, so a cached card
 * hits it far more often.
 *
 * The frontend's page carries `<home-assistant>` from the start and defines it
 * only after the swap, so the card waits for that. Anywhere else (tests, the
 * demo page) or once the frontend is up, it defines at once.
 */
export function defineWhenReady(
  tag: string,
  element: CustomElementConstructor,
  onDefined?: () => void,
): void {
  const define = () => {
    // Read the registry now, not at load: by then it may be a different object.
    const registry = window.customElements;
    if (registry.get(tag)) {
      return;
    }
    registry.define(tag, element);
    onDefined?.();
  };

  const booting =
    document.querySelector("home-assistant") !== null &&
    !window.customElements.get("home-assistant");
  if (booting) {
    void window.customElements.whenDefined("home-assistant").then(define);
  } else {
    define();
  }
}
