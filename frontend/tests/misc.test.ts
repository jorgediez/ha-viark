import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { BUTTON_IDS } from "../src/buttons";
import { VERSION } from "../src/const";
import { findMediaPlayer, findViarkEntity } from "../src/entities";
import { TRANSLATIONS, localize } from "../src/localize";
import type { HomeAssistant } from "../src/types";

const hass = (entities: HomeAssistant["entities"]): HomeAssistant => ({
  states: {},
  entities,
  callService: async () => undefined,
});

describe("entities", () => {
  const registry = {
    "light.kitchen": { entity_id: "light.kitchen", device_id: "d2", platform: "hue" },
    "remote.viark_remote": { entity_id: "remote.viark_remote", device_id: "d1", platform: "viark" },
    "media_player.viark": { entity_id: "media_player.viark", device_id: "d1", platform: "viark" },
  };

  it("finds the media player that shares the remote's device", () => {
    expect(findMediaPlayer(hass(registry), "remote.viark_remote")).toBe("media_player.viark");
    expect(findMediaPlayer(hass(registry), "media_player.viark")).toBe("media_player.viark");
    expect(findMediaPlayer(hass({}), "remote.viark_remote")).toBeUndefined();
  });

  it("prefers the Viark media player for the stub config", () => {
    expect(findViarkEntity(hass(registry))).toBe("media_player.viark");
    expect(findViarkEntity(hass({}))).toBeUndefined();
  });
});

describe("localize", () => {
  it("falls back to English and substitutes variables", () => {
    expect(localize("es-ES", "status.standby")).toBe("En espera");
    expect(localize("de", "status.standby")).toBe("Standby");
    expect(localize("en", "status.not_found", { entity: "x.y" })).toBe("Entity not available: x.y");
  });

  it.each(Object.keys(TRANSLATIONS))("labels every button in %s", (lang) => {
    for (const id of BUTTON_IDS) {
      expect(localize(lang, `buttons.${id}`), id).not.toBe(`buttons.${id}`);
    }
  });
});

describe("release metadata", () => {
  it("keeps the card version in step with package.json", () => {
    const pkg = JSON.parse(readFileSync("package.json", "utf8")) as { version: string };
    expect(VERSION).toBe(pkg.version);
  });

  it("points HACS at the built file", () => {
    const hacs = JSON.parse(readFileSync("hacs.json", "utf8")) as { filename: string };
    expect(hacs.filename).toBe("ha-viark-remote-card.js");
  });
});
