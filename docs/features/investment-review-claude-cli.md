# Análisis IA de inversiones con Claude Code (CLI)

El análisis IA del portafolio puede ejecutarse con dos **motores**, elegidos en el selector "Motor de IA" del diálogo de análisis:

| Motor | Valor | Cómo se autentica |
|-------|-------|-------------------|
| API key (OpenAI / Mistral) | `api` | API key de "Configurar IA" (proveedor compartido con el análisis de presupuesto) |
| Claude Code (CLI) | `claude_cli` | Sesión local de Claude Code, sin API key |

La elección es **solo para inversiones**. El análisis de presupuesto sigue usando siempre la API key.

## Piezas

- `services/investment_ai_engine.py` / `investment_ai_engine_store.py`: el enum y su persistencia en `data/investment_ai_engine.txt` (env `FINANMIND_INVESTMENT_AI_ENGINE`).
- `services/claude_cli_model_store.py`: modelo opcional en `data/claude_cli_model.txt` (env `CLAUDE_CLI_MODEL`). Vacío significa el modelo por defecto de Claude Code. Solo se aceptan alias o ids simples (`sonnet`, `opus`, …).
- `services/claude_cli_locator.py`: busca el ejecutable en este orden: env `FINANMIND_CLAUDE_CLI_PATH`, `PATH`, `%APPDATA%\npm\claude.cmd`, `~/.local/bin/claude.exe`. Si encuentra el shim `claude.cmd` de npm, usa el `claude.exe` nativo que hay detrás para no pasar por `cmd.exe`.
- `services/claude_cli_chat_client.py`: implementa el mismo puerto que `LlmHttpChatClient` (`request_json_completion`). Ejecuta:
  ```
  claude.exe -p --output-format json --tools "" --no-session-persistence
             --disable-slash-commands --strict-mcp-config
             --system-prompt-file <tmp> [--model <m>]
  ```
  El system prompt va en un archivo temporal y el prompt de usuario por stdin. El proceso corre en una carpeta temporal vacía y sin ventana de consola, con un timeout de 300 s. Del sobre JSON se lee `result`: si `is_error` es verdadero se lanza un `LlmChatCompletionError` con un mensaje amigable (sesión, modelo, etc.).
- `InvestmentReviewLlmFactory.build()`: si el motor es `claude_cli`, devuelve este cliente. El prompt, el parser y la UI de resultados no cambian.
- `InvestmentReviewBridge.set_engine(engine, model_id)` está expuesto como `set_investment_review_engine`. `get_setup()` agrega `engine`, `engine_env_locked` y `claude_cli` (`detected`, `path`, `model_id`, `model_env_locked`).

## Notas

- Cada análisis consume del plan o los límites de Claude Code del usuario. Con `sonnet` tarda unos 25 s.
- Si el .exe no encuentra la CLI (PATH distinto), define `FINANMIND_CLAUDE_CLI_PATH`.
