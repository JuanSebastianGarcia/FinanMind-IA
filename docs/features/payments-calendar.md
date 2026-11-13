# Calendario de pagos (pagos recurrentes)

Sección del menú lateral "Calendario de pagos". Lleva las facturas que se repiten (arriendo, servicios, seguros), su día de pago, si ya se pagaron cada mes y su aviso.

## Qué hace

- **Pago recurrente:** nombre, día de pago (1–31; el 31 se ajusta al último día del mes) y **frecuencia** (mensual, bimestral, trimestral, semestral o anual) contada desde el **primer mes de cobro**. Un pago solo aparece en los meses en que se cobra.
- **Tipo de valor:**
  - **Constante:** el valor es obligatorio.
  - **Variable:** el valor estimado es opcional. El valor real se registra por mes con "Registrar"; mientras no exista, la pantalla muestra el estimado con `≈` o "Sin valor".
- **Marca de pagado por mes.** Cada mes empieza pendiente. Un pago sin marcar cuya fecha ya pasó se muestra como **Vencido**.
- **Etiqueta del presupuesto:** opcional. El pago toma el color de la categoría de esa etiqueta.
- **Aviso:** "Agregar a Google Calendar", uno o varios avisos (el mismo día, 1 día antes, 3 días antes o 1 semana antes) y la hora del aviso. Con Google conectado, cada pago es un evento que se repite (ver abajo).
- **Pantalla:** 4 indicadores (total del mes, pagado, pendiente y próximo pago), el calendario mensual con la semana empezando el lunes, la lista de próximos pagos y la tabla del mes.
  - "Próximos pagos" muestra lo vencido sin pagar del mes actual más los próximos 15 días.

## Dónde vive

`PaymentsBridge` → `RecurringPaymentService` → `RecurringPaymentRepository` → modelos → `recurring_payments.csv`

- Modelos:
  - [recurring_payment.py](../../src/finanmind/models/recurring_payment.py): la definición del pago.
  - [recurring_payment_month.py](../../src/finanmind/models/recurring_payment_month.py): el estado del mes (`paid_on` y el valor real).
- CSV: [recurring_payment_csv_codec.py](../../src/finanmind/repositories/recurring_payment_csv_codec.py)
  - Una sola tabla con filas `payment` y filas `month`, igual que `monthly_distribution.csv`.
  - Una fila `month` solo existe si hubo pago marcado o valor registrado; si queda vacía, se elimina.
- Lógica de fechas pura: [recurring_payment_schedule.py](../../src/finanmind/services/recurring_payment_schedule.py)
- Operaciones y validaciones: [recurring_payment_service.py](../../src/finanmind/services/recurring_payment_service.py)
- Bridge: [payments_bridge.py](../../src/finanmind/ui/web/bridges/payments_bridge.py)
  - `payments_state_builder.py` arma todo el estado.
  - `payments_row_serializer.py` arma cada fila (estado, color y texto del aviso).
  - `payments_calendar_builder.py` arma las semanas del calendario.
  - `payments_summary_builder.py` calcula los indicadores.
  - `payments_draft_parser.py` convierte los datos que manda JS.
  - Las opciones de etiqueta reutilizan `DistributionLabelOptionsBuilder`.
- Interfaz: [webui/assets/js/payments/](../../src/finanmind/webui/assets/js/payments/)
  - `payments_panel.js` coordina las vistas y abre las ventanas `dialogs/payment_dialog.js` y `dialogs/payment_amount_dialog.js`.
  - Estilos en `webui/assets/css/payments.css`.
- Métodos JS (`window.pywebview.api`):
  - `get_payments_state`
  - `get_payments_label_options`
  - `add_recurring_payment` / `update_recurring_payment` / `delete_recurring_payment`
  - `set_recurring_payment_paid`
  - `record_recurring_payment_amount`

## Google Calendar

- **Conexión** (botón "Conectar Google Calendar"):
  1. Se carga la credencial OAuth tipo **"App de escritorio"** que el usuario crea en Google Cloud. Los pasos están dentro de la misma ventana.
  2. `InstalledAppFlow` abre el navegador para que el usuario autorice.
  3. Permisos pedidos: `calendar.events` y el email.
- **Dónde se guarda:** todo cifrado con DPAPI en la carpeta de trabajo. `google_calendar_client.json` guarda la credencial; `google_calendar_account.json` guarda el token, el email, la zona horaria y los borrados pendientes. Código: [google_calendar_store.py](../../src/finanmind/services/google_calendar_store.py).
- **Un evento repetido por pago** en el calendario principal, armado en [google_calendar_event_builder.py](../../src/finanmind/services/google_calendar_event_builder.py):
  - Evento con hora (no de día completo) a la hora del aviso, el día de pago.
  - Repetición `RRULE FREQ=MONTHLY;INTERVAL=n`. Los días 29 a 31 usan `BYMONTHDAY=28..d;BYSETPOS=-1`, así caen el último día en los meses cortos.
  - Avisos de tipo `popup`, `días × 1440` minutos antes.
- **Sincronización:** [payment_calendar_sync.py](../../src/finanmind/services/payment_calendar_sync.py) es de mejor esfuerzo. Guardar un pago nunca falla por Google: el error vuelve a la pantalla como `calendar_warning`.
  - Al crear o editar un pago, su evento se crea o se reemplaza. Si el evento ya no existe en Google, se recrea.
  - Apagar el aviso borra el evento.
  - Lo que se borra sin conexión queda en `pending_deletes`.
  - "Sincronizar" y "Conectar" envían todos los pagos.
- **Desconectar** revoca el token. Los eventos se quedan en el calendario, pero se olvidan los `google_event_id`.
- Si la app OAuth queda en modo **"Prueba"** en Google Cloud, el permiso vence cada 7 días. Por eso los pasos piden publicarla.
- **Dependencias:** `google-auth` y `google-auth-oauthlib`, sin el cliente de la API de Google. Las llamadas REST pasan por `AuthorizedSession` en [google_calendar_client.py](../../src/finanmind/services/google_calendar_client.py).

## Decisiones

- La marca de pagado es **por mes** y no por pago, para tener historial y que cada mes empiece limpio.
- **Por ahora solo se relaciona con el presupuesto.** Marcar un pago como pagado no descuenta del presupuesto ni carga una tarjeta.
- Si se elimina una etiqueta del presupuesto, el pago queda "Sin enlace" y el `label_id` viejo se ignora al mostrarlo.
