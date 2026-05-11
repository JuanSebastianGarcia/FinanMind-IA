export class InvestmentsChartPalette {
  /** JS mirror of the Python ``InvestmentChartPalette`` accent sequence. */
  static get COLORS() {
    return InvestmentsChartPalette._COLORS;
  }

  static colorAt(index) {
    const palette = InvestmentsChartPalette._COLORS;
    return palette[((index % palette.length) + palette.length) % palette.length];
  }
}

InvestmentsChartPalette._COLORS = [
  "#4f8ef7",
  "#22c55e",
  "#f59e0b",
  "#a855f7",
  "#ec4899",
  "#14b8a6",
  "#6366f1",
  "#eab308",
  "#0ea5e9",
  "#f97316",
];
