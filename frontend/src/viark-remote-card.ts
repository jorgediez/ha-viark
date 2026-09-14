import { LitElement, html, nothing, svg, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { resolveAction, validateConfig } from "./actions";
import { BUTTONS, isButtonId, type ButtonId } from "./buttons";
import {
  CARD_TYPE,
  DEFAULT_NAME,
  DEFAULTS,
  EDITOR_TYPE,
  HOLD_DELAY_MS,
  REPEAT_INTERVAL_MS,
  VERSION,
} from "./const";
import { findMediaPlayer, findViarkEntity } from "./entities";
import { localize } from "./localize";
import { styles } from "./styles";
import type { HassEntity, HomeAssistant, ViarkRemoteCardConfig } from "./types";
import "./editor";

type PowerState = "on" | "standby" | "unavailable" | "unknown";
type HapticType = "light" | "warning" | "failure";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export class ViarkRemoteCard extends LitElement {
  static styles = styles;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: ViarkRemoteCardConfig;

  private _holdTimer?: ReturnType<typeof setTimeout>;
  private _holdToken = 0;
  private _holdFired = false;

  public static getConfigElement(): HTMLElement {
    return document.createElement(EDITOR_TYPE);
  }

  public static getStubConfig(hass: HomeAssistant): Omit<ViarkRemoteCardConfig, "type"> {
    return { entity: findViarkEntity(hass) ?? "media_player.viark_receiver" };
  }

  public setConfig(config: ViarkRemoteCardConfig): void {
    validateConfig(config);
    this._config = config;
  }

  public getCardSize(): number {
    return 16;
  }

  public getGridOptions() {
    return { columns: 6, min_columns: 4 };
  }

  public disconnectedCallback(): void {
    super.disconnectedCallback();
    this._cancelHold();
  }

  private get _lang(): string | undefined {
    return this.hass?.locale?.language ?? this.hass?.language;
  }

  private get _playerId(): string | undefined {
    return this.hass && this._config ? findMediaPlayer(this.hass, this._config.entity) : undefined;
  }

  private _option<K extends keyof typeof DEFAULTS>(name: K): boolean {
    return this._config?.[name] ?? DEFAULTS[name];
  }

  /** Re-render only when an entity this card displays has changed. */
  protected shouldUpdate(changed: PropertyValues<this>): boolean {
    if (!this._config) {
      return false;
    }
    if (changed.has("_config" as keyof ViarkRemoteCard)) {
      return true;
    }
    const oldHass = changed.get("hass") as HomeAssistant | undefined;
    if (!oldHass || !this.hass) {
      return true;
    }
    if (
      oldHass.language !== this.hass.language ||
      oldHass.locale?.language !== this.hass.locale?.language ||
      oldHass.entities !== this.hass.entities
    ) {
      return true;
    }
    return [this._config.entity, this._playerId].some(
      (id) => id !== undefined && oldHass.states[id] !== this.hass!.states[id],
    );
  }

  private _powerState(entity: HassEntity, player?: HassEntity): PowerState {
    const states = [entity.state, player?.state];
    if (states.includes("unavailable")) {
      return "unavailable";
    }
    const state = player?.state ?? entity.state;
    if (state === "off" || state === "standby") {
      return "standby";
    }
    return state === "unknown" ? "unknown" : "on";
  }

  private _statusText(power: PowerState, player?: HassEntity): string {
    if (power !== "on") {
      return power === "unknown" ? "" : localize(this._lang, `status.${power}`);
    }
    const channel = player?.attributes.media_channel;
    const title = player?.attributes.media_title;
    const parts = [channel, title].filter((part) => part !== undefined && part !== null && part !== "");
    return parts.length ? parts.join("  ") : localize(this._lang, "status.on");
  }

  protected render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) {
      return nothing;
    }
    const entity = this.hass.states[this._config.entity];
    if (!entity) {
      return html`<ha-card>
        <div class="warning">
          ${localize(this._lang, "status.not_found", { entity: this._config.entity })}
        </div>
      </ha-card>`;
    }

    const playerId = this._playerId;
    const player = playerId ? this.hass.states[playerId] : undefined;
    const power = this._powerState(entity, player);
    const disabled = power === "unavailable";
    const name = this._config.name ?? DEFAULT_NAME;
    const deviceName =
      this._config.name ??
      (player?.attributes.friendly_name as string | undefined) ??
      (entity.attributes.friendly_name as string | undefined) ??
      name;

    const key = (id: ButtonId, className = "key") => this._renderKey(id, className, disabled);

    return html`
      <ha-card>
        <div class="frame">
          <div class="remote" role="group" aria-label=${deviceName}>
            <div class="cap">
              <span class="led ${power}"></span>
              ${this._option("show_status")
                ? html`<span class="status" aria-live="polite">${this._statusText(power, player)}</span>`
                : nothing}
            </div>

            <div class="row">${key("power", "key round power")} ${key("mute", "key round mute")}</div>

            <div class="grid four pills">${(["resol", "txt", "audio", "subt"] as const).map((id) => key(id))}</div>

            <div class="grid numpad">
              ${(
                [
                  "digit_1",
                  "digit_2",
                  "digit_3",
                  "digit_4",
                  "digit_5",
                  "digit_6",
                  "digit_7",
                  "digit_8",
                  "digit_9",
                  "chevron_left",
                  "digit_0",
                  "chevron_right",
                ] as const
              ).map((id) => key(id))}
            </div>

            <div class="rockers">
              <div class="rocker vol">${key("vol_up")}${key("vol_down")}</div>
              ${key("fav", "key middle")}
              <div class="rocker ch">${key("ch_up")}${key("ch_down")}</div>
              ${key("epg", "key middle")}
            </div>

            <div class="dpad">
              <div class="ring">
                ${key("up", "wedge up")} ${key("down", "wedge down")} ${key("left", "wedge left")}
                ${key("right", "wedge right")}
              </div>
              ${key("ok", "key ok")} ${key("info", "key corner info")} ${key("menu", "key corner menu")}
              ${key("recall", "key corner recall")} ${key("exit", "key corner exit")}
            </div>

            <div class="grid four colors">
              ${(["red", "green", "yellow", "blue"] as const).map((id) => key(id, `key color ${id}`))}
            </div>

            <div class="panel">
              <div class="grid four">
                ${(
                  [
                    "f1",
                    "f2",
                    "media",
                    "update",
                    "rewind",
                    "play",
                    "pause",
                    "fast_forward",
                    "timer",
                    "record",
                    "stop",
                    "tv_radio",
                  ] as const
                ).map((id) => key(id, `key ${id}`))}
              </div>
            </div>

            ${this._option("show_name") ? html`<div class="name">${name}</div>` : nothing}
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderKey(id: ButtonId, className: string, disabled: boolean): TemplateResult {
    const def = BUTTONS[id];
    const label = localize(this._lang, `buttons.${id}`);
    const face = def.icon
      ? html`<svg viewBox="0 0 24 24" aria-hidden="true">${svg`<path d=${def.icon}></path>`}</svg>`
      : (def.label ?? "").split("\n").map((line) => html`<span>${line}</span>`);

    return html`<button
      type="button"
      class=${className}
      data-button=${id}
      title=${label}
      aria-label=${label}
      ?disabled=${disabled}
      @click=${this._onClick}
      @pointerdown=${this._onPointerDown}
      @pointerup=${this._cancelHold}
      @pointerleave=${this._cancelHold}
      @pointercancel=${this._cancelHold}
      @contextmenu=${this._onContextMenu}
    >
      ${face}
    </button>`;
  }

  private _buttonId(ev: Event): ButtonId | undefined {
    const id = (ev.currentTarget as HTMLElement | null)?.dataset.button;
    return id && isButtonId(id) ? id : undefined;
  }

  private _onClick(ev: MouseEvent): void {
    const id = this._buttonId(ev);
    if (!id) {
      return;
    }
    // A hold already sent the key; the click that ends it must not send it again.
    // Keyboard activation (detail 0) never goes through a hold.
    if (this._holdFired && ev.detail !== 0) {
      this._holdFired = false;
      return;
    }
    void this._press(id);
  }

  /**
   * Repeatable buttons start auto-repeating after HOLD_DELAY_MS. Nothing is sent
   * on pointerdown itself, so scrolling the dashboard over the card never presses
   * a key: the browser cancels the pointer before the hold delay elapses.
   */
  private _onPointerDown(ev: PointerEvent): void {
    const id = this._buttonId(ev);
    this._cancelHold();
    this._holdFired = false;
    if (!id || !BUTTONS[id].repeat || ev.button !== 0) {
      return;
    }
    const token = this._holdToken;
    this._holdTimer = setTimeout(() => {
      this._holdFired = true;
      void this._repeat(id, token);
    }, HOLD_DELAY_MS);
  }

  private _onContextMenu(ev: Event): void {
    const id = this._buttonId(ev);
    if (id && BUTTONS[id].repeat) {
      ev.preventDefault();
    }
  }

  private async _repeat(id: ButtonId, token: number): Promise<void> {
    while (token === this._holdToken && this.isConnected) {
      if (!(await this._press(id))) {
        return;
      }
      await sleep(REPEAT_INTERVAL_MS);
    }
  }

  private _cancelHold(): void {
    clearTimeout(this._holdTimer);
    this._holdTimer = undefined;
    this._holdToken++;
  }

  /** Performs the button's action. Resolves to false when nothing was sent. */
  private async _press(id: ButtonId): Promise<boolean> {
    if (!this.hass || !this._config) {
      return false;
    }
    const action = resolveAction(id, this._config);
    if (action.type === "none") {
      return false;
    }
    if (action.type === "unsupported") {
      this._haptic("warning");
      this._fire("hass-notification", {
        message: localize(this._lang, "toast.unsupported", {
          button: localize(this._lang, `buttons.${id}`),
        }),
      });
      return false;
    }

    this._haptic("light");
    const { domain, service, data, target } = action.call;
    try {
      // Home Assistant reports failed actions to the user itself.
      await this.hass.callService(domain, service, data, target);
      return true;
    } catch (err) {
      this._haptic("failure");
      console.debug(`${CARD_TYPE}: ${domain}.${service} failed`, err);
      return false;
    }
  }

  private _haptic(type: HapticType): void {
    if (this._option("haptics")) {
      this._fire("haptic", type);
    }
  }

  private _fire(type: string, detail: unknown): void {
    this.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, ViarkRemoteCard);

  window.customCards = window.customCards ?? [];
  window.customCards.push({
    type: CARD_TYPE,
    name: localize(navigator.language, "card.name"),
    description: localize(navigator.language, "card.description"),
    preview: true,
    documentationURL: "https://github.com/jorgediez/ha-viark-remote-card",
  });

  console.info(
    `%c VIARK-REMOTE-CARD %c v${VERSION} `,
    "color: #fff; background: #1e1f22; font-weight: 700;",
    "color: #1e1f22; background: #c5d3e1; font-weight: 700;",
  );
}
