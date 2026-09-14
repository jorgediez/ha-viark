/**
 * Minimal subset of the Home Assistant frontend types this card relies on.
 * Defined locally so the card does not depend on the unmaintained
 * `custom-card-helpers` package.
 */

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

export interface EntityRegistryDisplayEntry {
  entity_id: string;
  device_id?: string;
  platform?: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  entities?: Record<string, EntityRegistryDisplayEntry>;
  language?: string;
  locale?: { language: string };
  callService(
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>,
    target?: Record<string, unknown>,
  ): Promise<unknown>;
}

/**
 * Per-button override. Exactly one of `key`, `perform_action` or `action` is set.
 */
export interface ButtonOverride {
  /** A key alias understood by the integration ("epg") or a raw key code (44). */
  key?: string | number;
  /** Any Home Assistant action, e.g. "script.watch_news". */
  perform_action?: string;
  data?: Record<string, unknown>;
  target?: Record<string, unknown>;
  /** Disable the button. */
  action?: "none";
}

export interface ViarkRemoteCardConfig {
  type: string;
  entity: string;
  name?: string;
  show_name?: boolean;
  show_status?: boolean;
  haptics?: boolean;
  buttons?: Record<string, ButtonOverride>;
}

export interface ServiceCall {
  domain: string;
  service: string;
  data?: Record<string, unknown>;
  target?: Record<string, unknown>;
}

declare global {
  interface Window {
    customCards?: Array<{
      type: string;
      name: string;
      description: string;
      preview?: boolean;
      documentationURL?: string;
    }>;
    loadCardHelpers?: () => Promise<{
      createCardElement(config: Record<string, unknown>): Promise<HTMLElement>;
    }>;
  }
}
