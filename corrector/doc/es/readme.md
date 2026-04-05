# ProofAI

Este complemento para NVDA revisa el texto seleccionado en un cuadro de edición usando una API compatible con OpenAI.

## Uso

1. Abre NVDA.
2. Ve a Preferencias > Configuración > ProofAI.
3. Indica la clave de API, la URL del endpoint y el modelo.
4. Sitúa el foco en un cuadro de edición y selecciona el texto que quieras revisar.
5. Pulsa `NVDA+Shift+X`.
6. El complemento reemplazará la selección por el texto mejorado.

## Valores por defecto

- Endpoint: `https://api.openai.com/v1/chat/completions`
- Modelo: `gpt-4.1-mini`

## Notas

- El complemento envía solo el texto seleccionado a la API configurada.
- También puede funcionar con servicios compatibles con la API de OpenAI, como OpenRouter o servidores locales compatibles.
- El gesto puede cambiarse desde NVDA en Preferencias > Gestos de entrada.
