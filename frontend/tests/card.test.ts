// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HOLD_DELAY_MS, REPEAT_INTERVAL_MS } from "../src/const";
import type { HassEntity, HomeAssistant, ViarkRemoteCardConfig } from "../src/types";
import { ViarkRemoteCard } from "../src/viark-remote-card";

const PLAYER = "media_player.viark_sat_4k";
const REMOTE = "remote.viark_sat_4k_remote";

const entity = (
  entity_id: string,
  state: string,
  attributes: Record<string, unknown> = {},
): HassEntity => ({ entity_id, state, attributes });

const playing = () =>
  entity(PLAYER, "playing", {
    friendly_name: "Living room receiver",
    media_channel: "2",
    media_title: "Sports HD",
  });

type CallService = HomeAssistant["callService"];

function makeHass(
  states: HassEntity[] = [playing(), entity(REMOTE, "on")],
  overrides: Partial<HomeAssistant> = {},
): HomeAssistant & { callService: ReturnType<typeof vi.fn<CallService>> } {
  return {
    states: Object.fromEntries(states.map((s) => [s.entity_id, s])),
    entities: {
      [PLAYER]: { entity_id: PLAYER, device_id: "dev1", platform: "viark" },
      [REMOTE]: { entity_id: REMOTE, device_id: "dev1", platform: "viark" },
    },
    language: "en",
    callService: vi.fn<CallService>(() => Promise.resolve(undefined)),
    ...overrides,
  } as HomeAssistant & { callService: ReturnType<typeof vi.fn<CallService>> };
}

async function mount(
  config: Partial<ViarkRemoteCardConfig> = {},
  hass: HomeAssistant = makeHass(),
): Promise<ViarkRemoteCard> {
  const card = document.createElement("viark-remote-card") as ViarkRemoteCard;
  card.setConfig({ type: "custom:viark-remote-card", entity: PLAYER, ...config });
  card.hass = hass;
  document.body.append(card);
  await card.updateComplete;
  return card;
}

const root = (card: ViarkRemoteCard) => card.shadowRoot!;
const button = (card: ViarkRemoteCard, id: string) =>
  root(card).querySelector<HTMLButtonElement>(`button[data-button="${id}"]`)!;
const statusText = (card: ViarkRemoteCard) =>
  root(card).querySelector(".status")?.textContent?.trim();

/** Collects the events a card fires, by type. */
function listen(card: ViarkRemoteCard, ...types: string[]) {
  const seen: { type: string; detail: unknown }[] = [];
  for (const type of types) {
    card.addEventListener(type, (ev) =>
      seen.push({ type, detail: (ev as CustomEvent).detail }),
    );
  }
  return seen;
}

/** Lets a press finish: the click handler starts it without awaiting. */
const settle = () => new Promise((resolve) => setTimeout(resolve));

afterEach(() => {
  document.body.replaceChildren();
  vi.useRealTimers();
});

describe("rendering", () => {
  it("draws every button of the remote with an accessible label", async () => {
    const card = await mount();
    const buttons = root(card).querySelectorAll("button");

    expect(buttons).toHaveLength(49);
    for (const b of buttons) {
      expect(b.getAttribute("aria-label"), b.dataset.button).toBeTruthy();
    }
    expect(button(card, "power").getAttribute("aria-label")).toBe("Power");
  });

  it("shows the channel playing and an on LED", async () => {
    const card = await mount();

    expect(statusText(card)).toBe("2  Sports HD");
    expect(root(card).querySelector(".led")?.classList.contains("on")).toBe(true);
    expect(root(card).querySelector(".name")?.textContent).toBe("VIARK");
  });

  it("names the remote after the receiver for screen readers", async () => {
    const card = await mount();

    expect(root(card).querySelector(".remote")?.getAttribute("aria-label")).toBe(
      "Living room receiver",
    );
  });

  it("finds the media player through the device when bound to the remote", async () => {
    const card = await mount({ entity: REMOTE });

    expect(statusText(card)).toBe("2  Sports HD");
  });

  it("reports soft standby", async () => {
    const card = await mount({}, makeHass([entity(PLAYER, "off")]));

    expect(statusText(card)).toBe("Standby");
    expect(root(card).querySelector(".led")?.classList.contains("standby")).toBe(true);
    expect(button(card, "power").disabled).toBe(false);
  });

  it("greys every button out when the receiver is unavailable", async () => {
    const card = await mount({}, makeHass([entity(PLAYER, "unavailable")]));

    expect(statusText(card)).toBe("Unavailable");
    for (const b of root(card).querySelectorAll("button")) {
      expect(b.disabled, b.dataset.button).toBe(true);
    }
  });

  it("explains a missing entity instead of drawing the remote", async () => {
    const card = await mount({}, makeHass([]));

    expect(root(card).querySelector(".warning")?.textContent?.trim()).toBe(
      `Entity not available: ${PLAYER}`,
    );
    expect(root(card).querySelectorAll("button")).toHaveLength(0);
  });

  it("hides the name and status when asked", async () => {
    const card = await mount({ show_name: false, show_status: false });

    expect(root(card).querySelector(".name")).toBeNull();
    expect(root(card).querySelector(".status")).toBeNull();
  });

  it("prints a custom name", async () => {
    const card = await mount({ name: "Bedroom" });

    expect(root(card).querySelector(".name")?.textContent).toBe("Bedroom");
  });

  it("speaks the user's language", async () => {
    const card = await mount(
      {},
      makeHass([entity(PLAYER, "off")], { language: "es", locale: { language: "es" } }),
    );

    expect(statusText(card)).toBe("En espera");
    expect(button(card, "power").getAttribute("aria-label")).toBe("Encendido");
  });
});

describe("pressing buttons", () => {
  it("sends a key through viark.send_key", async () => {
    const hass = makeHass();
    const card = await mount({}, hass);

    button(card, "epg").click();
    await settle();

    expect(hass.callService).toHaveBeenCalledExactlyOnceWith(
      "viark",
      "send_key",
      { key: "epg" },
      { entity_id: PLAYER },
    );
  });

  it("sends a key through remote.send_command when bound to the remote", async () => {
    const hass = makeHass();
    const card = await mount({ entity: REMOTE }, hass);

    button(card, "mute").click();
    await settle();

    expect(hass.callService).toHaveBeenCalledExactlyOnceWith(
      "remote",
      "send_command",
      { command: "mute" },
      { entity_id: REMOTE },
    );
  });

  it("toggles power through the entity", async () => {
    const hass = makeHass();
    const card = await mount({}, hass);

    button(card, "power").click();
    await settle();

    expect(hass.callService).toHaveBeenCalledExactlyOnceWith(
      "media_player",
      "toggle",
      undefined,
      { entity_id: PLAYER },
    );
  });

  it("runs an override's action", async () => {
    const hass = makeHass();
    const card = await mount(
      { buttons: { update: { perform_action: "script.turn_on", data: { x: 1 } } } },
      hass,
    );

    button(card, "update").click();
    await settle();

    expect(hass.callService).toHaveBeenCalledExactlyOnceWith(
      "script",
      "turn_on",
      { x: 1 },
      undefined,
    );
  });

  it("does nothing for a disabled button", async () => {
    const hass = makeHass();
    const card = await mount({ buttons: { epg: { action: "none" } } }, hass);
    const events = listen(card, "haptic", "hass-notification");

    button(card, "epg").click();
    await settle();

    expect(hass.callService).not.toHaveBeenCalled();
    expect(events).toEqual([]);
  });

  it("explains a button the integration cannot send yet", async () => {
    const hass = makeHass();
    const card = await mount({}, hass);
    const events = listen(card, "haptic", "hass-notification");

    button(card, "update").click();
    await settle();

    expect(hass.callService).not.toHaveBeenCalled();
    expect(events).toEqual([
      { type: "haptic", detail: "warning" },
      {
        type: "hass-notification",
        detail: { message: "Update is not supported by the Viark integration yet." },
      },
    ]);
  });

  it("vibrates on a press, and not when haptics are off", async () => {
    const card = await mount();
    const events = listen(card, "haptic");
    button(card, "ok").click();
    await settle();
    expect(events).toEqual([{ type: "haptic", detail: "light" }]);

    const quiet = await mount({ haptics: false });
    const none = listen(quiet, "haptic");
    button(quiet, "ok").click();
    await settle();
    expect(none).toEqual([]);
  });

  it("signals a failed action without throwing", async () => {
    const hass = makeHass();
    hass.callService.mockRejectedValueOnce(new Error("Unknown Viark key"));
    vi.spyOn(console, "debug").mockImplementation(() => undefined);
    const card = await mount({}, hass);
    const events = listen(card, "haptic");

    button(card, "epg").click();
    await settle();

    expect(events).toEqual([
      { type: "haptic", detail: "light" },
      { type: "haptic", detail: "failure" },
    ]);
  });
});

describe("holding a button", () => {
  let hass: ReturnType<typeof makeHass>;
  let card: ViarkRemoteCard;

  beforeEach(async () => {
    hass = makeHass();
    card = await mount({}, hass);
    vi.useFakeTimers();
  });

  const pointer = (id: string, type: string, init: PointerEventInit = {}) =>
    button(card, id).dispatchEvent(
      new PointerEvent(type, { bubbles: true, button: 0, ...init }),
    );

  it("repeats a repeatable key at the receiver's pace until released", async () => {
    pointer("vol_up", "pointerdown");
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS);
    expect(hass.callService).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(REPEAT_INTERVAL_MS * 2);
    expect(hass.callService).toHaveBeenCalledTimes(3);

    pointer("vol_up", "pointerup");
    await vi.advanceTimersByTimeAsync(REPEAT_INTERVAL_MS * 4);
    expect(hass.callService).toHaveBeenCalledTimes(3);

    // The click that ends a hold must not send the key once more.
    button(card, "vol_up").dispatchEvent(new MouseEvent("click", { detail: 1 }));
    await vi.advanceTimersByTimeAsync(0);
    expect(hass.callService).toHaveBeenCalledTimes(3);
  });

  it("sends nothing when the pointer is cancelled, as when scrolling", async () => {
    pointer("vol_up", "pointerdown");
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS / 2);
    pointer("vol_up", "pointercancel");
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS * 4);

    expect(hass.callService).not.toHaveBeenCalled();
  });

  it("presses once on a short tap", async () => {
    pointer("vol_up", "pointerdown");
    pointer("vol_up", "pointerup");
    button(card, "vol_up").dispatchEvent(new MouseEvent("click", { detail: 1 }));
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS * 4);

    expect(hass.callService).toHaveBeenCalledExactlyOnceWith(
      "viark",
      "send_key",
      { key: "volume_up" },
      { entity_id: PLAYER },
    );
  });

  it("does not repeat keys that should not", async () => {
    pointer("epg", "pointerdown");
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS * 4);

    expect(hass.callService).not.toHaveBeenCalled();
  });

  it("ignores a right-button press", async () => {
    pointer("vol_up", "pointerdown", { button: 2 });
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS * 4);

    expect(hass.callService).not.toHaveBeenCalled();
  });

  it("stops repeating when the card leaves the page", async () => {
    pointer("vol_up", "pointerdown");
    await vi.advanceTimersByTimeAsync(HOLD_DELAY_MS);
    card.remove();
    await vi.advanceTimersByTimeAsync(REPEAT_INTERVAL_MS * 4);

    expect(hass.callService).toHaveBeenCalledTimes(1);
  });

  it("keeps the long-press menu from opening on repeatable keys only", () => {
    const menu = (id: string) =>
      button(card, id).dispatchEvent(new Event("contextmenu", { cancelable: true }));

    expect(menu("vol_up")).toBe(false);
    expect(menu("epg")).toBe(true);
  });
});

describe("updates", () => {
  it("re-renders only when an entity the card shows changes", async () => {
    const hass = makeHass([playing(), entity(REMOTE, "on"), entity("light.x", "on")]);
    const card = await mount({ entity: REMOTE }, hass);
    const render = vi.spyOn(card as unknown as { render(): unknown }, "render");

    card.hass = {
      ...hass,
      states: { ...hass.states, "light.x": entity("light.x", "off") },
    };
    await card.updateComplete;
    expect(render).not.toHaveBeenCalled();

    // The remote's media player, found through the device, counts too.
    const changed = {
      ...playing(),
      attributes: { media_channel: "3", media_title: "Jazz" },
    };
    card.hass = { ...card.hass, states: { ...card.hass.states, [PLAYER]: changed } };
    await card.updateComplete;
    expect(render).toHaveBeenCalledOnce();
    expect(statusText(card)).toBe("3  Jazz");
  });

  it("re-renders when the language changes", async () => {
    const card = await mount({}, makeHass([entity(PLAYER, "off")]));

    card.hass = { ...card.hass!, language: "es", locale: { language: "es" } };
    await card.updateComplete;

    expect(statusText(card)).toBe("En espera");
  });
});

describe("card API", () => {
  it("rejects an invalid configuration with a readable error", () => {
    const card = document.createElement("viark-remote-card") as ViarkRemoteCard;

    expect(() =>
      card.setConfig({ type: "custom:viark-remote-card", entity: "light.kitchen" }),
    ).toThrow("'entity' must be a media_player or remote entity");
  });

  it("suggests the receiver's media player in the card picker", () => {
    expect(ViarkRemoteCard.getStubConfig(makeHass())).toEqual({ entity: PLAYER });
    expect(ViarkRemoteCard.getStubConfig(makeHass([], { entities: {} }))).toEqual({
      entity: "media_player.viark_receiver",
    });
  });

  it("sizes itself for masonry and sections views", async () => {
    const card = await mount();

    expect(card.getCardSize()).toBe(16);
    expect(card.getGridOptions()).toEqual({ columns: 6, min_columns: 4 });
  });

  it("offers its editor", () => {
    expect(ViarkRemoteCard.getConfigElement().tagName.toLowerCase()).toBe(
      "viark-remote-card-editor",
    );
  });

  it("registers itself with the card picker", () => {
    expect(window.customCards).toContainEqual(
      expect.objectContaining({ type: "viark-remote-card", preview: true }),
    );
  });
});
