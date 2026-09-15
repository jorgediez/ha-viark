import { describe, expect, it } from "vitest";

import { keyCall, resolveAction, validateConfig } from "../src/actions";
import { BUTTON_IDS, BUTTONS } from "../src/buttons";
import type { ViarkRemoteCardConfig } from "../src/types";

const PLAYER = "media_player.viark_sat_4k";
const REMOTE = "remote.viark_sat_4k_remote";

const config = (overrides: Partial<ViarkRemoteCardConfig> = {}): ViarkRemoteCardConfig => ({
  type: "custom:viark-remote-card",
  entity: PLAYER,
  ...overrides,
});

/**
 * KEY_ALIASES from custom_components/viark/const.py in jorgediez/ha-viark 1.1.0,
 * unchanged in 1.2.0.
 * Every named key the card sends must be one the integration accepts.
 */
const INTEGRATION_KEY_ALIASES = new Set([
  "up", "down", "left", "right", "ok", "select", "menu", "exit", "back",
  "red", "green", "yellow", "blue", "tv_radio", "mute", "recall", "satellite",
  "subtitle", "epg", "favourite", "favorite", "teletext", "volume_up",
  "volume_down", "page_up", "page_down", "find", "power", "usb", "audio",
  "freeze", "resolution", "timer", "f1", "f2", "info",
  "record", "rewind", "fast_forward", "play", "stop", "pause", "previous",
  "next", "channel_up", "channel_down",
  ...Array.from({ length: 10 }, (_, d) => `digit_${d}`),
]);

describe("button table", () => {
  it("only uses key names the integration knows", () => {
    for (const id of BUTTON_IDS) {
      const action = BUTTONS[id].action;
      if (action.type === "key") {
        expect(INTEGRATION_KEY_ALIASES, `button ${id}`).toContain(action.key);
      }
    }
  });

  it("leaves exactly the unmapped buttons without an action", () => {
    const unsupported = BUTTON_IDS.filter((id) => BUTTONS[id].action.type === "none");
    expect(unsupported.sort()).toEqual(
      ["chevron_left", "chevron_right", "update"].sort(),
    );
  });

  it("has every key of the physical remote", () => {
    expect(BUTTON_IDS).toHaveLength(49);
  });
});

describe("keyCall", () => {
  it("uses viark.send_key for a media player", () => {
    expect(keyCall(PLAYER, "epg")).toEqual({
      domain: "viark",
      service: "send_key",
      data: { key: "epg" },
      target: { entity_id: PLAYER },
    });
  });

  it("uses remote.send_command for a remote", () => {
    expect(keyCall(REMOTE, "epg")).toEqual({
      domain: "remote",
      service: "send_command",
      data: { command: "epg" },
      target: { entity_id: REMOTE },
    });
  });
});

describe("resolveAction", () => {
  it("toggles power through the bound entity", () => {
    expect(resolveAction("power", config())).toEqual({
      type: "call",
      call: { domain: "media_player", service: "toggle", target: { entity_id: PLAYER } },
    });
    expect(resolveAction("power", config({ entity: REMOTE }))).toEqual({
      type: "call",
      call: { domain: "remote", service: "toggle", target: { entity_id: REMOTE } },
    });
  });

  it("maps labelled buttons to integration keys", () => {
    expect(resolveAction("txt", config())).toEqual({ type: "call", call: keyCall(PLAYER, "teletext") });
    expect(resolveAction("digit_7", config())).toEqual({ type: "call", call: keyCall(PLAYER, "digit_7") });
    expect(resolveAction("tv_radio", config())).toEqual({ type: "call", call: keyCall(PLAYER, "tv_radio") });
  });

  it("maps the keys added in integration 1.1.0", () => {
    for (const [button, key] of [
      ["resol", "resolution"],
      ["audio", "audio"],
      ["timer", "timer"],
      ["f1", "f1"],
      ["f2", "f2"],
    ] as const) {
      expect(resolveAction(button, config()), button).toEqual({ type: "call", call: keyCall(PLAYER, key) });
    }
  });

  it("uses the receiver's dedicated channel keys, not the arrows", () => {
    expect(resolveAction("ch_up", config())).toEqual({ type: "call", call: keyCall(PLAYER, "channel_up") });
    expect(resolveAction("ch_down", config())).toEqual({ type: "call", call: keyCall(PLAYER, "channel_down") });
  });

  it("reports buttons the integration cannot send", () => {
    expect(resolveAction("update", config())).toEqual({ type: "unsupported" });
  });

  it("sends a raw key code override as text", () => {
    const cfg = config({ buttons: { f1: { key: 44 } } });
    expect(resolveAction("f1", cfg)).toEqual({ type: "call", call: keyCall(PLAYER, "44") });
  });

  it("performs an arbitrary action override", () => {
    const cfg = config({
      buttons: { update: { perform_action: "script.turn_on", target: { entity_id: "script.x" } } },
    });
    expect(resolveAction("update", cfg)).toEqual({
      type: "call",
      call: { domain: "script", service: "turn_on", data: undefined, target: { entity_id: "script.x" } },
    });
  });

  it("disables a button", () => {
    expect(resolveAction("power", config({ buttons: { power: { action: "none" } } }))).toEqual({
      type: "none",
    });
  });
});

describe("validateConfig", () => {
  it("accepts a minimal config", () => {
    expect(() => validateConfig(config())).not.toThrow();
    expect(() => validateConfig(config({ entity: REMOTE }))).not.toThrow();
  });

  it.each([
    [undefined, "Invalid configuration"],
    [{ type: "x" }, "Set 'entity'"],
    [config({ entity: "light.kitchen" }), "must be a media_player or remote"],
    [config({ haptics: "yes" as unknown as boolean }), "'haptics' must be true or false"],
    [config({ buttons: { nope: { key: "ok" } } }), "Unknown button 'nope'"],
    [config({ buttons: { f1: {} } }), "exactly one of"],
    [config({ buttons: { f1: { key: "ok", action: "none" } } }), "exactly one of"],
    [config({ buttons: { f1: { key: -1 } } }), "non-negative"],
    [config({ buttons: { f1: { perform_action: "script" } } }), "domain.action"],
    [config({ buttons: { f1: { key: "44", data: {} } } }), "only apply to 'perform_action'"],
    [config({ buttons: { f1: { action: "toggle" as "none" } } }), "only supports 'none'"],
  ])("rejects %j", (input, message) => {
    expect(() => validateConfig(input)).toThrow(message);
  });
});
