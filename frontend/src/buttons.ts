import {
  mdiFastForward,
  mdiMenuDown,
  mdiMenuLeft,
  mdiMenuRight,
  mdiMenuUp,
  mdiPause,
  mdiPlay,
  mdiPower,
  mdiRecord,
  mdiRewind,
  mdiStop,
  mdiVolumeOff,
} from "@mdi/js";

/**
 * What a button does by default.
 *
 * - `key`: a named key from the integration's KEY_ALIASES table, sent through
 *   `viark.send_key` (media_player) or `remote.send_command` (remote).
 * - `power`: the entity's `toggle` action, which uses the receiver's dedicated
 *   power request (1041) and respects soft standby.
 * - `none`: the integration has no verified key for this button yet.
 */
export type ButtonAction =
  | { type: "key"; key: string }
  | { type: "power" }
  | { type: "none" };

export interface ButtonDef {
  /** Printed label; "\n" splits it over two lines. */
  label?: string;
  /** MDI path, used instead of a label. */
  icon?: string;
  action: ButtonAction;
  /** Auto-repeat while held. */
  repeat?: boolean;
}

const key = (name: string): ButtonAction => ({ type: "key", key: name });
const NONE: ButtonAction = { type: "none" };

const defs = {
  power: { icon: mdiPower, action: { type: "power" } },
  mute: { icon: mdiVolumeOff, action: key("mute") },

  resol: { label: "RESOL", action: NONE },
  txt: { label: "TXT", action: key("teletext") },
  audio: { label: "AUDIO", action: NONE },
  subt: { label: "SUBT", action: key("subtitle") },

  digit_1: { label: "1", action: key("digit_1") },
  digit_2: { label: "2", action: key("digit_2") },
  digit_3: { label: "3", action: key("digit_3") },
  digit_4: { label: "4", action: key("digit_4") },
  digit_5: { label: "5", action: key("digit_5") },
  digit_6: { label: "6", action: key("digit_6") },
  digit_7: { label: "7", action: key("digit_7") },
  digit_8: { label: "8", action: key("digit_8") },
  digit_9: { label: "9", action: key("digit_9") },
  chevron_left: { label: "<", action: NONE },
  digit_0: { label: "0", action: key("digit_0") },
  chevron_right: { label: ">", action: NONE },

  vol_up: { label: "VOL\n+", action: key("volume_up"), repeat: true },
  vol_down: { label: "VOL\n−", action: key("volume_down"), repeat: true },
  fav: { label: "FAV", action: key("favourite") },
  epg: { label: "EPG", action: key("epg") },
  ch_up: { label: "CH\n+", action: key("channel_up"), repeat: true },
  ch_down: { label: "CH\n−", action: key("channel_down"), repeat: true },

  info: { label: "INFO", action: key("info") },
  menu: { label: "MENU", action: key("menu") },
  recall: { label: "RECALL", action: key("recall") },
  exit: { label: "EXIT", action: key("exit") },
  up: { icon: mdiMenuUp, action: key("up"), repeat: true },
  down: { icon: mdiMenuDown, action: key("down"), repeat: true },
  left: { icon: mdiMenuLeft, action: key("left"), repeat: true },
  right: { icon: mdiMenuRight, action: key("right"), repeat: true },
  ok: { label: "OK", action: key("ok") },

  red: { action: key("red") },
  green: { action: key("green") },
  yellow: { action: key("yellow") },
  blue: { action: key("blue") },

  f1: { label: "F1", action: NONE },
  f2: { label: "F2", action: NONE },
  // The integration's "usb" key opens the receiver's media player, which is what
  // this remote labels MEDIA.
  media: { label: "MEDIA", action: key("usb") },
  update: { label: "UPDATE", action: NONE },

  rewind: { icon: mdiRewind, action: key("rewind") },
  play: { icon: mdiPlay, action: key("play") },
  pause: { icon: mdiPause, action: key("pause") },
  fast_forward: { icon: mdiFastForward, action: key("fast_forward") },

  timer: { label: "TIMER", action: NONE },
  record: { icon: mdiRecord, action: key("record") },
  stop: { icon: mdiStop, action: key("stop") },
  tv_radio: { label: "TV/R", action: key("tv_radio") },
} satisfies Record<string, ButtonDef>;

export type ButtonId = keyof typeof defs;

export const BUTTONS: Readonly<Record<ButtonId, ButtonDef>> = defs;

export const BUTTON_IDS = Object.keys(defs) as ButtonId[];

export const isButtonId = (id: string): id is ButtonId =>
  Object.prototype.hasOwnProperty.call(defs, id);
