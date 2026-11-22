# Documentación de Finanmind

Índice de documentación detallada del proyecto. Para el resumen de alto nivel (arquitectura, bootstrap, archivos clave) ver [CLAUDE.md](../CLAUDE.md) en la raíz.

Esta carpeta se mantiene con la skill `document-project`: cada vez que se agrega o cambia una funcionalidad, arquitectura o flujo relevante, se agrega una nota corta aquí.

## architecture/

- [storage-environments.md](architecture/storage-environments.md): CSV en desarrollo y Cloudflare D1 en producción (selección de backend, capa D1, credenciales, importador, efectos externos apagados en desarrollo)
- [data-model.md](architecture/data-model.md): modelo de datos persistido (CSV/JSON en la carpeta de trabajo) con diagrama entidad-relación. Su réplica como esquema en Cloudflare D1 está en [infra/cloudflare-d1/](../infra/cloudflare-d1/README.md)

## features/

- [investment-review-claude-cli.md](features/investment-review-claude-cli.md): análisis IA de inversiones con API key o con Claude Code (CLI)
- [payments-calendar.md](features/payments-calendar.md): calendario de pagos recurrentes (frecuencias, marca de pagado por mes, etiqueta del presupuesto, avisos)

## flows/

_(vacío por ahora — agregar flujos end-to-end aquí, ej. "agregar un gasto en tarjeta de crédito")_
