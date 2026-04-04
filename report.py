import logging
from datetime import date
from pathlib import Path
from typing import Optional

from fpdf import FPDF, XPos, YPos

import analysis as ana
import charts
import cleaner
import explorer
import fetcher

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Midnight Ledger palette ───────────────────────────────────────────────────
# Dark-first design system matching the React frontend (index.css variables)

C_BG_BASE    = (7,   9,   15)   # --bg-base:    #07090F
C_BG_SURFACE = (14,  21,  35)   # --bg-surface: #0E1523
C_BG_RAISED  = (20,  31,  48)   # --bg-raised:  #141F30
C_BG_HOVER   = (26,  40,  64)   # --bg-hover:   #1A2840

C_BORDER_S   = (24,  37,  58)   # --border-subtle:  #18253A
C_BORDER_D   = (31,  48,  80)   # --border-default: #1F3050
C_BORDER_B   = (44,  69,  112)  # --border-bright:  #2C4570

C_ACCENT     = (79,  172, 247)  # --accent:    #4FACF7
C_POSITIVE   = (43,  196, 138)  # --positive:  #2BC48A
C_NEGATIVE   = (240, 100, 112)  # --negative:  #F06470

C_TEXT_1     = (232, 240, 252)  # --text-1:    #E8F0FC
C_TEXT_2     = (107, 141, 181)  # --text-2:    #6B8DB5
C_TEXT_3     = (61,  88,  120)  # --text-3:    #3D5878
C_TEXT_4     = (36,  54,  80)   # --text-4:    #243650

# Page geometry
MARGIN     = 16   # mm
PAGE_W     = 210  # A4
PAGE_H     = 297  # A4
USABLE_W   = PAGE_W - MARGIN * 2

# ── Field definitions ─────────────────────────────────────────────────────────
_STAT_LABELS = {
    "start_date":            "Start Date",
    "end_date":              "End Date",
    "total_return_pct":      "Total Return",
    "annualised_return_pct": "Annualised Return",
    "volatility_pct":        "Volatility (Ann.)",
    "sharpe_ratio":          "Sharpe Ratio",
    "max_drawdown_pct":      "Max Drawdown",
    "best_day_pct":          "Best Day",
    "worst_day_pct":         "Worst Day",
    "avg_daily_volume":      "Avg Daily Volume",
}
_PCT_KEYS = {
    "total_return_pct", "annualised_return_pct", "volatility_pct",
    "max_drawdown_pct", "best_day_pct", "worst_day_pct",
}
_INFO_FIELDS = [
    ("sector",           "Sector"),
    ("industry",         "Industry"),
    ("marketCap",        "Market Cap"),
    ("trailingPE",       "Trailing P/E"),
    ("fiftyTwoWeekHigh", "52-Week High"),
    ("fiftyTwoWeekLow",  "52-Week Low"),
    ("dividendYield",    "Dividend Yield"),
]
_CHART_CAPTIONS = {
    "candlestick":         "Candlestick chart (last 90 trading days) with volume bars",
    "price_ma":            "Close price with 20-day, 50-day, and 200-day moving averages",
    "cumulative_return":   "Cumulative return (%) from the start of the report period",
    "drawdown":            "Rolling drawdown from the all-time high within the period",
    "monthly_returns":     "Heatmap of average daily returns by month and year",
    "summary_stats_table": "Summary statistics table",
}
_CHART_ORDER = [
    "candlestick", "price_ma", "cumulative_return",
    "drawdown", "monthly_returns", "summary_stats_table",
]


# ── Formatters ────────────────────────────────────────────────────────────────

def _fmt_stat(key: str, val) -> str:
    if val is None:
        return "N/A"
    if key in _PCT_KEYS:
        return f"{val:+.2f}%"
    if key == "sharpe_ratio":
        return f"{val:.2f}"
    if key == "avg_daily_volume":
        return f"{val:,.0f}"
    return str(val)


def _fmt_info(key: str, val) -> str:
    if val is None:
        return "N/A"
    if key == "marketCap":
        v = float(val)
        if v >= 1e12:
            return f"${v/1e12:.2f}T"
        if v >= 1e9:
            return f"${v/1e9:.2f}B"
        return f"${v:,.0f}"
    if key == "dividendYield" and isinstance(val, (int, float)):
        return f"{float(val)*100:.2f}%"
    if isinstance(val, float):
        return f"{val:,.2f}"
    return str(val)


def _val_color(key: str, val) -> Optional[tuple]:
    """Return accent color for a stat value, or None for neutral."""
    if key in _PCT_KEYS and isinstance(val, (int, float)):
        return C_POSITIVE if val >= 0 else C_NEGATIVE
    return None


# ── PDF class ─────────────────────────────────────────────────────────────────

class FinancialReport(FPDF):

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.set_auto_page_break(auto=False)
        self.set_margins(MARGIN, MARGIN, MARGIN)

    # -- Recurring elements ---------------------------------------------------

    def header(self):
        """Thin top accent bar + app name on every page except the cover."""
        if self.page_no() == 1:
            return
        # Dark background fill for the top strip
        self.set_fill_color(*C_BG_SURFACE)
        self.rect(0, 0, PAGE_W, 12, style="F")
        # Accent bottom border
        self.set_fill_color(*C_ACCENT)
        self.rect(0, 11.5, PAGE_W, 0.5, style="F")
        # App name (left) + asset symbol (right)
        self.set_xy(MARGIN, 3)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*C_ACCENT)
        self.cell(USABLE_W / 2, 6, "FINPIPE  /  AUTOMATED FINANCIAL REPORT", align="L")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*C_TEXT_3)
        self.set_xy(MARGIN, 3)
        self.cell(USABLE_W, 6,
                  f"{self.config['symbol']}  ·  {self.config.get('period', '')}  ·  {self.config.get('interval', '')}",
                  align="R")

    def footer(self):
        """Page number + source attribution."""
        if self.page_no() == 1:
            return
        y = PAGE_H - 10
        self.set_fill_color(*C_BG_SURFACE)
        self.rect(0, PAGE_H - 11, PAGE_W, 11, style="F")
        self.set_fill_color(*C_BORDER_S)
        self.rect(0, PAGE_H - 11, PAGE_W, 0.4, style="F")
        self.set_xy(MARGIN, y)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_TEXT_3)
        self.cell(USABLE_W / 2, 5, f"Page {self.page_no()}", align="L")
        self.cell(USABLE_W / 2, 5, "Data: Yahoo Finance via yfinance", align="R")

    # -- Drawing primitives ---------------------------------------------------

    def _fill_page_bg(self, color=None):
        """Paint a full-page dark background."""
        self.set_fill_color(*(color or C_BG_BASE))
        self.rect(0, 0, PAGE_W, PAGE_H, style="F")

    def _accent_divider(self, y=None, width=None, color=None):
        """Draw a horizontal accent rule."""
        y = y if y is not None else self.get_y()
        x = MARGIN
        w = width or USABLE_W
        self.set_fill_color(*(color or C_BORDER_D))
        self.rect(x, y, w, 0.4, style="F")

    def _section_heading(self, text: str, y_gap: float = 8):
        """Uppercase section label with an accent left bar."""
        self.ln(y_gap)
        y = self.get_y()
        # Left accent bar
        self.set_fill_color(*C_ACCENT)
        self.rect(MARGIN, y, 2.5, 6, style="F")
        # Label text
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_ACCENT)
        self.set_xy(MARGIN + 6, y)
        self.cell(USABLE_W - 6, 6, text.upper(), align="L",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)
        self._accent_divider(color=C_BORDER_D)
        self.ln(5)

    def _badge(self, x: float, y: float, text: str, bg: tuple, fg: tuple,
               h: float = 5.5, pad: float = 6) -> float:
        """Draw a badge, returns its width."""
        self.set_font("Helvetica", "B", 7)
        w = self.get_string_width(text) + pad * 2
        # Background rect
        self.set_fill_color(*bg)
        self.set_draw_color(*bg)
        self.rect(x, y, w, h, style="F")
        # Text
        self.set_text_color(*fg)
        self.set_xy(x, y + (h - 3.5) / 2)
        self.cell(w, 3.5, text, align="C")
        return w

    # -- Cover page -----------------------------------------------------------

    def title_page(self, analysis: dict):
        self.add_page()
        self._fill_page_bg(C_BG_BASE)

        cfg   = self.config
        stats = analysis.get("summary_stats") or {}

        # ── Hero banner (top third) ──────────────────────────────────────────
        banner_h = 95
        # Gradient-look: two overlapping rects
        self.set_fill_color(*C_BG_SURFACE)
        self.rect(0, 0, PAGE_W, banner_h, style="F")
        self.set_fill_color(*C_BG_RAISED)
        self.rect(0, banner_h - 12, PAGE_W, 12, style="F")

        # Top accent strip
        self.set_fill_color(*C_ACCENT)
        self.rect(0, 0, PAGE_W, 1.5, style="F")

        # Corner decoration — thin vertical accent lines
        for xi in [0, PAGE_W - 1.5]:
            self.set_fill_color(*C_BORDER_B)
            self.rect(xi, 0, 1.5, banner_h, style="F")

        # Finpipe wordmark
        self.set_xy(0, 14)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_ACCENT)
        self.cell(PAGE_W, 5, "FINPIPE", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Divider dot
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_TEXT_4)
        self.cell(PAGE_W, 4, "·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Asset name — large
        self.ln(5)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*C_TEXT_1)
        self.cell(PAGE_W, 12, cfg["name"], align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Ticker + asset type badges — centered
        sym_w   = self.get_string_width(f"  {cfg['symbol']}  ") + 4
        atype   = cfg.get("asset_type", "")
        badge_gap = 4
        total_badge_w = sym_w + (self.get_string_width(f"  {atype}  ") + 4 + badge_gap if atype else 0)
        bx = (PAGE_W - total_badge_w) / 2

        y_badges = self.get_y() + 3
        # Symbol badge
        sym_badge_w = self._badge(bx, y_badges, f"  {cfg['symbol']}  ",
                                   C_ACCENT, C_BG_BASE, h=7, pad=4)
        if atype:
            self._badge(bx + sym_badge_w + badge_gap, y_badges, f"  {atype}  ",
                        C_BG_HOVER, C_TEXT_2, h=7, pad=4)

        # Currency / period / interval line
        self.set_xy(0, y_badges + 10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*C_TEXT_3)
        details = (
            f"Currency: {cfg.get('currency', 'N/A')}     "
            f"Period: {cfg.get('period', '')}     "
            f"Interval: {cfg.get('interval', '')}"
        )
        self.cell(PAGE_W, 5, details, align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Date generated
        self.ln(3)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_TEXT_4)
        self.cell(PAGE_W, 4, f"Generated  {date.today().strftime('%B %d, %Y')}",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ── Stats strip (below banner) ────────────────────────────────────────
        strip_y = banner_h + 6
        self.set_y(strip_y)

        # Quick-glance: Period Return
        ret = stats.get("total_return_pct")
        if ret is not None:
            ret_color  = C_POSITIVE if ret >= 0 else C_NEGATIVE
            ret_label  = f"{ret:+.2f}%"
            self.set_xy(0, strip_y)
            self.set_font("Helvetica", "B", 28)
            self.set_text_color(*ret_color)
            self.cell(PAGE_W, 14, ret_label, align="C",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*C_TEXT_3)
            self.cell(PAGE_W, 5, "PERIOD TOTAL RETURN", align="C",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Dates bar
        if stats.get("start_date") and stats.get("end_date"):
            self.ln(3)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*C_TEXT_2)
            self.cell(PAGE_W, 5,
                      f"{stats['start_date']}  to  {stats['end_date']}",
                      align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ── Key metrics grid (4 cards, 2×2) ──────────────────────────────────
        self.ln(10)
        grid_y = self.get_y()
        col_w  = USABLE_W / 2
        row_h  = 22
        card_items = [
            ("Annualised Return", "annualised_return_pct"),
            ("Volatility (Ann.)", "volatility_pct"),
            ("Sharpe Ratio",      "sharpe_ratio"),
            ("Max Drawdown",      "max_drawdown_pct"),
        ]
        for idx, (label, key) in enumerate(card_items):
            col = idx % 2
            row = idx // 2
            cx  = MARGIN + col * (col_w + 2)
            cy  = grid_y + row * (row_h + 3)

            # Card background
            self.set_fill_color(*C_BG_RAISED)
            self.set_draw_color(*C_BORDER_D)
            self.rect(cx, cy, col_w - 2, row_h, style="FD")

            # Card label
            self.set_xy(cx + 5, cy + 4)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C_TEXT_3)
            self.cell(col_w - 12, 4, label.upper())

            # Card value
            val = stats.get(key)
            fmt = _fmt_stat(key, val)
            color = _val_color(key, val) or C_TEXT_1
            self.set_xy(cx + 5, cy + 9)
            self.set_font("Courier", "B", 14)
            self.set_text_color(*color)
            self.cell(col_w - 12, 7, fmt)

        # ── Footer note ───────────────────────────────────────────────────────
        self.set_xy(MARGIN, PAGE_H - 20)
        self._accent_divider(color=C_BORDER_S)
        self.ln(4)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_TEXT_4)
        self.cell(USABLE_W, 4,
                  "This report is for informational purposes only and does not constitute financial advice.",
                  align="C")

    # -- Metrics page ---------------------------------------------------------

    def metrics_page(self, analysis: dict):
        self.add_page()
        self._fill_page_bg()

        content_top = 16   # below header bar
        self.set_y(content_top)

        stats = analysis.get("summary_stats") or {}
        self._section_heading("Key Performance Metrics")

        # Grid: 2 columns, rows of cards
        keys   = list(_STAT_LABELS.items())
        col_w  = USABLE_W / 2
        card_h = 16
        card_gap_x = 3
        card_gap_y = 3
        inner_w = col_w - card_gap_x

        for idx, (key, label) in enumerate(keys):
            col = idx % 2
            row = idx // 2
            cx  = MARGIN + col * col_w
            cy  = self.get_y() - (16 - 1)   # track manually below

            # We'll just lay them out sequentially, row by row
            pass

        # Re-render as a proper grid
        y0 = self.get_y()
        for idx, (key, label) in enumerate(keys):
            col = idx % 2
            row = idx // 2
            cx  = MARGIN + col * (inner_w + card_gap_x)
            cy  = y0 + row * (card_h + card_gap_y)

            val   = stats.get(key)
            fmt   = _fmt_stat(key, val)
            color = _val_color(key, val) or C_TEXT_1

            # Card
            self.set_fill_color(*C_BG_RAISED)
            self.set_draw_color(*C_BORDER_S)
            self.rect(cx, cy, inner_w, card_h, style="FD")

            # Left accent stripe for colored values
            if _val_color(key, val):
                self.set_fill_color(*color)
                self.rect(cx, cy, 2, card_h, style="F")

            # Label
            self.set_xy(cx + 6, cy + 3)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C_TEXT_3)
            self.cell(inner_w - 8, 3.5, label.upper())

            # Value
            self.set_xy(cx + 6, cy + 7.5)
            self.set_font("Courier", "B", 11)
            self.set_text_color(*color)
            self.cell(inner_w - 8, 5.5, fmt)

        # Move cursor below the grid
        rows = (len(keys) + 1) // 2
        self.set_y(y0 + rows * (card_h + card_gap_y) + 4)

    # -- Asset info page ------------------------------------------------------

    def asset_info_page(self, analysis: dict):
        info = analysis.get("asset_info") or {}
        rows = [
            (label, _fmt_info(key, info[key]))
            for key, label in _INFO_FIELDS
            if key in info and info[key] not in (None, "", 0)
        ]
        if not rows:
            return

        self.add_page()
        self._fill_page_bg()

        content_top = 16
        self.set_y(content_top)
        self._section_heading("Asset Information")

        col_w  = USABLE_W / 2
        card_h = 15
        card_gap_x = 3
        card_gap_y = 3
        inner_w = col_w - card_gap_x

        y0 = self.get_y()
        for idx, (label, value) in enumerate(rows):
            col = idx % 2
            row = idx // 2
            cx  = MARGIN + col * (inner_w + card_gap_x)
            cy  = y0 + row * (card_h + card_gap_y)

            # Card
            self.set_fill_color(*C_BG_RAISED)
            self.set_draw_color(*C_BORDER_S)
            self.rect(cx, cy, inner_w, card_h, style="FD")

            # Label
            self.set_xy(cx + 6, cy + 3)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C_TEXT_3)
            self.cell(inner_w - 8, 3.5, label.upper())

            # Value
            self.set_xy(cx + 6, cy + 7.5)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*C_TEXT_1)
            self.cell(inner_w - 8, 5, str(value))

    # -- Chart pages ----------------------------------------------------------

    def charts_pages(self, chart_paths: list):
        path_map = {}
        for p in chart_paths:
            stem = Path(p).stem
            for key in _CHART_ORDER:
                if stem.endswith(key):
                    path_map[key] = p
                    break

        for key in _CHART_ORDER:
            p = path_map.get(key)
            if not p or not Path(p).exists():
                continue

            self.add_page()
            self._fill_page_bg()

            caption = _CHART_CAPTIONS.get(key, key.replace("_", " ").title())

            # Header area
            header_h = 14
            self.set_fill_color(*C_BG_SURFACE)
            self.rect(MARGIN, 16, USABLE_W, header_h, style="F")
            # Left accent bar on header
            self.set_fill_color(*C_ACCENT)
            self.rect(MARGIN, 16, 3, header_h, style="F")

            # Caption text
            self.set_xy(MARGIN + 8, 16 + (header_h - 5) / 2)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*C_TEXT_1)
            self.cell(USABLE_W - 8, 5, caption)

            # Chart image — fit usable width, preserve aspect
            img_y = 16 + header_h + 4
            max_h = PAGE_H - img_y - 14  # leave footer room
            self.image(p, x=MARGIN, y=img_y, w=USABLE_W, h=0)

            # Subtle border around the image area
            self.set_draw_color(*C_BORDER_S)
            self.rect(MARGIN, img_y, USABLE_W, max_h, style="D")

    # -- Disclaimer page ------------------------------------------------------

    def disclaimer_page(self):
        self.add_page()
        self._fill_page_bg()
        self.set_y(16)
        self._section_heading("Disclaimer")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_TEXT_2)
        text = (
            "This report is generated automatically from Yahoo Finance data via the yfinance library "
            "for educational and portfolio tracking purposes only. It does not constitute financial "
            "advice, a solicitation, or a recommendation to buy or sell any security.\n\n"
            "Past performance is not indicative of future results. All data is sourced from public "
            "market feeds and may be subject to delays or inaccuracies. The user assumes full "
            "responsibility for any investment decisions made using this information.\n\n"
            "Finpipe is an open-source project and is not affiliated with Yahoo Finance, "
            "any brokerage, or financial institution."
        )
        self.set_x(MARGIN)
        self.multi_cell(USABLE_W, 6, text)

        # Legal note box
        self.ln(8)
        bx, by = MARGIN, self.get_y()
        bw, bh = USABLE_W, 18
        self.set_fill_color(*C_BG_RAISED)
        self.set_draw_color(*C_BORDER_D)
        self.rect(bx, by, bw, bh, style="FD")
        self.set_fill_color(*C_ACCENT)
        self.rect(bx, by, 2, bh, style="F")
        self.set_xy(bx + 8, by + 3)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_ACCENT)
        self.cell(bw - 12, 4, "NOT FINANCIAL ADVICE")
        self.set_xy(bx + 8, by + 8)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*C_TEXT_3)
        self.cell(bw - 12, 4,
                  "For personal research and tracking only. Always consult a qualified financial advisor.")


# ── Public API ────────────────────────────────────────────────────────────────

def generate_report(config: dict, analysis: dict, chart_paths: list) -> str:
    """Build and save the PDF report. Returns the saved file path."""
    symbol   = config["symbol"]
    from config import DATA_DIR
    out_path = Path(DATA_DIR) / f"{symbol}_report.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FinancialReport(config)
    pdf.title_page(analysis)
    pdf.metrics_page(analysis)
    pdf.asset_info_page(analysis)
    pdf.charts_pages(chart_paths)
    pdf.disclaimer_page()

    pdf.output(str(out_path))
    logger.info("Report saved to %s", out_path)
    return str(out_path)


# ── Main guard ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    config = explorer.interactive_select()
    fetcher.fetch_data(config)
    cleaner.clean_data(config)
    results = ana.run_analysis(config)
    chart_files = charts.generate_charts(config, results)
    path = generate_report(config, results, chart_files)
    print(f"\nReport saved: {path}")
