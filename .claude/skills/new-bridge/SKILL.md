---
name: new-bridge
description: Guia para agregar un nuevo bridge (o metodo a un bridge existente) en ui/web/bridges/ siguiendo el patron del proyecto Finanmind (bridge + builder/resolver/serializer, wiring en JsApi y JS). Usar cuando se necesite exponer nueva funcionalidad de Python a la UI web.
---

# New Bridge

Finanmind conecta Python y la UI web (`webui/`) via bridges expuestos como `window.pywebview.api.*`. Esta skill guia como agregar uno nuevo o extender uno existente de forma consistente con el patron ya usado por los 7 bridges actuales (Budget, Cards, Investment, Distribution, Dashboard, BudgetReview, InvestmentReview).

## Pasos

1. **Ubicar el bridge existente mas parecido** en `src/finanmind/ui/web/bridges/` (ej. si es tabular como Cards, revisar `cards_bridge.py` y sus companions).
2. **Separar responsabilidades en archivos pequenos**, no meter todo en el bridge:
   - `*_bridge.py`: metodos que se exponen a JS, delegan a services y a los builders/resolvers.
   - `*_builder.py`: arma el dict/payload que se serializa a JSON para la UI.
   - `*_resolver.py`: logica de resolucion de datos (ej. calcular ciclos de facturacion).
   - `*_serializer.py`: si hace falta transformar modelos a formatos intermedios.
3. **El bridge nunca accede a CSV directamente** — siempre pasa por `services/` que a su vez usa `repositories/` (via factories, requieren `AppConfig.USER_DATA_ROOT` seteado).
4. **Registrar el bridge** en `src/finanmind/ui/web/web_application.py` (wiring a `JsApi`).
5. **Exponer el metodo en `js_api.py`** si aplica, y llamarlo desde JS via `window.pywebview.api.<metodo>()`.
6. **Frontend**: agregar el modulo JS en la subcarpeta de dominio correspondiente bajo `webui/assets/js/` (budget, cards, investments, distribution, dashboard, core, format).
7. **Documentar**: usar la skill `document-project` para dejar una nota corta en `docs/features/` o `docs/flows/` explicando el nuevo flujo end-to-end.

## Reglas

- No hay tests automatizados en el proyecto — verificar corriendo la app manualmente (`python main.py`).
- Mantener el mismo estilo de separacion de archivos por responsabilidad que ya existe (evita bridges gigantes con toda la logica adentro).
- Escrituras a CSV siempre atomicas (tmp + rename) — eso ya lo maneja el repository, no reimplementar en el bridge.
