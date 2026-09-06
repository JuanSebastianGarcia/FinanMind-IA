---
name: document-project
description: Documenta una funcionalidad, arquitectura o flujo nuevo/modificado del proyecto Finanmind en docs/, y actualiza CLAUDE.md si cambia algo estructural. Usar despues de implementar o modificar una feature, bridge, repositorio, modelo o flujo de UI.
---

# Document Project

Objetivo: que el contexto completo del proyecto Finanmind (arquitectura, features, flujos) quede siempre documentado en `docs/`, de forma simple, para que cualquier sesion futura de Claude Code pueda retomarlo sin tener que re-explorar todo el codigo.

## Cuando usar esta skill

- Despues de agregar o modificar un bridge (`ui/web/bridges/`), servicio, repositorio o modelo.
- Despues de agregar o cambiar un flujo de UI relevante (ej: nueva vista, nueva tabla, nuevo modal).
- Despues de una decision de arquitectura (ej: por que se separo algo en varios archivos, por que se eligio un patron).
- Cuando el usuario pida explicitamente "documenta esto".

## Estructura de docs/

Si `docs/` no existe, crearla con este layout:

```
docs/
  README.md              # indice: que hay documentado y donde
  architecture/          # decisiones y capas (una nota por tema)
  features/              # una nota por funcionalidad de negocio
  flows/                 # flujos end-to-end (ej: "agregar gasto en tarjeta")
```

- `docs/README.md` es solo un indice: una linea por documento, con link relativo y descripcion de una frase. Mantenerlo corto.
- Cada nota individual (`architecture/*.md`, `features/*.md`, `flows/*.md`) debe ser breve (idealmente <60 lineas): que es, donde vive el codigo (rutas de archivo), por que existe si no es obvio, y como se conecta con otras piezas (bridge -> service -> repository -> modelo -> csv).

## Como documentar

1. Identificar el tipo: arquitectura (decision estructural), feature (funcionalidad de negocio visible al usuario) o flow (secuencia de pasos entre capas).
2. Escribir la nota en el archivo correspondiente, en espanol simple, sin relleno. Enfocarse en el "por que" y "donde", no en repetir el codigo linea por linea.
3. Enlazar archivos de codigo relevantes con rutas relativas.
4. Agregar/actualizar la entrada en `docs/README.md`.
5. Si el cambio afecta algo que CLAUDE.md describe (capas, bridges, archivos clave, patrones), actualizar CLAUDE.md tambien — CLAUDE.md es el resumen de alto nivel para Claude Code, `docs/` es el detalle.

## Reglas

- No documentar detalles que cambian seguido (nombres de variables locales, TODOs temporales) — eso se ve en el codigo.
- No duplicar lo que ya esta en CLAUDE.md; si aplica a ambos, la version corta va en CLAUDE.md y el detalle en `docs/`.
- Preferir actualizar una nota existente antes que crear una nueva si el tema ya esta cubierto.
- Idioma: espanol, igual que las convenciones de commit del proyecto (ver git log).
