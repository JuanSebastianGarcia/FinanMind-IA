export class PercentFormatter {
  /** Mirrors ``PercentagePresenter.format_pct``: one decimal, comma separator. */
  static formatPct(ratio) {
    const value = Number(ratio) || 0;
    const body = value.toFixed(1).replace(".", ",");
    return `${body} %`;
  }
}
