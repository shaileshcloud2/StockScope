"""
╔══════════════════════════════════════════════════════════════════╗
║  update_fundamentals.py — v3 (yfinance edition)                 ║
║  Fetches fundamentals from Yahoo Finance (yfinance)             ║
║                                                                  ║
║  Run:  python update_fundamentals.py                            ║
║  When: Monthly, or after quarterly results season               ║
║                                                                  ║
║  Data source: Yahoo Finance via yfinance                        ║
║  Fields used: trailingPE, priceToBook, trailingEps, bookValue,  ║
║               fiftyTwoWeekHigh/Low, marketCap                   ║
║  Requires:    pip install yfinance pandas                        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, time, logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────
DATA_DIR    = Path(__file__).parent / "data"
SYMBOLS_CSV = DATA_DIR / "nse500_symbols.csv"
FUND_CSV    = DATA_DIR / "fundamentals.csv"

# ── Columns ───────────────────────────────────────────────────────
FUND_COLS = [
    "symbol", "rev_growth_score", "pat_growth_score", "roe_score",
    "de_score", "promoter_score",
    "pe", "pb", "roe_pct", "de_ratio",
    "rev_growth_pct", "pat_growth_pct", "promoter_pct",
    "eps", "book_value", "market_cap",
    "last_updated", "source",
]

# ── Scoring functions ─────────────────────────────────────────────
def score_pe_vs_sector(pe, sector):
    """Score PE against sector median benchmarks (FY2025 sector PEs)."""
    SECTOR_PE = {
        "Financial Services": 18,  "IT": 28,          "Auto": 22,
        "Defence":            45,  "Engineering":      40,
        "Chemicals":          30,  "Healthcare":       32,
        "FMCG":               48,  "Retail":           70,
        "Energy":             12,  "Metals":           12,
        "Building Materials": 30,  "Real Estate":      50,
        "Telecom":            28,  "Logistics":        30,
        "Aviation":           14,  "New Age Tech":     80,
    }
    if pe <= 0:
        return 4   # neutral — no earnings yet
    sector_pe = SECTOR_PE.get(sector, 30)
    ratio = pe / sector_pe
    if ratio <= 0.60:  return 7   # trading at big discount to sector
    if ratio <= 0.80:  return 6
    if ratio <= 1.00:  return 5
    if ratio <= 1.30:  return 4
    if ratio <= 1.70:  return 2
    return 1                        # very expensive vs sector

def score_pb(pb):
    if pb <= 0:    return 3
    if pb <= 1.5:  return 6
    if pb <= 3.0:  return 5
    if pb <= 5.0:  return 4
    if pb <= 8.0:  return 2
    return 1

def score_roe(roe):
    if roe <= 0:   return 0
    if roe >= 25:  return 6
    if roe >= 20:  return 5
    if roe >= 15:  return 4
    if roe >= 10:  return 2
    return 1

def score_de(de):
    if de < 0:     return 2   # unusual
    if de <= 0.3:  return 3
    if de <= 0.8:  return 2
    if de <= 1.5:  return 1
    return 0

def score_wk52_position(cmp, yr_high, yr_low):
    """
    52-week position as a proxy for revenue/PAT growth momentum.
    Stock in top 30% of year range = strong business momentum.
    """
    if yr_high <= 0 or yr_low < 0 or yr_high <= yr_low or cmp <= 0:
        return 3   # neutral
    pos = (cmp - yr_low) / (yr_high - yr_low)
    if pos >= 0.80:  return 7   # near 52-week high
    if pos >= 0.60:  return 6
    if pos >= 0.40:  return 5
    if pos >= 0.20:  return 3
    return 2                    # near 52-week low

def score_eps_growth(eps, book_value):
    """
    EPS/Book value ratio as ROE proxy when direct ROE unavailable.
    ROE = EPS / Book Value per share × 100
    """
    if eps > 0 and book_value > 0:
        implied_roe = (eps / book_value) * 100
        return score_roe(implied_roe), round(implied_roe, 2)
    return 3, 0.0

# ── yfinance fetch ──────────────────────────────────────────────────
def fetch_yf_data(symbol):
    """
    Fetch fundamentals for a single NSE symbol via yfinance.
    Returns dict with raw metrics or None on failure.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("\n❌  yfinance not installed. Run: pip install yfinance\n")
        sys.exit(1)

    yf_symbol = f"{symbol}.NS"
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
    except Exception as e:
        log.warning("yfinance fetch failed for %s: %s", symbol, e)
        return None

    cmp        = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0
    pe         = info.get("trailingPE") or 0
    pb         = info.get("priceToBook") or 0
    eps        = info.get("trailingEps") or info.get("epsTrailingTwelveMonths") or 0
    book_val   = info.get("bookValue") or 0
    yr_high    = info.get("fiftyTwoWeekHigh") or 0
    yr_low     = info.get("fiftyTwoWeekLow") or 0
    mkt_cap    = info.get("marketCap") or 0
    prev_close = info.get("previousClose") or cmp

    if cmp and prev_close and prev_close > 0:
        chg_pct = ((cmp - prev_close) / prev_close) * 100
    else:
        chg_pct = 0.0

    return {
        "cmp":        float(cmp) if cmp else 0,
        "pe":         float(pe) if pe else 0,
        "pb":         float(pb) if pb else 0,
        "eps":        float(eps) if eps else 0,
        "book_val":   float(book_val) if book_val else 0,
        "yr_high":    float(yr_high) if yr_high else 0,
        "yr_low":     float(yr_low) if yr_low else 0,
        "mkt_cap":    float(mkt_cap) if mkt_cap else 0,
        "chg_pct":    round(chg_pct, 2),
    }

# ── Main ──────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update NSE 500 fundamentals from Yahoo Finance")
    parser.add_argument("--symbols", nargs="*", help="Specific symbols to update")
    parser.add_argument("--force",   action="store_true", help="Re-fetch even if recently updated")
    parser.add_argument("--days",    type=int, default=25,
                        help="Skip symbols updated within this many days (default: 25)")
    parser.add_argument("--batch",   type=int, default=20,
                        help="Batch size for yfinance requests (default: 20)")
    parser.add_argument("--sleep",   type=float, default=1.0,
                        help="Seconds between requests (default: 1.0)")
    args = parser.parse_args()

    if not SYMBOLS_CSV.exists():
        print(f"❌  {SYMBOLS_CSV} not found")
        sys.exit(1)

    sym_df = pd.read_csv(SYMBOLS_CSV)
    sym_df = sym_df.drop_duplicates(subset=["symbol"])
    sym_df["angel_token"] = pd.to_numeric(sym_df.get("angel_token", 0), errors="coerce").fillna(0).astype(int)

    existing = {}
    if FUND_CSV.exists():
        df_ex = pd.read_csv(FUND_CSV)
        for _, row in df_ex.iterrows():
            existing[str(row["symbol"]).upper()] = row.to_dict()

    today   = datetime.now().date()
    target  = [s.upper() for s in args.symbols] if args.symbols else sym_df["symbol"].tolist()

    if not args.force:
        to_update = []
        for sym in target:
            ex   = existing.get(sym, {})
            last = str(ex.get("last_updated",""))[:10]
            if last:
                try:
                    age = (today - datetime.strptime(last, "%Y-%m-%d").date()).days
                    if age < args.days:
                        continue
                except Exception:
                    pass
            to_update.append(sym)
    else:
        to_update = target

    if not to_update:
        print(f"\n✅  All {len(target)} symbols updated within {args.days} days. Use --force to refresh.\n")
        return

    print(f"\n  Symbols to update: {len(to_update)}")
    print(f"  Existing cache:    {len(existing)} symbols")
    print(f"  Source:            Yahoo Finance (PE, PB, EPS, Book Value, 52W H/L)")
    print(f"  Batch size:        {args.batch}")
    print(f"  Rate limit sleep:  {args.sleep}s\n")

    sym_to_row = {}
    for _, row in sym_df.iterrows():
        sym = str(row["symbol"]).upper()
        sym_to_row[sym] = row

    total        = len(to_update)
    updated      = 0
    neutral_used = 0
    failed       = 0

    print(f"  Fetching data for {total} symbols…\n")

    for idx, sym in enumerate(to_update, start=1):
        row    = sym_to_row.get(sym, {})
        sector = str(row.get("sector", "Unknown")) if hasattr(row, "get") else str(row.get("sector", "Unknown"))

        print(f"  [{idx:>3}/{total}]  {sym:<15}", end=" ", flush=True)

        data = fetch_yf_data(sym)

        if data is None:
            if sym not in existing:
                existing[sym] = _neutral_row(sym, today)
                neutral_used += 1
            else:
                failed += 1
            print("⚠ (fetch failed)")
            time.sleep(args.sleep)
            continue

        cmp        = data["cmp"]
        pe         = data["pe"]
        pb         = data["pb"]
        eps        = data["eps"]
        book_val   = data["book_val"]
        yr_high    = data["yr_high"]
        yr_low     = data["yr_low"]
        mkt_cap    = data["mkt_cap"]
        chg_pct    = data["chg_pct"]

        if cmp <= 0 and pe <= 0 and eps <= 0:
            if sym not in existing:
                existing[sym] = _neutral_row(sym, today)
                neutral_used += 1
            else:
                failed += 1
            print("⚠ (no data)")
            time.sleep(args.sleep)
            continue

        roe_score_val, roe_pct = score_eps_growth(eps, book_val)
        wk_score    = score_wk52_position(cmp, yr_high, yr_low)
        rev_score   = wk_score
        pat_score   = min(wk_score, 6)
        roe_s       = roe_score_val
        de_s        = score_de(0.5)
        prom_s      = 2

        if sym in existing:
            ex = existing[sym]
            if float(ex.get("de_ratio", 0) or 0) > 0:
                de_s = score_de(float(ex.get("de_ratio", 0)))
            if float(ex.get("promoter_pct", 0) or 0) > 0:
                prom_s = _score_promoter(float(ex.get("promoter_pct", 0)))

        existing[sym] = {
            "symbol":           sym,
            "rev_growth_score": rev_score,
            "pat_growth_score": pat_score,
            "roe_score":        roe_s,
            "de_score":         de_s,
            "promoter_score":   prom_s,
            "pe":               round(pe, 2),
            "pb":               round(pb, 2),
            "roe_pct":          round(roe_pct, 2),
            "de_ratio":         round(float(existing.get(sym, {}).get("de_ratio", 0) or 0), 2),
            "rev_growth_pct":   round(chg_pct, 2),
            "pat_growth_pct":   round(chg_pct, 2),
            "promoter_pct":     round(float(existing.get(sym, {}).get("promoter_pct", 0) or 0), 2),
            "eps":              round(eps, 2),
            "book_value":       round(book_val, 2),
            "market_cap":       round(mkt_cap, 2),
            "last_updated":     str(today),
            "source":           "yfinance",
        }
        updated += 1
        print(f"✓  PE={pe:.1f} PB={pb:.1f} EPS={eps:.1f} BV={book_val:.1f}")
        time.sleep(args.sleep)

    for _, row in sym_df.iterrows():
        sym = str(row["symbol"]).upper()
        if sym not in existing:
            existing[sym] = _neutral_row(sym, today)
            neutral_used += 1

    rows   = []
    for _, row in sym_df.iterrows():
        sym = str(row["symbol"]).upper()
        r   = existing.get(sym, _neutral_row(sym, today))
        rows.append({col: r.get(col, "") for col in FUND_COLS})

    df_out = pd.DataFrame(rows, columns=FUND_COLS)
    df_out.to_csv(FUND_CSV, index=False)

    print("\n" + "═"*52)
    print(f"  ✅  Updated from Yahoo Finance:  {updated} symbols")
    print(f"  ⚪  Neutral fallback used:       {neutral_used} symbols")
    print(f"  ⚠   Fetch failed / no data:     {failed} symbols")
    print(f"  📄  Saved to:                   data/fundamentals.csv")
    print(f"  📊  Total rows:                 {len(df_out)}")
    print()
    print("  Next steps:")
    print("  1. In browser → click 'Reload Fundamentals' button")
    print("  2. Or restart: python server.py")
    print("═"*52 + "\n")

def _neutral_row(sym, today):
    return {
        "symbol": sym,
        "rev_growth_score": 3,
        "pat_growth_score": 3,
        "roe_score": 3,
        "de_score": 2,
        "promoter_score": 2,
        "pe": 0,
        "pb": 0,
        "roe_pct": 0,
        "de_ratio": 0,
        "rev_growth_pct": 0,
        "pat_growth_pct": 0,
        "promoter_pct": 0,
        "eps": 0,
        "book_value": 0,
        "market_cap": 0,
        "last_updated": str(today),
        "source": "neutral-fallback",
    }

def _score_promoter(pct):
    if pct >= 50: return 3
    if pct >= 35: return 2
    if pct >= 20: return 1
    return 0

if __name__ == "__main__":
    main()
