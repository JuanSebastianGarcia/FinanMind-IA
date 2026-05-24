# Finanmind

Aplicación de escritorio para el manejo de finanzas personales. Permite registrar ingresos, controlar gastos con tarjeta de crédito, gestionar inversiones y obtener análisis con inteligencia artificial.

---

## ¿Qué puedes hacer con Finanmind?

| Módulo | ¿Para qué sirve? |
|---|---|
| **Presupuesto** | Define tu salario y distribúyelo en categorías y etiquetas de gasto. |
| **Distribución** | Registra cuánto dinero real recibiste cada mes y cómo lo asignaste. |
| **Tarjetas de crédito** | Lleva el control de tus tarjetas: gastos por ciclo, cuotas, pagos y límite disponible. Soporta compras en múltiples cuotas con distribución automática mes a mes. |
| **Inversiones** | Registra tus activos en COP y USD con seguimiento de portafolio. |
| **Dashboard** | Vista general del mes: ingresos, saldo, deuda en tarjetas e inversiones. |
| **Análisis con IA** | Conecta OpenAI o Mistral para recibir recomendaciones sobre tu presupuesto e inversiones basadas en reglas personalizables. |

---

## Instalación (Windows)

### Opción A — Ejecutable listo para usar

1. Descarga la carpeta `instalador/Finanmind/` o el archivo `Finanmind.zip`.
2. Extrae el contenido y ejecuta `Finanmind.exe`.
3. La primera vez te pedirá seleccionar una carpeta donde guardar tus datos.

No requiere instalar Python ni ninguna dependencia.

### Opción B — Desde el código fuente

**Requisitos:** Python 3.11, 3.12 o 3.13.

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la aplicación
python main.py
```

---

## Primer uso

1. Al abrir la aplicación por primera vez, selecciona la carpeta donde se guardarán tus datos (puede ser cualquier carpeta vacía en tu equipo).
2. Ve al módulo **Presupuesto** y registra tu salario mensual.
3. Crea categorías de gasto (por ejemplo: Vivienda, Alimentación, Transporte) y asígnales un monto.
4. Agrega tus tarjetas de crédito en el módulo **Tarjetas**.
5. Usa el **Dashboard** para ver el resumen financiero del mes.

---

## Análisis con IA (opcional)

Para activar el análisis de presupuesto o inversiones con IA:

1. Abre el módulo correspondiente y busca el botón de análisis.
2. Selecciona el proveedor: **OpenAI** o **Mistral**.
3. Ingresa tu API key cuando se solicite (se guarda localmente en tu carpeta de datos).

---

## Datos y privacidad

Toda la información se guarda en archivos CSV dentro de la carpeta que elegiste al inicio. No se envía ningún dato a servidores externos, excepto el texto que se envía al modelo de IA cuando usas esa función de forma explícita.
