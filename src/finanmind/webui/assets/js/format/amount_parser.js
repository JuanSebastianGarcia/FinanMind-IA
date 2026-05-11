export class AmountParser {
  /** Mirrors ``CopAmountParser.parse``: strip non-digits then read whole pesos. */
  static parse(raw) {
    const trimmed = String(raw || "").trim();
    if (trimmed === "") throw new Error("Vacío");
    const digitsOnly = trimmed.replace(/[^\d]/g, "");
    if (digitsOnly === "") throw new Error("Sin dígitos");
    return Number(digitsOnly);
  }
}
