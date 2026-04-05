# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An NVDA screen reader add-on ("Corrector") that corrects selected text in editable fields using an OpenAI-compatible chat completions API. The user selects text, presses NVDA+Shift+X, and the add-on sends the text to the configured LLM endpoint, then replaces the selection with the corrected result.

## Build

```bash
python build_addon.py
```

This produces `dist/Corrector-<version>.nvda-addon` (a ZIP archive). Version and name are read from `corrector/manifest.ini`.

## Architecture

- **`corrector/`** — The NVDA add-on package (gets zipped into the `.nvda-addon` file).
  - `manifest.ini` — Add-on metadata (name, version, NVDA compatibility range).
  - `globalPlugins/corrector/__init__.py` — Main plugin: registers the NVDA global plugin, settings panel (`SettingsDlg`), keyboard gesture, and manages the async correction flow via `CorrectionThread`.
  - `globalPlugins/corrector/client.py` — `OpenAICompatibleClient` — HTTP client using only stdlib (`urllib`) to call any OpenAI-compatible `/v1/chat/completions` endpoint.
  - `globalPlugins/corrector/configspec.py` — NVDA config spec registration and default system prompt.
- **`sample/OpenAI/`** — Reference NVDA add-on used as a starting point (not part of the build).
- **`build_addon.py`** — Packages `corrector/` into a `.nvda-addon` ZIP, excluding `__pycache__` and `.pyc` files.

## Key Constraints

- **Stdlib only in `client.py`**: NVDA add-ons cannot rely on third-party packages; the HTTP client uses `urllib.request` directly.
- **UI language is Spanish**: All user-facing strings and NVDA messages are in Spanish, wrapped with `_()` for translation.
- **Threading model**: Correction runs in a daemon thread (`CorrectionThread`); results are dispatched back to the main thread via `wx.CallAfter`.
- **Text insertion**: Uses `brailleInput.handler.sendChars()` to type the corrected text into the focused control.
- **No tests**: There is no test suite currently.
