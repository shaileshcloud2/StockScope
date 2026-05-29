"""
Fundamentals SQLite store — replaces fundamentals.csv.
- Auto-migrates from CSV on first run (no data loss)
- Daily staleness check (24-hour threshold)
- refresh_fundamentals() fetches live data from Yahoo Finance
- load_fundamentals() returns same dict format as the old CSV loader
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

DATA_DIR    = Path(__file__).parent.parent / "data"
DB_PATH     = DATA_DIR / "fundamentals.db"
CSV_PATH    = DATA_DIR / "fundamentals.csv"
SYMBOLS_CSV = DATA_DIR / "nse500_symbols.csv"

STALE_HOURS = 24

# ── Schema ─────────────────────────────────────────────────────────
_DDL = """
CREATE TABLE IF NOT EXISTS fundamentals (
    symbol           TEXT PRIMARY KEY,
    rev_growth_score INTEGER DEFAULT 3,
    pat_growth_score INTEGER DEFAULT 3,
    roe_score        INTEGER DEFAULT 3,
    de_score         INTEGER DEFAULT 2,
    promoter_score   INTEGER DEFAULT 2,
    pe               REAL    DEFAULT 0,
    pb               REAL    DEFAULT 0,
    roe_pct          REAL    DEFAULT 0,
    de_ratio         REAL    DEFAULT 0,
    rev_growth_pct   REAL    DEFAULT 0,
    pat_growth_pct   REAL    DEFAULT 0,
    promoter_pct     REAL    DEFAULT 0,
    eps              REAL    DEFAULT 0,
    book_value       REAL    DEFAULT 0,
    market_cap       REAL    DEFAULT 0,
    last_updated     TEXT    DEFAULT '',
    source           TEXT    DEFAULT 'sqlite'
);
"""

# ── Scoring helpers (identical to update_fundamentals.py logic) ────
def _score_roe(roe):
    if roe <= 0:   return 0
    if roe >= 25:  return 6
    if roe >= 20:  return 5
    if roe >= 15:  return 4
    if roe >= 10:  return 2
    return 1

def _score_de(de):
    if de < 0:    return 2
    if de <= 0.3: return 3
    if de <= 0.8: return 2
    if de <= 1.5: return 1
    return 0

def _score_wk52(cmp, yr_high, yr_low):
    if yr_high <= 0 or yr_low < 0 or yr_high <= yr_low or cmp <= 0:
        return 3
    pos = (cmp - yr_low) / (yr_high - yr_low)
    if pos >= 0.80: return 7
    if pos >= 0.60: return 6
    if pos >= 0.40: return 5
    if pos >= 0.20: return 3
    return 2

def _score_eps_roe(eps, book_value):
    if eps > 0 and book_value > 0:
        implied_roe = (eps / book_value) * 100
        return _score_roe(implied_roe), round(implied_roe, 2)
    return 3, 0.0

def _score_promoter(pct):
    if pct >= 50: return 3
    if pct >= 35: return 2
    if pct >= 20: return 1
    return 0

# ── DB helpers ─────────────────────────────────────────────────────
def _conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)

def init_db():
    """Create DB and migrate from CSV if it's the first run."""
    DATA_DIR.mkdir(exist_ok=True)
    with _conn() as con:
        con.executescript(_DDL)
        con.commit()

    with _conn() as con:
        count = con.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0]

    if count == 0 and CSV_PATH.exists():
        log.info("First run — migrating fundamentals.csv → fundamentals.db")
        try:
            df = pd.read_csv(CSV_PATH)
            rows = []
            for _, row in df.iterrows():
                rows.append((
                    str(row["symbol"]),
                    int(row.get("rev_growth_score", 3) or 3),
                    int(row.get("pat_growth_score", 3) or 3),
                    int(row.get("roe_score",        3) or 3),
                    int(row.get("de_score",         2) or 2),
                    int(row.get("promoter_score",   2) or 2),
                    float(row.get("pe",             0) or 0),
                    float(row.get("pb",             0) or 0),
                    float(row.get("roe_pct",        0) or 0),
                    float(row.get("de_ratio",       0) or 0),
                    float(row.get("rev_growth_pct", 0) or 0),
                    float(row.get("pat_growth_pct", 0) or 0),
                    float(row.get("promoter_pct",   0) or 0),
                    float(row.get("eps",            0) or 0),
                    float(row.get("book_value",     0) or 0),
                    float(row.get("market_cap",     0) or 0),
                    str(row.get("last_updated", "") or ""),
                    str(row.get("source", "migrated") or "migrated"),
                ))
            with _conn() as con:
                con.executemany(
                    "INSERT OR REPLACE INTO fundamentals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    rows,
                )
                con.commit()
            log.info("Migrated %d rows from fundamentals.csv to SQLite", len(rows))
        except Exception as e:
            log.error("CSV migration failed: %s", e)

# ── Public API ──────────────────────────────────────────────────────
def load_fundamentals():
    """
    Return {symbol: {...}} — identical structure to the old CSV-based loader.
    Called at screener startup and after every refresh.
    """
    init_db()
    fund = {}
    with _conn() as con:
        cur  = con.execute("SELECT * FROM fundamentals")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    for row in rows:
        r   = dict(zip(cols, row))
        sym = r["symbol"]
        fund[sym] = {
            "rev_growth_score": int(r.get("rev_growth_score", 3) or 3),
            "pat_growth_score": int(r.get("pat_growth_score", 3) or 3),
            "roe_score":        int(r.get("roe_score",        3) or 3),
            "de_score":         int(r.get("de_score",         2) or 2),
            "promoter_score":   int(r.get("promoter_score",   2) or 2),
            "pe":               float(r.get("pe",             0) or 0),
            "pb":               float(r.get("pb",             0) or 0),
            "roe_pct":          float(r.get("roe_pct",        0) or 0),
            "de_ratio":         float(r.get("de_ratio",       0) or 0),
            "rev_growth_pct":   float(r.get("rev_growth_pct", 0) or 0),
            "pat_growth_pct":   float(r.get("pat_growth_pct", 0) or 0),
            "promoter_pct":     float(r.get("promoter_pct",   0) or 0),
            "eps":              float(r.get("eps",            0) or 0),
            "book_value":       float(r.get("book_value",     0) or 0),
            "market_cap":       float(r.get("market_cap",     0) or 0),
            "last_updated":     str(r.get("last_updated", "") or ""),
            "source":           str(r.get("source", "sqlite") or "sqlite"),
        }
    log.info("Fundamentals loaded from SQLite: %d symbols", len(fund))
    return fund


def get_db_status():
    """Return a status dict shown in the UI."""
    init_db()
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0]
        dates = con.execute(
            "SELECT last_updated FROM fundamentals "
            "WHERE last_updated != '' ORDER BY last_updated"
        ).fetchall()

    if not dates:
        return {
            "total": total, "stale": total,
            "oldest": None, "newest": None, "is_stale": True,
        }

    oldest = dates[0][0][:10]
    newest = dates[-1][0][:10]
    cutoff = (datetime.now() - timedelta(hours=STALE_HOURS)).strftime("%Y-%m-%d")
    stale  = sum(1 for (d,) in dates if d[:10] < cutoff)

    return {
        "total":    total,
        "stale":    stale,
        "oldest":   oldest,
        "newest":   newest,
        "is_stale": stale > 0,
    }


def is_stale():
    return get_db_status()["is_stale"]


# ── yfinance fetch for one stock ────────────────────────────────────
def _fetch_one(symbol, existing_row=None):
    """Fetch from yfinance and return a row dict, or None on failure."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info   = ticker.info
    except Exception as e:
        log.debug("yfinance fetch failed for %s: %s", symbol, e)
        return None

    cmp      = float(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0)
    prev     = float(info.get("previousClose") or cmp)
    pe       = float(info.get("trailingPE")             or 0)
    pb       = float(info.get("priceToBook")            or 0)
    eps      = float(info.get("trailingEps") or info.get("epsTrailingTwelveMonths") or 0)
    book_val = float(info.get("bookValue")              or 0)
    yr_high  = float(info.get("fiftyTwoWeekHigh")       or 0)
    yr_low   = float(info.get("fiftyTwoWeekLow")        or 0)
    mkt_cap  = float(info.get("marketCap")              or 0)

    if cmp <= 0 and pe <= 0 and eps <= 0:
        return None

    chg_pct = round(((cmp - prev) / prev * 100), 2) if prev > 0 else 0.0

    roe_score_val, roe_pct = _score_eps_roe(eps, book_val)
    wk_score = _score_wk52(cmp, yr_high, yr_low)

    # Preserve existing de_ratio and promoter_pct (not available in yfinance easily)
    de_ratio   = float(existing_row.get("de_ratio",    0) or 0) if existing_row else 0.0
    promoter   = float(existing_row.get("promoter_pct", 0) or 0) if existing_row else 0.0

    return {
        "rev_growth_score": wk_score,
        "pat_growth_score": min(wk_score, 6),
        "roe_score":        roe_score_val,
        "de_score":         _score_de(de_ratio),
        "promoter_score":   _score_promoter(promoter),
        "pe":               round(pe,       2),
        "pb":               round(pb,       2),
        "roe_pct":          round(roe_pct,  2),
        "de_ratio":         round(de_ratio, 2),
        "rev_growth_pct":   chg_pct,
        "pat_growth_pct":   chg_pct,
        "promoter_pct":     round(promoter, 2),
        "eps":              round(eps,      2),
        "book_value":       round(book_val, 2),
        "market_cap":       round(mkt_cap,  2),
        "last_updated":     datetime.now().strftime("%Y-%m-%d"),
        "source":           "yfinance",
    }


def refresh_fundamentals(symbols=None, progress_cb=None, sleep_sec=0.8):
    """
    Fetch fresh fundamentals from Yahoo Finance for all (or specified) symbols.
    Updates SQLite records in-place.
    Returns (updated_count, failed_count).
    """
    def _cb(pct, status):
        if progress_cb:
            try:
                progress_cb(pct, status)
            except Exception:
                pass

    init_db()

    if not SYMBOLS_CSV.exists():
        _cb(100, "nse500_symbols.csv not found")
        return 0, 0

    sym_df   = pd.read_csv(SYMBOLS_CSV).drop_duplicates(subset=["symbol"])
    all_syms = [str(r["symbol"]) for _, r in sym_df.iterrows()]

    to_update = symbols if symbols else all_syms

    # Load existing rows so we can preserve de_ratio / promoter_pct
    with _conn() as con:
        cur  = con.execute("SELECT * FROM fundamentals")
        cols = [d[0] for d in cur.description]
        existing = {r[0]: dict(zip(cols, r)) for r in cur.fetchall()}

    total   = len(to_update)
    updated = 0
    failed  = 0

    _cb(0, f"Starting refresh for {total} stocks…")

    for idx, sym in enumerate(to_update):
        pct = int((idx / total) * 100)
        _cb(min(pct, 99), f"Fetching {sym} ({idx+1}/{total}) — {updated} updated, {failed} failed")

        data = _fetch_one(sym, existing.get(sym))

        if data is None:
            failed += 1
            # If brand-new symbol with no existing row, insert neutral placeholder
            if sym not in existing:
                with _conn() as con:
                    con.execute(
                        "INSERT OR IGNORE INTO fundamentals (symbol, last_updated, source) VALUES (?,?,?)",
                        (sym, datetime.now().strftime("%Y-%m-%d"), "neutral-fallback"),
                    )
                    con.commit()
        else:
            with _conn() as con:
                con.execute(
                    """INSERT OR REPLACE INTO fundamentals
                       (symbol,rev_growth_score,pat_growth_score,roe_score,
                        de_score,promoter_score,pe,pb,roe_pct,de_ratio,
                        rev_growth_pct,pat_growth_pct,promoter_pct,eps,
                        book_value,market_cap,last_updated,source)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        sym,
                        data["rev_growth_score"], data["pat_growth_score"],
                        data["roe_score"],         data["de_score"],
                        data["promoter_score"],    data["pe"],
                        data["pb"],                data["roe_pct"],
                        data["de_ratio"],          data["rev_growth_pct"],
                        data["pat_growth_pct"],    data["promoter_pct"],
                        data["eps"],               data["book_value"],
                        data["market_cap"],        data["last_updated"],
                        data["source"],
                    ),
                )
                con.commit()
            updated += 1

        time.sleep(sleep_sec)

    _cb(100, f"Refresh complete — {updated} updated, {failed} failed")
    log.info("Fundamentals refresh done: %d updated, %d failed out of %d", updated, failed, total)
    return updated, failed
