type Dictionary = { [key: string]: string | Dictionary };

const digits = (): Record<string, string> =>
  Object.fromEntries(Array.from({ length: 10 }, (_, n) => [`digit_${n}`, String(n)]));

const unsupportedList = "RESOL, AUDIO, <, >, F1, F2, UPDATE, TIMER";

const en: Dictionary = {
  card: {
    name: "Viark Remote Card",
    description: "A replica of the Viark satellite receiver remote control.",
  },
  status: {
    on: "On",
    standby: "Standby",
    unavailable: "Unavailable",
    not_found: "Entity not available: {entity}",
  },
  toast: {
    unsupported: "{button} is not supported by the Viark integration yet.",
  },
  editor: {
    entity: "Viark entity (media player or remote)",
    name: "Name",
    name_helper: "Shown at the bottom of the remote. Defaults to VIARK.",
    show_name: "Show name",
    show_status: "Show power and channel",
    haptics: "Haptic feedback",
    buttons_hint: `Buttons without a verified key in the integration (${unsupportedList}) do nothing by default. You can assign each of them a key code or any action in YAML under "buttons:" — see the README.`,
  },
  buttons: {
    power: "Power",
    mute: "Mute",
    resol: "Resolution",
    txt: "Teletext",
    audio: "Audio track",
    subt: "Subtitles",
    ...digits(),
    chevron_left: "Left angle (<)",
    chevron_right: "Right angle (>)",
    vol_up: "Volume up",
    vol_down: "Volume down",
    fav: "Favourites",
    epg: "Programme guide",
    ch_up: "Channel up",
    ch_down: "Channel down",
    info: "Info",
    menu: "Menu",
    recall: "Recall",
    exit: "Exit",
    up: "Up",
    down: "Down",
    left: "Left",
    right: "Right",
    ok: "OK",
    red: "Red",
    green: "Green",
    yellow: "Yellow",
    blue: "Blue",
    f1: "F1",
    f2: "F2",
    media: "Media",
    update: "Update",
    rewind: "Rewind",
    play: "Play",
    pause: "Pause",
    fast_forward: "Fast forward",
    timer: "Timer",
    record: "Record",
    stop: "Stop",
    tv_radio: "TV / Radio",
  },
};

const es: Dictionary = {
  card: {
    name: "Tarjeta mando Viark",
    description: "Una réplica del mando a distancia del receptor de satélite Viark.",
  },
  status: {
    on: "Encendido",
    standby: "En espera",
    unavailable: "No disponible",
    not_found: "Entidad no disponible: {entity}",
  },
  toast: {
    unsupported: "La integración Viark todavía no admite el botón {button}.",
  },
  editor: {
    entity: "Entidad Viark (reproductor multimedia o mando)",
    name: "Nombre",
    name_helper: "Se muestra al pie del mando. Por defecto, VIARK.",
    show_name: "Mostrar nombre",
    show_status: "Mostrar encendido y canal",
    haptics: "Respuesta háptica",
    buttons_hint: `Los botones sin tecla verificada en la integración (${unsupportedList}) no hacen nada por defecto. Puedes asignar a cada uno un código de tecla o cualquier acción en YAML bajo "buttons:" — consulta el README.`,
  },
  buttons: {
    power: "Encendido",
    mute: "Silencio",
    resol: "Resolución",
    txt: "Teletexto",
    audio: "Pista de audio",
    subt: "Subtítulos",
    ...digits(),
    chevron_left: "Ángulo izquierdo (<)",
    chevron_right: "Ángulo derecho (>)",
    vol_up: "Subir volumen",
    vol_down: "Bajar volumen",
    fav: "Favoritos",
    epg: "Guía de programación",
    ch_up: "Canal siguiente",
    ch_down: "Canal anterior",
    info: "Información",
    menu: "Menú",
    recall: "Último canal",
    exit: "Salir",
    up: "Arriba",
    down: "Abajo",
    left: "Izquierda",
    right: "Derecha",
    ok: "Aceptar",
    red: "Rojo",
    green: "Verde",
    yellow: "Amarillo",
    blue: "Azul",
    f1: "F1",
    f2: "F2",
    media: "Multimedia",
    update: "Actualizar",
    rewind: "Retroceso rápido",
    play: "Reproducir",
    pause: "Pausa",
    fast_forward: "Avance rápido",
    timer: "Temporizador",
    record: "Grabar",
    stop: "Detener",
    tv_radio: "TV / Radio",
  },
};

export const TRANSLATIONS: Record<string, Dictionary> = { en, es };

function lookup(dictionary: Dictionary | undefined, path: string): string | undefined {
  let node: string | Dictionary | undefined = dictionary;
  for (const part of path.split(".")) {
    if (typeof node !== "object") {
      return undefined;
    }
    node = node[part];
  }
  return typeof node === "string" ? node : undefined;
}

export function localize(
  language: string | undefined,
  path: string,
  vars: Record<string, string> = {},
): string {
  const lang = (language ?? "en").split("-")[0].toLowerCase();
  const text = lookup(TRANSLATIONS[lang], path) ?? lookup(en, path) ?? path;
  return text.replace(/\{(\w+)\}/g, (match, name: string) => vars[name] ?? match);
}
