---
name: verify-manually
description: Checklist para verificar manualmente un cambio en Finanmind ya que el proyecto no tiene tests automatizados. Usar antes de dar por terminada una tarea que toco backend (services/repositories/bridges) o frontend (webui).
---

# Verify Manually

Finanmind no tiene tests automatizados (ver CLAUDE.md, seccion "No Tests"). Toda verificacion es manual, corriendo la app.

## Checklist antes de cerrar una tarea

1. Levantar la app: `python main.py` (o `python -m finanmind`) desde la raiz con el venv activo (Python 3.11-3.13).
2. Si el cambio toco un bridge o service: probar el flujo completo desde la UI (no solo leer el codigo) — abrir la vista relevante y ejercitar la accion (crear/editar/eliminar segun aplique).
3. Si el cambio toco CSV/repositorios: verificar que el archivo en `data/` se escribio correctamente y no quedo un `.tmp` huerfano (las escrituras son atomicas: tmp -> rename).
4. Si el cambio toco AI/LLM (BudgetReview o InvestmentReview): confirmar que hay una API key configurada (`data/openai_api_key.txt` o `data/mistral_api_key.txt`) antes de probar, y revisar el proveedor activo en `data/budget_ai_provider.txt`.
5. Probar al menos un caso borde ademas del camino feliz (ej: campo vacio, monto negativo, categoria sin gastos).
6. Si el cambio es solo frontend (JS/CSS), abrir la vista en la app y revisar la consola de devtools de pywebview por errores JS.
7. Si se toco el instalador (`instalador/`), no es necesario reconstruir el .exe salvo que el usuario lo pida explicitamente — es una operacion pesada y genera archivos binarios versionados.

## Reglas

- Nunca reportar una tarea como completa solo porque el codigo "se ve bien" — si el cambio es ejercitable en la app, ejercitarlo.
- Si no se puede correr la app (ej. entorno sin GUI), decirlo explicitamente en vez de asumir que funciona.
