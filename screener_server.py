"""
Positional Screener Server — adapted from server.py for Replit/Streamlit embedding.
Runs Flask on port 3001 (0.0.0.0) as a background thread.
Logic is 100% unchanged from the original server.py.
"""

import os, sys, time, threading, logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import yfinance as yf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────
PORT = 3001
HOST = "0.0.0.0"

DATA_DIR    = Path(__file__).parent / "data"
SYMBOLS_CSV = DATA_DIR / "nse500_symbols.csv"
FUND_CSV    = DATA_DIR / "fundamentals.csv"

SECTOR_INDEX_MAP = {
    "Financial Services": ["^CNXBANK", "^CNXFIN", "^CNXPSUBANK"],
    "IT":                 ["^CNXIT"],
    "Auto":               ["^CNXAUTO"],
    "Defence":            ["^CNXDEFENCE"],
    "Chemicals":          ["^CEX"],
    "Healthcare":         ["^CNXPHARMA", "^NIFTY_HEALTHCARE"],
    "Pharma":             ["^CNXPHARMA"],
    "FMCG":               ["^CNXFMCG"],
    "Energy":             ["^CNXENERGY"],
    "Metals":             ["^CNXMETAL"],
    "Real Estate":        ["^CNXREALTY"],
    "Building Materials": ["^CNXREALTY"],
    "Telecom":            ["^CNXMEDIA"],
    "Media":              ["^CNXMEDIA"],
    "Logistics":          ["^CNXSERVICE"],
    "Services":           ["^CNXSERVICE"],
    "Aviation":           ["^CNXSERVICE"],
    "Infrastructure":     ["^CNXINFRA"],
    "Engineering":        ["^CNXINFRA"],
    "Retail":             ["^CNXCONSUM"],
    "Consumption":        ["^CNXCONSUM"],
    "New Age Tech":       ["^CNXIT"],
}

# ── Shared state ──────────────────────────────────────────────────
scan = {
    "active":    False,
    "progress":  0,
    "status":    "Idle - click Refresh Scan to start",
    "results":   {},
    "scan_time": None,
    "total_symbols": 0,
}

# ── Load CSV data ─────────────────────────────────────────────────
def load_symbols():
    if not SYMBOLS_CSV.exists():
        log.error("nse500_symbols.csv not found at %s", SYMBOLS_CSV)
        return []
    df = pd.read_csv(SYMBOLS_CSV)
    df = df.drop_duplicates(subset=["symbol"])
    df["angel_token"] = pd.to_numeric(df.get("angel_token", 0), errors="coerce").fillna(0).astype(int)
    symbols = df.to_dict("records")
    log.info("Symbols loaded: %d", len(symbols))
    return symbols

def load_fundamentals():
    if not FUND_CSV.exists():
        log.warning("fundamentals.csv not found - all stocks get neutral fundamental score")
        return {}
    df = pd.read_csv(FUND_CSV)
    fund = {}
    for _, row in df.iterrows():
        sym = str(row["symbol"])
        fund[sym] = {
            "rev_growth_score":  int(row.get("rev_growth_score", 3)),
            "pat_growth_score":  int(row.get("pat_growth_score", 3)),
            "roe_score":         int(row.get("roe_score", 3)),
            "de_score":          int(row.get("de_score", 2)),
            "promoter_score":    int(row.get("promoter_score", 2)),
            "pe":          float(row.get("pe", 0) or 0),
            "pb":          float(row.get("pb", 0) or 0),
            "roe_pct":     float(row.get("roe_pct", 0) or 0),
            "de_ratio":    float(row.get("de_ratio", 0) or 0),
            "rev_growth_pct": float(row.get("rev_growth_pct", 0) or 0),
            "pat_growth_pct": float(row.get("pat_growth_pct", 0) or 0),
            "promoter_pct":   float(row.get("promoter_pct", 0) or 0),
            "last_updated":   str(row.get("last_updated", "")),
            "source":         str(row.get("source", "cached")),
        }
    log.info("Fundamentals loaded: %d symbols", len(fund))
    return fund

SYMBOLS      = load_symbols()
FUNDAMENTALS = load_fundamentals()
scan["total_symbols"] = len(SYMBOLS)

# ── Flask app ─────────────────────────────────────────────────────
app = Flask(__name__, static_folder="public", static_url_path="")
app.secret_key = "screener_secret_replit"
CORS(app, origins="*", supports_credentials=True)

# ── yfinance data fetchers ────────────────────────────────────────
def fetch_stock_info(symbol, max_retries=2):
    yf_sym = f"{symbol}.NS"
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(yf_sym)
            info = ticker.info
            if not info:
                time.sleep(0.3)
                continue

            cmp  = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0
            prev = info.get("previousClose") or info.get("regularMarketPreviousClose") or cmp
            change = 0
            if cmp and prev and prev > 0:
                change = ((cmp - prev) / prev) * 100

            return {
                "cmp":     float(cmp) if cmp else 0,
                "change":  round(change, 2),
                "yr_high": float(info.get("fiftyTwoWeekHigh", 0) or 0),
                "yr_low":  float(info.get("fiftyTwoWeekLow", 0) or 0),
                "volume":  int(info.get("regularMarketVolume", 0) or 0),
            }
        except Exception as e:
            log.debug("Quote fetch error for %s (attempt %d): %s", symbol, attempt+1, e)
            time.sleep(0.5)
    return None

def fetch_historical(symbol, days=270, max_retries=2):
    yf_sym = f"{symbol}.NS"
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(yf_sym)
            hist = ticker.history(period="1y", interval="1d", auto_adjust=True)

            if hist.empty or len(hist) < 20:
                time.sleep(0.3)
                continue

            rows = []
            for idx, row in hist.iterrows():
                if pd.isna(row["Close"]):
                    continue
                dt_str = idx.strftime("%Y-%m-%d %H:%M")
                rows.append([
                    dt_str,
                    float(row["Open"])   if not pd.isna(row["Open"])   else float(row["Close"]),
                    float(row["High"])   if not pd.isna(row["High"])   else float(row["Close"]),
                    float(row["Low"])    if not pd.isna(row["Low"])    else float(row["Close"]),
                    float(row["Close"]),
                    int(row["Volume"])   if not pd.isna(row["Volume"]) else 0,
                ])
            return rows
        except Exception as e:
            log.debug("Historical fetch error for %s (attempt %d): %s", symbol, attempt+1, e)
            time.sleep(0.5)
    return []

def fetch_index_return(index_sym, period="1y"):
    try:
        ticker = yf.Ticker(index_sym)
        hist = ticker.history(period=period, interval="1d", auto_adjust=True)
        if len(hist) < 10:
            return None
        old_close = float(hist["Close"].iloc[0])
        new_close = float(hist["Close"].iloc[-1])
        if old_close <= 0:
            return None
        return round((new_close - old_close) / old_close * 100, 2)
    except Exception as e:
        log.debug("Index fetch failed for %s: %s", index_sym, e)
        return None

def fetch_nifty_3m():
    try:
        ticker = yf.Ticker("^CRSLDX")
        hist = ticker.history(period="3mo", interval="1d", auto_adjust=True)
        if len(hist) < 10:
            log.warning("Nifty 500 (^CRSLDX): insufficient data, using fallback 4.5%")
            return 4.5
        old_close = float(hist["Close"].iloc[0])
        new_close = float(hist["Close"].iloc[-1])
        if old_close <= 0:
            log.warning("Nifty 500 (^CRSLDX): invalid close, using fallback 4.5%")
            return 4.5
        ret = round((new_close - old_close) / old_close * 100, 2)
        log.info("Nifty 500 3M return: %.2f%%", ret)
        return ret
    except Exception as e:
        log.warning("Nifty 500 (^CRSLDX) fetch failed: %s — using fallback 4.5%%", e)
        return 4.5

# ── Technical indicators ──────────────────────────────────────────
def calc_rsi(closes, period=14):
    if len(closes) < period + 2:
        return None
    arr    = np.array(closes, dtype=float)
    deltas = np.diff(arr)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    ag = np.mean(gains[:period])
    al = np.mean(losses[:period])
    for i in range(period, len(gains)):
        ag = (ag * (period-1) + gains[i])  / period
        al = (al * (period-1) + losses[i]) / period
    if al == 0:
        return 100.0
    return round(100 - 100 / (1 + ag/al), 2)

def calc_sma(closes, period):
    if len(closes) < period:
        return None
    return round(float(np.mean(closes[-period:])), 2)

def calc_atr(highs, lows, closes, period=14):
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return float(closes[-1]) * 0.02 if closes and len(closes) > 0 else 0
    trs = [max(highs[-period+i] - lows[-period+i],
               abs(highs[-period+i] - closes[-period+i-1]),
               abs(lows[-period+i]  - closes[-period+i-1]))
           for i in range(period)]
    return round(float(np.mean(trs)), 4)

def check_hh_hl(closes):
    if len(closes) < 40:
        return False
    seg    = closes[-40:]
    weekly = [seg[i] for i in range(0, len(seg), 5)]
    if len(weekly) < 4:
        return False
    hh = weekly[-1] > weekly[-2] and weekly[-2] > weekly[-3]
    hl = min(weekly[-2:]) > min(weekly[-4:-2])
    return hh and hl

def calc_vol_ratio(closes, volumes):
    n = min(20, len(closes) - 1)
    if n < 5 or len(volumes) < n + 1:
        return 1.0
    up_v, dn_v = [], []
    for i in range(len(closes)-n, len(closes)):
        if i < len(volumes):
            (up_v if closes[i] > closes[i-1] else dn_v).append(volumes[i])
    avg_up = float(np.mean(up_v)) if up_v else 0
    avg_dn = float(np.mean(dn_v)) if dn_v else 1
    return round(avg_up / avg_dn, 3) if avg_dn > 0 else 1.0

# ── Scoring ───────────────────────────────────────────────────────
def score_trend(cmp, sma50, sma200, hh_hl):
    s, det = 0, []
    if sma200:
        if cmp > sma200:  s += 10; det.append(f"Above 200 DMA Rs{sma200:,.0f} -> +10")
        else:             det.append(f"Below 200 DMA Rs{sma200:,.0f} -> +0")
    if sma50 and sma200:
        if sma50 > sma200:           s += 8; det.append("Golden cross (50>200 DMA) -> +8")
        elif sma50 > sma200 * 0.97:  s += 4; det.append("50 DMA approaching 200 -> +4")
        else:                         det.append("50 DMA below 200 DMA -> +0")
    if hh_hl:  s += 7; det.append("Higher highs + higher lows -> +7")
    else:      det.append("No clear HH/HL structure -> +0")
    return min(s, 25), det

def score_momentum(rsi, rel_str, vol_ratio):
    s, det = 0, []
    if rsi is not None:
        if 50 <= rsi <= 72:    s += 8; det.append(f"RSI {rsi} - ideal trending zone -> +8")
        elif 72 < rsi <= 80:   s += 4; det.append(f"RSI {rsi} - slightly overbought -> +4")
        elif rsi > 80:         det.append(f"RSI {rsi} - overbought -> +0")
        else:                  det.append(f"RSI {rsi} - below 50, weak -> +0")
    if rel_str is not None:
        if rel_str > 0:  s += 7; det.append(f"Outperforming Nifty 500 +{rel_str:.1f}% -> +7")
        else:            det.append(f"Underperforming Nifty 500 {rel_str:.1f}% -> +0")
    if vol_ratio is not None:
        if vol_ratio > 1.15:   s += 5; det.append(f"Volume ratio {vol_ratio}x - buying pressure -> +5")
        elif vol_ratio > 0.9:  s += 2; det.append(f"Volume ratio {vol_ratio}x - neutral -> +2")
        else:                  det.append(f"Volume ratio {vol_ratio}x - selling -> +0")
    return min(s, 20), det

def score_fundamental(symbol):
    fd = FUNDAMENTALS.get(symbol)
    if not fd:
        return 13, [
            "Fundamental data not in cache - run update_fundamentals.py",
            "Neutral scores applied: 3+3+3+2+2 = 13/25"
        ], {"pe":0,"pb":0,"roe_pct":0,"de_ratio":0,"rev_growth_pct":0,"pat_growth_pct":0,"promoter_pct":0,"source":"not-cached"}
    s = (fd["rev_growth_score"] + fd["pat_growth_score"] +
         fd["roe_score"] + fd["de_score"] + fd["promoter_score"])
    det = [
        f"Revenue growth {fd['rev_growth_pct']:+.1f}% -> {fd['rev_growth_score']}/7",
        f"PAT growth {fd['pat_growth_pct']:+.1f}% -> {fd['pat_growth_score']}/6",
        f"ROE {fd['roe_pct']:.1f}% -> {fd['roe_score']}/6",
        f"D/E {fd['de_ratio']:.2f} -> {fd['de_score']}/3",
        f"Promoter {fd['promoter_pct']:.0f}% -> {fd['promoter_score']}/3",
        f"Updated: {fd['last_updated']} | Source: {fd['source']}",
    ]
    return min(s, 25), det, fd

def score_rr(cmp, sma50, sma200, atr):
    s, det = 0, []
    candidates = [v for v in [sma50, sma200] if v]
    support = max(candidates) if candidates else cmp * 0.92
    dist_pct = (cmp - support) / support * 100 if support else 0
    if   dist_pct <= 5:   s += 7; det.append(f"Near support Rs{support:,.0f} ({dist_pct:.1f}% away) -> +7")
    elif dist_pct <= 10:  s += 4; det.append(f"Moderate from support ({dist_pct:.1f}%) -> +4")
    else:                 s += 1; det.append(f"Extended from support ({dist_pct:.1f}%) -> +1")
    if atr and atr > 0 and cmp > 0:
        sl_pct_raw = (atr * 2 / cmp) * 100
        sl_pct     = min(sl_pct_raw, 12) / 100
        sl_price   = round(cmp * (1 - sl_pct), 2)
        risk       = cmp - sl_price
        tgt_price  = round(cmp + risk * 2.5, 2)
        tgt_pct    = (tgt_price - cmp) / cmp * 100
        rr_ratio   = 2.5 if risk > 0 else 0
        if   rr_ratio >= 2.5 and tgt_pct >= 20:
            s += 8; det.append(f"R:R {rr_ratio:.1f}:1 (SL {sl_pct*100:.1f}%, Tgt {tgt_pct:.1f}%) -> +8")
        elif rr_ratio >= 2.0 and tgt_pct >= 15:
            s += 5; det.append(f"R:R {rr_ratio:.1f}:1 (SL {sl_pct*100:.1f}%, Tgt {tgt_pct:.1f}%) -> +5")
        else:
            s += 2; det.append(f"R:R {rr_ratio:.1f}:1 (Tgt {tgt_pct:.1f}%) -> +2")
    return min(s, 15), det

def get_signal(total):
    if total >= 80: return "STRONG BUY"
    if total >= 70: return "BUY"
    if total >= 60: return "WATCH"
    return "SKIP"

# ── Sector tailwinds ──────────────────────────────────────────────
def fetch_sector_tailwinds():
    index_perf = {}
    all_indices = set()
    for idxs in SECTOR_INDEX_MAP.values():
        all_indices.update(idxs)

    for idx_sym in all_indices:
        ret = fetch_index_return(idx_sym, period="1y")
        if ret is not None:
            index_perf[idx_sym] = ret
            log.info("Index %s 1Y return: %.1f%%", idx_sym, ret)
        else:
            log.warning("Index %s: no data", idx_sym)
        time.sleep(0.3)

    def score(index_names):
        for n in index_names:
            if n in index_perf:
                r = index_perf[n]
                if r >= 40: return 15
                if r >= 25: return 13
                if r >= 15: return 11
                if r >=  5: return 9
                if r >=  0: return 7
                return 5
        return 9

    return {s: score(idxs) for s, idxs in SECTOR_INDEX_MAP.items()}

# ── Background scan ───────────────────────────────────────────────
def run_scan():
    scan["active"]   = True
    scan["progress"] = 0
    scan["status"]   = "Loading symbols and fundamentals..."
    scan["results"]  = {}

    failed_symbols   = []
    skipped_symbols  = []
    no_data_symbols  = []

    try:
        symbols = load_symbols()
        fundamentals_fresh = load_fundamentals()
        global FUNDAMENTALS
        FUNDAMENTALS = fundamentals_fresh

        if not symbols:
            raise RuntimeError("No symbols loaded - check data/nse500_symbols.csv")

        total_syms = len(symbols)
        scan["total_symbols"] = total_syms
        scan["progress"] = 2
        scan["status"]   = "Fetching sector index performance..."

        sector_scores = fetch_sector_tailwinds()

        scan["progress"] = 5
        scan["status"]   = f"Fetching live quotes for {total_syms} stocks..."

        live_quotes = {}
        for idx, row in enumerate(symbols):
            sym = row["symbol"]
            q = fetch_stock_info(sym)
            if q and q["cmp"] > 0:
                live_quotes[sym] = q
            else:
                no_data_symbols.append(sym)

            if idx % 10 == 0:
                pct = 5 + int((idx / total_syms) * 15)
                scan["progress"] = min(pct, 20)
                scan["status"] = f"Fetched quotes {idx+1}/{total_syms} ({len(live_quotes)} OK, {len(no_data_symbols)} no data)..."

            time.sleep(0.15)

        log.info("Live quotes fetched: %d / %d symbols (%d no data)",
                 len(live_quotes), total_syms, len(no_data_symbols))

        if len(live_quotes) == 0:
            log.error("CRITICAL: No quotes fetched. Check internet connection.")
            scan["status"] = "Scan failed: Could not fetch any data from Yahoo Finance. Check your internet connection."
            scan["active"] = False
            return

        nifty_3m = fetch_nifty_3m()

        for idx, row in enumerate(symbols):
            sym    = row["symbol"]
            sector = row.get("sector", "Unknown")
            cap    = row.get("cap", "")
            name   = row.get("name", sym)

            pct = 20 + int((idx / total_syms) * 75)
            scan["progress"] = min(pct, 95)
            scan["status"]   = f"Analysing {sym} ({idx+1}/{total_syms})..."

            q   = live_quotes.get(sym, {})
            cmp = q.get("cmp", 0)
            if cmp <= 0:
                skipped_symbols.append(sym)
                continue

            try:
                hist_rows = fetch_historical(sym, days=270)

                if not hist_rows or len(hist_rows) < 50:
                    log.warning("Insufficient historical data for %s (%d rows), skipping",
                                sym, len(hist_rows) if hist_rows else 0)
                    failed_symbols.append(sym)
                    continue

                closes  = [float(r[4]) for r in hist_rows if r[4] is not None and r[4] > 0]
                volumes = [int(r[5])   for r in hist_rows if r[5] is not None and r[5] >= 0]
                highs   = [float(r[2]) for r in hist_rows if r[2] is not None and r[2] > 0]
                lows    = [float(r[3]) for r in hist_rows if r[3] is not None and r[3] > 0]

                n = len(closes)
                if n < 50:
                    log.warning("Not enough valid close prices for %s (%d), skipping", sym, n)
                    failed_symbols.append(sym)
                    continue

                min_len = min(n, len(volumes), len(highs), len(lows))
                closes  = closes[:min_len]
                volumes = volumes[:min_len]
                highs   = highs[:min_len]
                lows    = lows[:min_len]

                sma50     = calc_sma(closes, 50)
                sma200    = calc_sma(closes, 200)
                rsi       = calc_rsi(closes)
                hh_hl     = check_hh_hl(closes)
                vol_ratio = calc_vol_ratio(closes, volumes)
                atr       = calc_atr(highs, lows, closes)

                rel_str = None
                if n >= 63:
                    stk_3m  = (closes[-1] - closes[-63]) / closes[-63] * 100
                    rel_str = round(stk_3m - nifty_3m, 2)

                t_score, t_det        = score_trend(cmp, sma50, sma200, hh_hl)
                m_score, m_det        = score_momentum(rsi, rel_str, vol_ratio)
                f_score, f_det, f_raw = score_fundamental(sym)
                s_score               = sector_scores.get(sector, 9)
                r_score, r_det        = score_rr(cmp, sma50, sma200, atr)

                total_score = t_score + m_score + f_score + s_score + r_score

                sl_pct    = min((atr * 2 / cmp) * 100, 12) / 100 if atr else 0.10
                sl_price  = round(cmp * (1 - sl_pct), 2)
                tgt_price = round(cmp + (cmp - sl_price) * 2.5, 2)

                scan["results"][sym] = {
                    "symbol":      sym,
                    "name":        name,
                    "sector":      sector,
                    "cap":         cap,
                    "cmp":         round(cmp, 2),
                    "changePct":   round(q.get("change", 0), 2),
                    "yearHigh":    round(q.get("yr_high", 0), 2),
                    "yearLow":     round(q.get("yr_low", 0),  2),
                    "volume":      q.get("volume", 0),
                    "sma50":       sma50,
                    "sma200":      sma200,
                    "rsi":         rsi,
                    "volRatio":    vol_ratio,
                    "trendScore":  t_score,
                    "momScore":    m_score,
                    "fundScore":   f_score,
                    "secScore":    s_score,
                    "rrScore":     r_score,
                    "total":       total_score,
                    "signal":      get_signal(total_score),
                    "slPrice":     sl_price,
                    "tgtPrice":    tgt_price,
                    "pe":          f_raw.get("pe", 0),
                    "pb":          f_raw.get("pb", 0),
                    "roe":         f_raw.get("roe_pct", 0),
                    "de":          f_raw.get("de_ratio", 0),
                    "revGrowth":   f_raw.get("rev_growth_pct", 0),
                    "promoter":    f_raw.get("promoter_pct", 0),
                    "fundUpdated": f_raw.get("last_updated", ""),
                    "trendDet":    t_det,
                    "momDet":      m_det,
                    "fundDet":     f_det,
                    "rrDet":       r_det,
                    "dataQuality": "full" if n >= 200 else "partial" if n >= 50 else "limited",
                    "scannedAt":   datetime.now().strftime("%d %b %Y %H:%M"),
                }

            except Exception as e:
                log.warning("Analysis error for %s: %s", sym, e)
                failed_symbols.append(sym)

            time.sleep(0.05)

        n_scored = len(scan["results"])
        scan["progress"] = 100
        scan["status"]   = (f"Scan complete - {n_scored} scored, {len(skipped_symbols)} skipped, "
                            f"{len(failed_symbols)} failed, {len(no_data_symbols)} no data")
        scan["scan_time"] = datetime.now().strftime("%d %b %Y %H:%M IST")
        log.info("Scan done - %d/%d scored, %d skipped, %d failed, %d no data",
                 n_scored, total_syms, len(skipped_symbols), len(failed_symbols), len(no_data_symbols))

        if n_scored == 0:
            scan["status"] = "Scan failed: No stocks could be scored. Check internet connection and try again."

    except Exception as e:
        log.error("Scan error: %s", e, exc_info=True)
        scan["status"] = f"Scan failed: {e}"
    finally:
        scan["active"] = False

# ── API routes ────────────────────────────────────────────────────
@app.route("/api/scan", methods=["POST"])
def start_scan():
    if scan["active"]:
        return jsonify({"ok": False, "msg": "Scan already running"})
    t = threading.Thread(target=run_scan, daemon=True)
    t.start()
    return jsonify({"ok": True})

@app.route("/api/scan/status")
def scan_status():
    return jsonify({
        "ok":       True,
        "active":   scan["active"],
        "progress": scan["progress"],
        "status":   scan["status"],
        "ready":    len(scan["results"]),
        "total":    scan["total_symbols"],
        "scanTime": scan["scan_time"],
    })

@app.route("/api/results")
def results():
    data = sorted(scan["results"].values(), key=lambda x: x["total"], reverse=True)
    return jsonify({"ok": True, "data": data, "scanTime": scan["scan_time"],
                    "total": scan["total_symbols"]})

@app.route("/api/stock/<symbol>")
def stock_detail(symbol):
    s = scan["results"].get(symbol.upper())
    if not s:
        return jsonify({"ok": False, "msg": "Not yet scanned"}), 404
    return jsonify({"ok": True, "data": s})

@app.route("/api/fundamentals/reload", methods=["POST"])
def reload_fundamentals():
    global FUNDAMENTALS
    FUNDAMENTALS = load_fundamentals()
    return jsonify({"ok": True, "loaded": len(FUNDAMENTALS),
                    "msg": f"Reloaded {len(FUNDAMENTALS)} fundamental records from CSV"})

@app.route("/api/fundamentals/status")
def fund_status():
    total   = len(SYMBOLS)
    cached  = len(FUNDAMENTALS)
    missing = [s["symbol"] for s in SYMBOLS if s["symbol"] not in FUNDAMENTALS]
    dates   = [v.get("last_updated","") for v in FUNDAMENTALS.values() if v.get("last_updated")]
    oldest  = min(dates) if dates else "never"
    newest  = max(dates) if dates else "never"
    return jsonify({
        "ok":      True,
        "total":   total,
        "cached":  cached,
        "missing": len(missing),
        "oldest":  oldest,
        "newest":  newest,
        "missing_symbols": missing[:20],
    })

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path and (Path(app.static_folder) / path).exists():
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ── Direct scan (no Flask) — called from Streamlit ───────────────
def run_scan_direct(progress_cb=None):
    """
    Run the full NSE 500 scan synchronously.
    progress_cb(pct: int, status: str) is called periodically.
    Returns list of result dicts (same structure as scan["results"].values()).
    """
    def _cb(pct, status):
        if progress_cb:
            try:
                progress_cb(pct, status)
            except Exception:
                pass

    results       = {}
    failed        = []
    skipped       = []
    no_data       = []

    _cb(0, "Loading symbols and fundamentals...")
    symbols = load_symbols()
    fundamentals_fresh = load_fundamentals()
    global FUNDAMENTALS
    FUNDAMENTALS = fundamentals_fresh

    if not symbols:
        _cb(100, "No symbols loaded — check data/nse500_symbols.csv")
        return []

    total_syms = len(symbols)

    _cb(2, "Fetching sector index performance...")
    sector_scores = fetch_sector_tailwinds()

    _cb(5, f"Fetching live quotes for {total_syms} stocks...")
    live_quotes = {}
    for idx, row in enumerate(symbols):
        sym = row["symbol"]
        q   = fetch_stock_info(sym)
        if q and q["cmp"] > 0:
            live_quotes[sym] = q
        else:
            no_data.append(sym)
        if idx % 10 == 0:
            pct = 5 + int((idx / total_syms) * 15)
            _cb(min(pct, 20),
                f"Fetching quotes {idx+1}/{total_syms} "
                f"({len(live_quotes)} OK, {len(no_data)} no data)...")
        time.sleep(0.15)

    if not live_quotes:
        _cb(100, "Scan failed: no quotes fetched — check internet connection.")
        return []

    nifty_3m = fetch_nifty_3m()

    for idx, row in enumerate(symbols):
        sym    = row["symbol"]
        sector = row.get("sector", "Unknown")
        cap    = row.get("cap", "")
        name   = row.get("name", sym)

        pct = 20 + int((idx / total_syms) * 75)
        _cb(min(pct, 95), f"Analysing {sym} ({idx+1}/{total_syms})...")

        q   = live_quotes.get(sym, {})
        cmp = q.get("cmp", 0)
        if cmp <= 0:
            skipped.append(sym)
            continue

        try:
            hist_rows = fetch_historical(sym, days=270)
            if not hist_rows or len(hist_rows) < 50:
                failed.append(sym)
                continue

            closes  = [float(r[4]) for r in hist_rows if r[4] is not None and r[4] > 0]
            volumes = [int(r[5])   for r in hist_rows if r[5] is not None and r[5] >= 0]
            highs   = [float(r[2]) for r in hist_rows if r[2] is not None and r[2] > 0]
            lows    = [float(r[3]) for r in hist_rows if r[3] is not None and r[3] > 0]

            n = len(closes)
            if n < 50:
                failed.append(sym)
                continue

            min_len = min(n, len(volumes), len(highs), len(lows))
            closes  = closes[:min_len]
            volumes = volumes[:min_len]
            highs   = highs[:min_len]
            lows    = lows[:min_len]

            sma50     = calc_sma(closes, 50)
            sma200    = calc_sma(closes, 200)
            rsi       = calc_rsi(closes)
            hh_hl     = check_hh_hl(closes)
            vol_ratio = calc_vol_ratio(closes, volumes)
            atr       = calc_atr(highs, lows, closes)

            rel_str = None
            if n >= 63:
                stk_3m  = (closes[-1] - closes[-63]) / closes[-63] * 100
                rel_str = round(stk_3m - nifty_3m, 2)

            t_score, t_det        = score_trend(cmp, sma50, sma200, hh_hl)
            m_score, m_det        = score_momentum(rsi, rel_str, vol_ratio)
            f_score, f_det, f_raw = score_fundamental(sym)
            s_score               = sector_scores.get(sector, 9)
            r_score, r_det        = score_rr(cmp, sma50, sma200, atr)

            total_score = t_score + m_score + f_score + s_score + r_score

            sl_pct    = min((atr * 2 / cmp) * 100, 12) / 100 if atr else 0.10
            sl_price  = round(cmp * (1 - sl_pct), 2)
            tgt_price = round(cmp + (cmp - sl_price) * 2.5, 2)

            results[sym] = {
                "symbol":      sym,
                "name":        name,
                "sector":      sector,
                "cap":         cap,
                "cmp":         round(cmp, 2),
                "changePct":   round(q.get("change", 0), 2),
                "yearHigh":    round(q.get("yr_high", 0), 2),
                "yearLow":     round(q.get("yr_low", 0),  2),
                "volume":      q.get("volume", 0),
                "sma50":       sma50,
                "sma200":      sma200,
                "rsi":         rsi,
                "volRatio":    vol_ratio,
                "trendScore":  t_score,
                "momScore":    m_score,
                "fundScore":   f_score,
                "secScore":    s_score,
                "rrScore":     r_score,
                "total":       total_score,
                "signal":      get_signal(total_score),
                "slPrice":     sl_price,
                "tgtPrice":    tgt_price,
                "pe":          f_raw.get("pe", 0),
                "pb":          f_raw.get("pb", 0),
                "roe":         f_raw.get("roe_pct", 0),
                "de":          f_raw.get("de_ratio", 0),
                "revGrowth":   f_raw.get("rev_growth_pct", 0),
                "promoter":    f_raw.get("promoter_pct", 0),
                "fundUpdated": f_raw.get("last_updated", ""),
                "trendDet":    t_det,
                "momDet":      m_det,
                "fundDet":     f_det,
                "rrDet":       r_det,
                "dataQuality": "full" if n >= 200 else "partial" if n >= 50 else "limited",
                "scannedAt":   datetime.now().strftime("%d %b %Y %H:%M"),
            }
        except Exception as e:
            log.warning("Analysis error for %s: %s", sym, e)
            failed.append(sym)

        time.sleep(0.05)

    n_scored = len(results)
    _cb(100,
        f"Scan complete — {n_scored} scored, {len(skipped)} skipped, "
        f"{len(failed)} failed, {len(no_data)} no data")
    return sorted(results.values(), key=lambda x: x["total"], reverse=True)


# ── Server start helper ───────────────────────────────────────────
_server_started = False
_server_lock    = threading.Lock()

def start_server():
    """Start Flask in a background daemon thread. Safe to call multiple times."""
    global _server_started
    with _server_lock:
        if _server_started:
            return
        _server_started = True

    def _run():
        import logging as _lg
        _lg.getLogger("werkzeug").setLevel(_lg.ERROR)
        app.run(host=HOST, port=PORT, debug=False, threaded=True, use_reloader=False)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(1.5)
    log.info("Screener Flask server started on port %d", PORT)
