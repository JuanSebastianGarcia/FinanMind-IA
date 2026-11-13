export class PaymentsDates {
  /** Small Spanish date helpers shared by the payments views. */
  static MONTHS_SHORT = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  static MONTHS_LONG = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
  ];

  /** ``2026-11-18`` → ``18 nov`` */
  static shortDay(iso) {
    const [, m, d] = String(iso).split("-");
    return `${Number(d)} ${PaymentsDates.MONTHS_SHORT[Number(m) - 1] || ""}`;
  }

  /** ``2026-11-18`` → ``nov`` */
  static shortMonth(iso) {
    return PaymentsDates.MONTHS_SHORT[Number(String(iso).split("-")[1]) - 1] || "";
  }

  /** ``2026-11`` → ``Noviembre 2026`` */
  static monthTitle(ym) {
    const [y, m] = String(ym).split("-");
    const name = PaymentsDates.MONTHS_LONG[Number(m) - 1] || "";
    return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${y}`;
  }

  /** Shift ``yyyy-mm`` by ``delta`` months. */
  static shiftMonth(ym, delta) {
    const [y, m] = String(ym).split("-").map(Number);
    const idx = y * 12 + (m - 1) + delta;
    return `${String(Math.floor(idx / 12)).padStart(4, "0")}-${String((idx % 12) + 1).padStart(2, "0")}`;
  }
}
