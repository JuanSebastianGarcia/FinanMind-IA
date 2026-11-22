# Ambientes de almacenamiento: CSV en desarrollo, Cloudflare D1 en producción

## Qué ambiente es cuál

`RuntimeEnvironment` (`src/finanmind/storage/runtime_environment.py`) decide el ambiente:

| Cómo se ejecuta | Ambiente | Datos de dominio |
|---|---|---|
| `python main.py` / `python -m finanmind` | desarrollo | CSV en la carpeta de trabajo |
| `Finanmind.exe` (PyInstaller, `sys.frozen`) | producción | Cloudflare D1 |

`FINANMIND_ENV=production|development` fuerza un ambiente. Sirve, por ejemplo, para probar D1 desde el código fuente sin compilar. En desarrollo el título de la ventana es "Finanmind (desarrollo)".

"Datos de dominio" son presupuesto, tarjetas (con categorías, gastos y pagos), distribución del ingreso, inversiones, pagos recurrentes, categorías aprendidas de NU y terminaciones de tarjeta de Telegram. Todo lo demás sigue en la carpeta de trabajo en ambos ambientes: API keys, tasa USD/COP, sesión y cola de Telegram, tokens de Google Calendar, claves de Gmail y del PDF de NU, y reglas de la revisión IA.

## Cómo se elige el backend

Cada factory (`BudgetRepositoryFactory`, `CreditCardRepositoryFactory`, `InvestmentRepositoryFactory`, `MonthlyDistributionRepositoryFactory`, `RecurringPaymentRepositoryFactory`) devuelve el repositorio D1 cuando `RuntimeEnvironment.uses_cloud_storage()` y el CSV en otro caso. Los dos repositorios tienen el mismo contrato (`load_all` / `save_all`, o `load_workspace` / `save_workspace` en presupuesto), así que los servicios y bridges no cambian. `factory.csv_repository()` devuelve siempre el CSV, y lo usa el importador.

`KnownExpenseCategoryStore` y `TelegramCardTerminationStore` tienen una rama D1 interna con la misma API.

## Capa D1 (`src/finanmind/storage/`)

- `d1_client.py`: cliente REST de D1 con solo stdlib (`urllib`). Envía cada operación como un `batch`, que D1 aplica de forma atómica: si una sentencia falla, no se aplica ninguna. Reintenta una vez ante errores de red o 5xx, lo cual es seguro porque las escrituras son upserts y deletes idempotentes. Los errores salen como `D1Error` con mensaje en español. `D1ClientProvider.shared()` mantiene un cliente por proceso.
- `d1_table_sync.py`: convierte "la tabla debe quedar con estas filas" en upserts y deletes contra el último snapshot leído o escrito, así que solo viajan las filas que cambiaron. Usa `INSERT ... ON CONFLICT DO UPDATE` (nunca `INSERT OR REPLACE`, que dispararía los `ON DELETE CASCADE`). Escribe los padres antes que los hijos, ejecuta los deletes en orden inverso y verifica las claves foráneas al final (`PRAGMA defer_foreign_keys`).
  - `soft_refs`: referencias opcionales a otro repositorio (por ejemplo, de categoría de tarjeta a etiqueta). Se escriben con un sub-select, así que si el destino ya no existe queda NULL en vez de fallar.
  - `required_refs`: si el destino no existe, la fila se omite.
- `d1_credentials.py`: dónde están las credenciales (ver abajo).

En D1 una referencia vacía es `NULL`, y en los modelos sigue siendo `""`.

## Credenciales

- Producción lee `%LOCALAPPDATA%\Finanmind\cloudflare_d1.json`. Ese archivo está fuera del .exe y de la carpeta de trabajo, y su token está cifrado con DPAPI (solo lo descifra el mismo usuario de Windows).
- `instalador/installer_builder.py` escribe ese archivo al terminar el build, a partir de `cloudflare.env` en la raíz del repo, que git ignora. Si falta, el build avisa, y el .exe mostrará el error al arrancar.
- Desde el código fuente también se aceptan las variables `CLOUDFLARE_*` o el propio `cloudflare.env`.

## Arranque en producción

`WebApplication._build_api_or_report()` carga todos los servicios antes de abrir la ventana. Si falla (sin internet, credenciales vencidas), muestra un cuadro de Windows con el motivo y las opciones Reintentar o Cancelar, y guarda el detalle en `%LOCALAPPDATA%\Finanmind\startup_error.log`. Con Cancelar no se abre la ventana, así que nunca se muestran datos vacíos que luego se puedan guardar encima de los reales. Los errores al guardar, ya dentro de la app, llegan al JS como promesas rechazadas, igual que los errores de CSV.

## Efectos externos desactivados en desarrollo

Desarrollo y producción comparten la carpeta de trabajo. Por eso, en desarrollo están apagados por defecto (`ExternalSyncPolicy`, en `services/external_sync_policy.py`):

- **Lector de compras de Telegram.** Consumiría la cola compartida y las compras terminarían en los CSV en vez de en D1. El watcher JS ve el estado `disabled` y deja de consultar.
- **Espejo de Google Calendar.** Crearía eventos duplicados en el calendario real o borraría eventos de producción. En el calendario de pagos aparece la pastilla "Google Calendar · Desactivado en desarrollo".

`FINANMIND_DEV_EXTERNAL_SYNC=1` los vuelve a activar en desarrollo. En ese caso, las dos apps compiten por la misma cola de Telegram.

## Importar los CSV a D1

```bash
cd src
py -3.12 -m finanmind.tools.d1_import --workspace "C:\ruta\a\la\carpeta"            # simulación: solo conteos
py -3.12 -m finanmind.tools.d1_import --workspace "C:\ruta\a\la\carpeta" --yes      # importa
py -3.12 -m finanmind.tools.d1_import --workspace "C:\ruta\a\la\carpeta" --yes --replace
```

Importa en este orden: presupuesto → tarjetas → distribución → inversiones → recurrentes → categorías conocidas → terminaciones. Cada dominio es un batch atómico. Si alguna tabla de D1 ya tiene filas, no escribe nada a menos que se pase `--replace`. Al terminar compara los conteos de los CSV con los de D1.

## Esquema

Los scripts están en `infra/cloudflare-d1/` (ver su README). El esquema replica [data-model.md](data-model.md).
