# Cloudflare D1

Esquema de Finanmind en Cloudflare D1. Replica el modelo de [docs/architecture/data-model.md](../../docs/architecture/data-model.md) con una tabla por entidad. Solo la app compilada (producción) usa esta base; al ejecutar desde el código fuente se siguen usando los CSV. Ver [docs/architecture/storage-environments.md](../../docs/architecture/storage-environments.md).

## Archivos

Todos ya están aplicados en la base, en este orden:

- `001_schema.sql`: esquema inicial (17 tablas, claves foráneas e índices).
- `002_nullable_references.sql`: `credit_card_expenses.category_id` e `income_distribution_lines.label_id` pasan a aceptar NULL con `ON DELETE SET NULL`. Así coinciden con la app, que deja vacía la categoría de un gasto al borrar la categoría y no limpia las asignaciones al borrar una etiqueta.

## Credenciales

Se leen de `cloudflare.env` en la raíz del repo. Git ignora ese archivo por la regla `*.env`.

```
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_D1_DATABASE_ID=...
CLOUDFLARE_API_TOKEN=...   # permiso Account → D1 → Edit
```

## Aplicar un script

Con la API REST de D1. No necesita `wrangler`:

```bash
set -a && . ./cloudflare.env && set +a
node -e 'process.stdout.write(JSON.stringify({sql: require("fs").readFileSync(process.argv[1], "utf8")}))' infra/cloudflare-d1/001_schema.sql \
  | curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/d1/database/$CLOUDFLARE_D1_DATABASE_ID/query" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" --data @-
```

`001_schema.sql` usa `CREATE TABLE` sin `IF NOT EXISTS`, así que falla si las tablas ya existen. Los cambios futuros van en scripts nuevos (`002_...sql`).

## Diferencias con los CSV

- Cada `record_type` es una tabla propia, y las relaciones son claves foráneas reales que D1 hace cumplir.
- `budget_categories` y `budget_labels` tienen una columna `position`, porque en el CSV el orden de las filas es el orden en pantalla.
- Montos en COP como `INTEGER` (la app ya los redondea). Las inversiones usan `REAL` porque pueden estar en USD con decimales.
- Borrados: al borrar una tarjeta se borran sus categorías, gastos, pagos y archivos auxiliares (`CASCADE`). Una etiqueta usada por una asignación del ingreso no se puede borrar, y las referencias opcionales a una etiqueta quedan en `NULL`.

## Nota sobre credenciales cifradas

`gmail_card_automations.app_password` y `nu_pdf_passwords.password` existen solo para replicar el diagrama. En local se cifran con DPAPI, que solo descifra el mismo usuario de Windows, así que copiar ese texto a la nube no sirve en otro equipo. Guardarlo sin cifrar expondría las claves. Antes de llenarlas hay que decidir otro esquema de cifrado o dejarlas fuera de la nube.
