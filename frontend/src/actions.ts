import { BUTTON_IDS, BUTTONS, isButtonId, type ButtonId } from "./buttons";
import { VIARK_DOMAIN } from "./const";
import type { ButtonOverride, ServiceCall, ViarkRemoteCardConfig } from "./types";

export type ResolvedAction =
  | { type: "call"; call: ServiceCall }
  /** The integration cannot send this button yet. */
  | { type: "unsupported" }
  /** Explicitly disabled by the user. */
  | { type: "none" };

const ENTITY_DOMAINS = ["media_player", "remote"];
const BOOLEAN_OPTIONS = ["show_name", "show_status", "haptics"];
const ACTION_PATTERN = /^[a-z0-9_]+\.[a-z0-9_]+$/;

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export const entityDomain = (entityId: string): string => entityId.split(".", 1)[0];

/** Throws a readable error, shown by Home Assistant in place of the card. */
export function validateConfig(config: unknown): asserts config is ViarkRemoteCardConfig {
  if (!isObject(config)) {
    throw new Error("Invalid configuration.");
  }
  const { entity, name, buttons } = config;

  if (typeof entity !== "string" || !entity) {
    throw new Error("Set 'entity' to the media_player or remote entity of your Viark receiver.");
  }
  if (!ENTITY_DOMAINS.includes(entityDomain(entity))) {
    throw new Error(`'entity' must be a media_player or remote entity, got '${entity}'.`);
  }
  if (name !== undefined && typeof name !== "string") {
    throw new Error("'name' must be text.");
  }
  for (const option of BOOLEAN_OPTIONS) {
    if (config[option] !== undefined && typeof config[option] !== "boolean") {
      throw new Error(`'${option}' must be true or false.`);
    }
  }
  if (buttons === undefined) {
    return;
  }
  if (!isObject(buttons)) {
    throw new Error("'buttons' must be a mapping of button name to override.");
  }
  for (const [id, override] of Object.entries(buttons)) {
    if (!isButtonId(id)) {
      throw new Error(`Unknown button '${id}'. Valid buttons: ${BUTTON_IDS.join(", ")}.`);
    }
    validateOverride(id, override);
  }
}

function validateOverride(id: string, override: unknown): void {
  const where = `buttons.${id}`;
  if (!isObject(override)) {
    throw new Error(`'${where}' must be a mapping.`);
  }
  const kinds = ["key", "perform_action", "action"].filter((k) => override[k] !== undefined);
  if (kinds.length !== 1) {
    throw new Error(`'${where}' needs exactly one of 'key', 'perform_action' or 'action: none'.`);
  }

  const { key, perform_action, action, data, target } = override;
  if (kinds[0] === "key") {
    const validString = typeof key === "string" && key.trim() !== "";
    const validNumber = typeof key === "number" && Number.isInteger(key) && key >= 0;
    if (!validString && !validNumber) {
      throw new Error(`'${where}.key' must be a key name or a non-negative key code.`);
    }
  }
  if (kinds[0] === "perform_action") {
    if (typeof perform_action !== "string" || !ACTION_PATTERN.test(perform_action)) {
      throw new Error(`'${where}.perform_action' must look like 'domain.action'.`);
    }
  } else if (data !== undefined || target !== undefined) {
    throw new Error(`'${where}': 'data' and 'target' only apply to 'perform_action'.`);
  }
  if (kinds[0] === "action" && action !== "none") {
    throw new Error(`'${where}.action' only supports 'none'.`);
  }
  if (data !== undefined && !isObject(data)) {
    throw new Error(`'${where}.data' must be a mapping.`);
  }
  if (target !== undefined && !isObject(target)) {
    throw new Error(`'${where}.target' must be a mapping.`);
  }
}

/**
 * Builds the action that sends one remote key, using whichever entity the card is
 * bound to. Both routes resolve names and raw codes identically in the integration.
 */
export function keyCall(entityId: string, key: string): ServiceCall {
  const target = { entity_id: entityId };
  if (entityDomain(entityId) === "remote") {
    return { domain: "remote", service: "send_command", data: { command: key }, target };
  }
  return { domain: VIARK_DOMAIN, service: "send_key", data: { key }, target };
}

export function resolveAction(id: ButtonId, config: ViarkRemoteCardConfig): ResolvedAction {
  const override: ButtonOverride | undefined = config.buttons?.[id];
  if (override) {
    if (override.action === "none") {
      return { type: "none" };
    }
    if (override.perform_action) {
      const [domain, service] = override.perform_action.split(".");
      return {
        type: "call",
        call: { domain, service, data: override.data, target: override.target },
      };
    }
    if (override.key !== undefined) {
      return { type: "call", call: keyCall(config.entity, String(override.key).trim()) };
    }
  }

  const action = BUTTONS[id].action;
  switch (action.type) {
    case "power":
      return {
        type: "call",
        call: {
          domain: entityDomain(config.entity),
          service: "toggle",
          target: { entity_id: config.entity },
        },
      };
    case "key":
      return { type: "call", call: keyCall(config.entity, action.key) };
    case "none":
      return { type: "unsupported" };
  }
}
