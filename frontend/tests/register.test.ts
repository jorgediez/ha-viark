// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";

import { defineWhenReady } from "../src/register";

/** A registry like the frontend's polyfill: new, and empty. */
function freshRegistry(): CustomElementRegistry {
  const defined = new Map<string, CustomElementConstructor>();
  return {
    get: (tag: string) => defined.get(tag),
    define: (tag: string, element: CustomElementConstructor) => {
      defined.set(tag, element);
    },
    whenDefined: () => new Promise(() => {}),
  } as unknown as CustomElementRegistry;
}

const element = () => class extends HTMLElement {};

const native = window.customElements;

afterEach(() => {
  Object.defineProperty(window, "customElements", {
    value: native,
    configurable: true,
    writable: true,
  });
  document.body.innerHTML = "";
});

describe("defineWhenReady", () => {
  it("defines at once outside Home Assistant's page", () => {
    const onDefined = vi.fn();
    const Element = element();

    defineWhenReady("viark-test-plain", Element, onDefined);

    expect(window.customElements.get("viark-test-plain")).toBe(Element);
    expect(onDefined).toHaveBeenCalledOnce();
  });

  it("leaves an element defined by another copy alone", () => {
    const First = element();
    window.customElements.define("viark-test-twice", First);
    const onDefined = vi.fn();

    defineWhenReady("viark-test-twice", element(), onDefined);

    expect(window.customElements.get("viark-test-twice")).toBe(First);
    expect(onDefined).not.toHaveBeenCalled();
  });

  // Last: it defines <home-assistant> in the shared registry.
  it("waits for the frontend to swap registries while it boots", async () => {
    document.body.innerHTML = "<home-assistant></home-assistant>";
    const onDefined = vi.fn();
    const Element = element();

    defineWhenReady("viark-test-boot", Element, onDefined);
    expect(native.get("viark-test-boot")).toBeUndefined();
    expect(onDefined).not.toHaveBeenCalled();

    // The frontend boots: a new registry replaces the browser's, then the
    // frontend defines its root element, which also reaches the browser's.
    const polyfill = freshRegistry();
    Object.defineProperty(window, "customElements", {
      value: polyfill,
      configurable: true,
      writable: true,
    });
    native.define("home-assistant", element());
    await native.whenDefined("home-assistant");
    await Promise.resolve();

    expect(polyfill.get("viark-test-boot")).toBe(Element);
    expect(native.get("viark-test-boot")).toBeUndefined();
    expect(onDefined).toHaveBeenCalledOnce();
  });

  it("defines at once when the frontend is already up", () => {
    document.body.innerHTML = "<home-assistant></home-assistant>";
    const Element = element();

    defineWhenReady("viark-test-late", Element);

    expect(window.customElements.get("viark-test-late")).toBe(Element);
  });
});
