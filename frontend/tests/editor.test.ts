// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";

// Imported for its side effect: it defines the viark-remote-card-editor element.
import "../src/editor";
import type { ViarkRemoteCardEditor } from "../src/editor";
import type { HomeAssistant, ViarkRemoteCardConfig } from "../src/types";

const PLAYER = "media_player.viark_sat_4k";

const hass = (language = "en"): HomeAssistant => ({
  states: {},
  language,
  callService: () => Promise.resolve(undefined),
});

interface HaForm extends HTMLElement {
  data: Record<string, unknown>;
  schema: { name: string; selector?: Record<string, unknown> }[];
  computeLabel(item: { name: string }): string;
  computeHelper(item: { name: string }): string | undefined;
}

async function mount(
  config: Partial<ViarkRemoteCardConfig> = {},
  language = "en",
): Promise<{ editor: ViarkRemoteCardEditor; form: HaForm }> {
  const editor = document.createElement(
    "viark-remote-card-editor",
  ) as ViarkRemoteCardEditor;
  editor.setConfig({ type: "custom:viark-remote-card", entity: PLAYER, ...config });
  editor.hass = hass(language);
  document.body.append(editor);
  await editor.updateComplete;
  return { editor, form: editor.shadowRoot!.querySelector("ha-form") as HaForm };
}

/** Changes the form as Home Assistant's ha-form would, and returns the saved config. */
function edit(editor: ViarkRemoteCardEditor, form: HaForm, value: object) {
  const saved: unknown[] = [];
  editor.addEventListener("config-changed", (ev) =>
    saved.push((ev as CustomEvent<{ config: unknown }>).detail.config),
  );
  form.dispatchEvent(new CustomEvent("value-changed", { detail: { value } }));
  return saved;
}

afterEach(() => {
  document.body.replaceChildren();
  delete window.loadCardHelpers;
});

describe("editor", () => {
  it("shows the configuration with the defaults filled in", async () => {
    const { form } = await mount({ show_name: false });

    expect(form.data).toEqual({
      type: "custom:viark-remote-card",
      entity: PLAYER,
      show_name: false,
      show_status: true,
      haptics: true,
    });
  });

  it("only offers the integration's media player and remote", async () => {
    const { form } = await mount();
    const entityField = form.schema.find((item) => item.name === "entity");

    expect(entityField?.selector).toEqual({
      entity: {
        filter: [
          { integration: "viark", domain: "media_player" },
          { integration: "viark", domain: "remote" },
        ],
      },
    });
  });

  it("saves minimal YAML, leaving out options at their default", async () => {
    const { editor, form } = await mount();

    const saved = edit(editor, form, {
      type: "custom:viark-remote-card",
      entity: PLAYER,
      name: "",
      show_name: true,
      show_status: false,
      haptics: true,
    });

    expect(saved).toEqual([
      { type: "custom:viark-remote-card", entity: PLAYER, show_status: false },
    ]);
  });

  it("keeps button overrides it does not edit", async () => {
    const buttons = { update: { key: 25 } };
    const { editor, form } = await mount({ buttons });

    const saved = edit(editor, form, { ...form.data, name: "Bedroom" });

    expect(saved).toEqual([
      { type: "custom:viark-remote-card", entity: PLAYER, name: "Bedroom", buttons },
    ]);
  });

  it("labels the fields in the user's language", async () => {
    const { form } = await mount({}, "es");

    expect(form.computeLabel({ name: "show_name" })).toBe("Mostrar nombre");
    expect(form.computeHelper({ name: "name" })).toBeTruthy();
    expect(form.computeHelper({ name: "show_name" })).toBeUndefined();
  });

  it("explains how to remap the unsupported buttons", async () => {
    const { editor } = await mount();

    expect(editor.shadowRoot!.querySelector(".hint")?.textContent).toContain(
      "<, >, UPDATE",
    );
  });

  it("makes Home Assistant load ha-form when it is not loaded yet", async () => {
    const getConfigElement = vi.fn(() => Promise.resolve(undefined));
    class ButtonCard {
      static getConfigElement = getConfigElement;
    }
    const createCardElement = vi.fn(() => Promise.resolve(new ButtonCard()));
    window.loadCardHelpers = vi.fn(() =>
      Promise.resolve({
        createCardElement: createCardElement as unknown as (
          config: Record<string, unknown>,
        ) => Promise<HTMLElement>,
      }),
    );

    await mount();
    await vi.waitFor(() => expect(getConfigElement).toHaveBeenCalledOnce());

    expect(createCardElement).toHaveBeenCalledWith({ type: "button" });
  });

  it("still renders when the card helpers are unavailable", async () => {
    window.loadCardHelpers = () => Promise.reject(new Error("not in Home Assistant"));

    const { form } = await mount();

    expect(form).not.toBeNull();
  });
});
