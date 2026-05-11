export class UsdAmountParser {
  /** Mirrors ``UsdAmountParser`` from Python: strip non-digit/non-dot, one dot max. */
  static parse(raw) {
    const trimmed = String(raw || "").trim();
    if (trimmed === "") throw new Error("Vacío");
    const noCommas = trimmed.replace(/,/g, "");
    const cleaned = noCommas.replace(/[^\d.]/g, "");
    if (cleaned === "" || cleaned === ".") throw new Error("Sin dígitos");
    if (cleaned.split(".").length > 2) throw new Error("Use un solo punto decimal");
    return Number(cleaned);
  }
}
