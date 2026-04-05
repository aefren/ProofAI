# ProofAI

This NVDA add-on proofreads the text selected in an edit field using an OpenAI-compatible API.

## Usage

1. Open NVDA.
2. Go to Preferences > Settings > ProofAI.
3. Fill in the API key, endpoint URL, and model.
4. Move focus to an edit field and select the text to proofread.
5. Press `NVDA+Shift+X`.
6. The add-on will replace the selection with the improved text.

## Default values

- Endpoint: `https://api.openai.com/v1/chat/completions`
- Model: `gpt-4.1-mini`

## Notes

- The add-on sends only the selected text to the configured API.
- It can also work with OpenAI-compatible services such as OpenRouter or compatible local servers.
- The gesture can be changed in NVDA under Preferences > Input gestures.
