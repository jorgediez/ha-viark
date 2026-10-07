# Contributing

Thanks for looking. The card is a front end for the
[Viark Satellite Receiver integration](https://github.com/jorgediez/ha-viark): it
draws the remote and sends key names, and the integration talks to the receiver.
Knowing which side a problem is on saves everyone time.

## Reporting a problem

- **The card itself** (layout, buttons, the editor, a button that sends the wrong
  key): open an [issue here](https://github.com/jorgediez/ha-viark-remote-card/issues/new/choose).
  Include the card version (the browser console shows `VIARK-REMOTE-CARD vX.Y.Z`
  when the card loads), the integration version, your card YAML, and the browser
  or companion app.
- **The receiver doesn't react, a key the integration doesn't know, connection
  errors**: these are the integration's, and belong in
  [its issues](https://github.com/jorgediez/ha-viark/issues). Its diagnostics
  download helps there.
- **Questions and ideas**, or showing how you use the card: the
  [community thread](https://community.home-assistant.io/t/custom-card-viark-remote-card-the-receivers-remote-on-your-dashboard/1025251).

## Adding a button's key

A button can only send a key the integration knows by name. When the integration
adds one (to `KEY_ALIASES` in its `const.py`):

1. Update `tests/integration-key-aliases.json`. `node scripts/check-key-aliases.mjs`
   says what changed; it also runs weekly and before every release.
2. Point the button at the new name in `src/buttons.ts`. If it was one of the
   unsupported buttons, update the list in `src/localize.ts` and the test that
   counts them.
3. Update the README's button table, and the minimum integration version under
   Requirements if the card now needs a newer one.

A code that has not been pressed on a real receiver goes into the integration
first, with what it did; the card follows.

## What belongs here

Changes that fit:

- Making the card behave or look more like the physical remote.
- Accessibility, translations, and the visual editor.
- Fixing how the card reacts to what Home Assistant reports.

Changes that belong elsewhere:

- Anything that needs the receiver to do something new: that is the integration.
- Remotes of other receivers: a separate card, so this one can stay a faithful
  replica.

**If a change is more than a small fix, open an issue first.** A short
description of what you want and how you'd do it takes minutes and can save you
days.

## Working on the code

```bash
npm install
npm run lint && npm run format:check && npm run typecheck
npm test
npm run demo        # the card in a browser, with a mocked Home Assistant
```

A pull request is expected to:

- Pass lint, the format check, the type check and the tests. CI runs these and
  the build, and needs a maintainer to approve the first run on a fork.
- Come with tests. Pure logic is tested in Node (`tests/actions.test.ts`); the
  card and editor render in happy-dom against a mocked `hass`
  (`tests/card.test.ts`, `tests/editor.test.ts`).
- Update the README for anything a user sees.
- Explain, in the commit message, why the change is the way it is.

Keep a pull request to one subject. Two unrelated improvements are two pull
requests, and they'll both move faster.

## Style

Prettier (line length 88) and ESLint decide formatting and catch the usual
mistakes. Beyond that, follow the code already here: user-facing text goes
through `localize`, in English and Spanish; and comments say why rather than
what.

## License

Contributions are under the [MIT License](LICENSE), like the rest of the project.
