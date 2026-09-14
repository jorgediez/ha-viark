import { css } from "lit";

/*
 * Every size inside the remote is expressed in `cqi` (1% of the frame width), so
 * the replica keeps its proportions at any card width.
 */
export const styles = css`
  :host {
    display: block;
  }

  ha-card {
    height: 100%;
    box-sizing: border-box;
    padding: 16px;
    display: flex;
    justify-content: center;
  }

  .warning {
    padding: 8px;
    color: var(--error-color, #db4437);
  }

  .frame {
    container-type: inline-size;
    width: min(100%, var(--viark-remote-width, 280px));
  }

  .remote {
    --key-top: #3c3e43;
    --key-bottom: #25272b;
    --key-text: #ededed;
    --key-shadow: #09090a;
    --gap-color: #17181b;

    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 5cqi;
    padding: 0 7cqi 6cqi;
    border-radius: 16cqi 16cqi 14cqi 14cqi;
    background: linear-gradient(
      90deg,
      #101113 0%,
      #27292d 5%,
      #1e1f22 50%,
      #27292d 95%,
      #101113 100%
    );
    box-shadow:
      0 2cqi 5cqi rgba(0, 0, 0, 0.45),
      inset 0 0 0 0.5cqi #0b0c0d;
    color: var(--key-text);
    font-family: "Roboto Condensed", "Arial Narrow", Roboto, system-ui, sans-serif;
    font-weight: 600;
    user-select: none;
    -webkit-user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  /* Glossy IR window, doubling as the status display. */
  .cap {
    box-sizing: border-box;
    height: 14cqi;
    margin-inline: -7cqi;
    padding-inline: 10cqi;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2.5cqi;
    border-radius: 16cqi 16cqi 4cqi 4cqi;
    border-bottom: 0.6cqi solid #07070a;
    background: linear-gradient(#2b2c30, #0c0c0e 70%);
    overflow: hidden;
  }

  .led {
    flex: none;
    width: 2.6cqi;
    height: 2.6cqi;
    border-radius: 50%;
    background: #4a4a4a;
  }
  .led.on {
    background: #5bd46a;
    box-shadow: 0 0 2cqi #5bd46a;
  }
  .led.standby {
    background: #d8433b;
    box-shadow: 0 0 1.6cqi rgba(216, 67, 59, 0.7);
  }

  .status {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: #9fb4c8;
    font-size: 4cqi;
    font-weight: 500;
    letter-spacing: 0.02em;
  }

  /* ---- Keys ---------------------------------------------------------------- */

  .key {
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 0;
    margin: 0;
    padding: 0;
    border: none;
    border-radius: 3cqi;
    background: linear-gradient(var(--key-top), var(--key-bottom));
    box-shadow:
      0 0.9cqi 0 var(--key-shadow),
      inset 0 0.35cqi 0 rgba(255, 255, 255, 0.09);
    color: var(--key-text);
    font: inherit;
    font-size: 3.6cqi;
    line-height: 1.05;
    letter-spacing: 0.02em;
    cursor: pointer;
    touch-action: manipulation;
    -webkit-touch-callout: none;
    transition:
      transform 60ms ease,
      box-shadow 60ms ease,
      filter 120ms ease;
  }
  .key:active:not(:disabled) {
    transform: translateY(0.7cqi);
    box-shadow:
      0 0.2cqi 0 var(--key-shadow),
      inset 0 0.35cqi 0 rgba(255, 255, 255, 0.05);
    filter: brightness(1.3);
  }
  .key:focus-visible {
    outline: 0.8cqi solid var(--primary-color, #03a9f4);
    outline-offset: 0.6cqi;
  }
  .key:disabled {
    cursor: default;
    opacity: 0.45;
  }
  .key svg {
    width: 1em;
    height: 1em;
    fill: currentColor;
  }

  .row {
    display: flex;
    justify-content: space-between;
    padding-inline: 1cqi;
  }

  .grid {
    display: grid;
  }
  .four {
    grid-template-columns: repeat(4, 1fr);
    gap: 3cqi 4cqi;
  }

  .round {
    width: 14cqi;
    height: 14cqi;
    border-radius: 50%;
    font-size: 7cqi;
  }
  .power {
    background: radial-gradient(circle at 40% 35%, #ff6c73, #e23542 60%, #b0222c);
    box-shadow:
      0 0.9cqi 0 #4f0e14,
      inset 0 0.35cqi 0 rgba(255, 255, 255, 0.2);
    color: #fff;
  }
  .mute {
    background: radial-gradient(circle at 40% 35%, #4b4d53, #26282c 70%);
  }

  .pills .key {
    height: 8.5cqi;
    border-radius: 3.5cqi;
    font-size: 3.1cqi;
  }

  .numpad {
    grid-template-columns: repeat(3, 1fr);
    gap: 3.2cqi 7cqi;
    padding-inline: 1.5cqi;
  }
  .numpad .key {
    height: 8.5cqi;
    font-size: 5.2cqi;
  }

  /* ---- Volume / channel rockers ------------------------------------------- */

  .rockers {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 13cqi);
    gap: 3cqi 7cqi;
    padding-inline: 1.5cqi;
    justify-items: center;
    align-items: center;
  }
  .rocker {
    grid-row: 1 / span 2;
    align-self: stretch;
    width: 82%;
    display: flex;
    flex-direction: column;
    border-radius: 3cqi;
    box-shadow: 0 0.9cqi 0 var(--key-shadow);
    overflow: hidden;
  }
  .rocker.vol {
    grid-column: 1;
  }
  .rocker.ch {
    grid-column: 3;
  }
  .rocker .key {
    flex: 1;
    border-radius: 0;
    box-shadow: inset 0 0.35cqi 0 rgba(255, 255, 255, 0.09);
    font-size: 4cqi;
    line-height: 1.15;
  }
  .rocker .key + .key {
    border-top: 0.5cqi solid #141517;
  }
  .rocker .key:active:not(:disabled) {
    transform: none;
  }
  .middle {
    grid-column: 2;
    width: 72%;
    height: 11.5cqi;
    font-size: 3.8cqi;
  }

  /* ---- Navigation pad ------------------------------------------------------ */

  .dpad {
    position: relative;
    height: 78cqi;
  }
  .ring {
    position: absolute;
    top: calc(50% - 33cqi);
    left: calc(50% - 33cqi);
    width: 66cqi;
    height: 66cqi;
    border-radius: 50%;
    overflow: hidden;
    background: radial-gradient(circle, #303236 0%, #26282c 70%, #1c1d20 100%);
    box-shadow:
      0 1cqi 0 var(--key-shadow),
      inset 0 0.4cqi 0 rgba(255, 255, 255, 0.08);
  }
  .wedge {
    position: absolute;
    inset: 0;
    display: flex;
    margin: 0;
    padding: 0;
    border: none;
    background: transparent;
    color: #e8e8e8;
    font-size: 22cqi;
    cursor: pointer;
    touch-action: manipulation;
    -webkit-touch-callout: none;
    transition: background-color 80ms ease;
  }
  .wedge svg {
    width: 1em;
    height: 1em;
    fill: currentColor;
  }
  .wedge.up {
    clip-path: polygon(0 0, 100% 0, 50% 50%);
    justify-content: center;
    align-items: flex-start;
    padding-top: 0;
  }
  .wedge.down {
    clip-path: polygon(0 100%, 100% 100%, 50% 50%);
    justify-content: center;
    align-items: flex-end;
    padding-bottom: 0;
  }
  .wedge.left {
    clip-path: polygon(0 0, 0 100%, 50% 50%);
    align-items: center;
    justify-content: flex-start;
    padding-left: 0;
  }
  .wedge.right {
    clip-path: polygon(100% 0, 100% 100%, 50% 50%);
    align-items: center;
    justify-content: flex-end;
    padding-right: 0;
  }
  .wedge:active:not(:disabled) {
    background-color: rgba(255, 255, 255, 0.1);
  }
  .wedge:focus-visible {
    outline: none;
    background-color: rgba(3, 169, 244, 0.3);
  }
  .wedge:disabled {
    cursor: default;
    opacity: 0.45;
  }

  .ok,
  .corner {
    position: absolute;
    border: 1.4cqi solid var(--gap-color);
    border-radius: 50%;
    background-clip: padding-box;
  }
  .ok {
    top: calc(50% - 12cqi);
    left: calc(50% - 12cqi);
    width: 24cqi;
    height: 24cqi;
    font-size: 7.5cqi;
  }
  .corner {
    width: 17cqi;
    height: 17cqi;
    font-size: 3.3cqi;
    letter-spacing: 0;
  }
  .corner.info {
    top: 0.5cqi;
    left: 1cqi;
  }
  .corner.menu {
    top: 0.5cqi;
    right: 1cqi;
  }
  .corner.recall {
    bottom: 1.5cqi;
    left: 1cqi;
  }
  .corner.exit {
    bottom: 1.5cqi;
    right: 1cqi;
  }

  /* ---- Colour keys ---------------------------------------------------------- */

  .colors {
    justify-items: center;
    padding-inline: 1cqi;
  }
  .color {
    width: 11.5cqi;
    height: 10.5cqi;
    border-radius: 2cqi;
  }
  .color.red {
    background: linear-gradient(#ff6d73, #e0414a);
  }
  .color.green {
    background: linear-gradient(#34cc72, #15a150);
  }
  .color.yellow {
    background: linear-gradient(#fff05a, #efd200);
  }
  .color.blue {
    background: linear-gradient(#45adff, #1985db);
  }

  /* ---- Lower media panel ---------------------------------------------------- */

  .panel {
    padding: 4cqi 3cqi;
    border-radius: 5cqi;
    background-color: #141517;
    background-image: radial-gradient(rgba(255, 255, 255, 0.05) 0.25cqi, transparent 0.4cqi);
    background-size: 2cqi 2cqi;
    box-shadow:
      inset 0 0.6cqi 1.5cqi rgba(0, 0, 0, 0.6),
      0 0.3cqi 0 rgba(255, 255, 255, 0.04);
  }
  .panel .four {
    gap: 3.2cqi 3.5cqi;
  }
  .panel .key {
    height: 7.5cqi;
    border-radius: 2.6cqi;
    font-size: 3cqi;
    letter-spacing: 0;
  }
  .panel .key svg {
    font-size: 5cqi;
  }
  .panel .record svg {
    color: #e5262f;
  }

  .name {
    padding-top: 3cqi;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    text-align: center;
    text-transform: uppercase;
    color: #c5d3e1;
    font-size: 6.5cqi;
    font-weight: 700;
    letter-spacing: 0.08em;
  }

  @media (prefers-reduced-motion: reduce) {
    .key,
    .wedge {
      transition: none;
    }
  }
`;
