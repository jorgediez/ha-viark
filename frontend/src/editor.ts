import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { DEFAULTS, EDITOR_TYPE, VIARK_DOMAIN } from "./const";
import { localize } from "./localize";
import type { HomeAssistant, ViarkRemoteCardConfig } from "./types";

interface SchemaItem {
  name: string;
  type?: string;
  required?: boolean;
  selector?: Record<string, unknown>;
  schema?: SchemaItem[];
}

const SCHEMA: SchemaItem[] = [
  {
    name: "entity",
    required: true,
    selector: {
      entity: {
        filter: [
          { integration: VIARK_DOMAIN, domain: "media_player" },
          { integration: VIARK_DOMAIN, domain: "remote" },
        ],
      },
    },
  },
  { name: "name", selector: { text: {} } },
  {
    name: "",
    type: "grid",
    schema: [
      { name: "show_name", selector: { boolean: {} } },
      { name: "show_status", selector: { boolean: {} } },
      { name: "haptics", selector: { boolean: {} } },
    ],
  },
];

/**
 * `ha-form` is lazy-loaded by the frontend. Loading a built-in card's editor makes
 * sure it is defined before this editor renders.
 */
async function ensureHaForm(): Promise<void> {
  if (customElements.get("ha-form")) {
    return;
  }
  try {
    const helpers = await window.loadCardHelpers?.();
    const card = await helpers?.createCardElement({ type: "button" });
    const ctor = card?.constructor as { getConfigElement?: () => Promise<unknown> } | undefined;
    await ctor?.getConfigElement?.();
  } catch {
    // Older frontends: ha-form is already available inside the card editor dialog.
  }
}

export class ViarkRemoteCardEditor extends LitElement {
  static styles = css`
    .hint {
      margin: 16px 0 0;
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      line-height: 1.4;
    }
  `;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: ViarkRemoteCardConfig;

  public setConfig(config: ViarkRemoteCardConfig): void {
    this._config = config;
  }

  public connectedCallback(): void {
    super.connectedCallback();
    void ensureHaForm().then(() => this.requestUpdate());
  }

  private get _lang(): string | undefined {
    return this.hass?.locale?.language ?? this.hass?.language;
  }

  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) {
      return nothing;
    }
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${{ ...DEFAULTS, ...this._config }}
        .schema=${SCHEMA}
        .computeLabel=${this._computeLabel}
        .computeHelper=${this._computeHelper}
        @value-changed=${this._valueChanged}
      ></ha-form>
      <p class="hint">${localize(this._lang, "editor.buttons_hint")}</p>
    `;
  }

  private _computeLabel = (item: SchemaItem): string => localize(this._lang, `editor.${item.name}`);

  private _computeHelper = (item: SchemaItem): string | undefined =>
    item.name === "name" ? localize(this._lang, "editor.name_helper") : undefined;

  private _valueChanged(ev: CustomEvent<{ value: Record<string, unknown> }>): void {
    ev.stopPropagation();
    const config: Record<string, unknown> = { ...ev.detail.value };
    // Keep the saved YAML minimal: drop options left at their default.
    for (const [option, value] of Object.entries(DEFAULTS)) {
      if (config[option] === value) {
        delete config[option];
      }
    }
    if (!config.name) {
      delete config.name;
    }
    this.dispatchEvent(
      new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }),
    );
  }
}

if (!customElements.get(EDITOR_TYPE)) {
  customElements.define(EDITOR_TYPE, ViarkRemoteCardEditor);
}
