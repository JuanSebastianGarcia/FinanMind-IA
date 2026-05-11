export class DashboardShortAmountFormatter {
  /** Mirrors the ``M / K`` short label used by the original Tk chart. */
  static format(value) {
    const v = Number(value) || 0;
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `${Math.round(v / 1_000)}K`;
    return `${Math.round(v)}`;
  }
}
