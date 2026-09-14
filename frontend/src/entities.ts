import { VIARK_DOMAIN } from "./const";
import type { HomeAssistant } from "./types";

/**
 * The media_player that carries channel and power state for the card's entity.
 * When the card is bound to the remote entity, the media_player is found through
 * the shared device.
 */
export function findMediaPlayer(hass: HomeAssistant, entityId: string): string | undefined {
  if (entityId.startsWith("media_player.")) {
    return entityId;
  }
  const entities = hass.entities ?? {};
  const deviceId = entities[entityId]?.device_id;
  if (!deviceId) {
    return undefined;
  }
  return Object.values(entities).find(
    (entry) => entry.device_id === deviceId && entry.entity_id.startsWith("media_player."),
  )?.entity_id;
}

/** First Viark entity, preferring the media_player; used for the card picker preview. */
export function findViarkEntity(hass: HomeAssistant): string | undefined {
  const viark = Object.values(hass.entities ?? {}).filter((e) => e.platform === VIARK_DOMAIN);
  return (
    viark.find((e) => e.entity_id.startsWith("media_player.")) ??
    viark.find((e) => e.entity_id.startsWith("remote."))
  )?.entity_id;
}
