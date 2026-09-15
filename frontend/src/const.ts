export const VERSION = "1.1.1";

export const CARD_TYPE = "viark-remote-card";
export const EDITOR_TYPE = "viark-remote-card-editor";

/** Integration domain of https://github.com/jorgediez/ha-viark. */
export const VIARK_DOMAIN = "viark";

/** How long a repeatable button must be held before it starts auto-repeating. */
export const HOLD_DELAY_MS = 500;

/**
 * Gap between repeated key presses. Matches the integration's own KEY_INTERVAL:
 * the receiver drops keys sent back to back without a gap.
 */
export const REPEAT_INTERVAL_MS = 450;

/** Printed at the bottom of the remote unless `name` is set. */
export const DEFAULT_NAME = "VIARK";

export const DEFAULTS = {
  show_name: true,
  show_status: true,
  haptics: true,
} as const;
