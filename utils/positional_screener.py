"""
Positional Screener for NSE 500 stocks.
Ported from server.py (Flask) to Streamlit.
Scoring: Trend(25) + Momentum(20) + Fundamental(25) + Sector(15) + Risk:Reward(15) = 100
"""

import time
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

log = logging.getLogger(__name__)

DATA_DIR    = Path(__file__).parent.parent / "data"
SYMBOLS_CSV = DATA_DIR / "nse500_symbols.csv"
FUND_CSV    = DATA_DIR / "fundamentals.csv"

SECTOR_INDEX_MAP = {
    "Financial Services": ["^CNXBANK", "^CNXFIN", "^CNXPSUBANK"],
    "IT":                 ["^CNXIT"],
    "Auto":               ["^CNXAUTO"],
    "Defence":            ["^CNXDEFENCE"],
    "Engineering":        ["^CNXINFRA", "^CNXCONSUM"],
    "Chemicals":          ["^CNXPHARMA"],
    "Healthcare":         ["^CNXPHARMA", "^CNXHEALTH"],
    "FMCG":               ["^CNXFMCG"],
    "Retail":             ["^CNXCONSUM"],
    "Energy":             ["^CNXENERGY"],
    "Metals":             ["^CNXMETAL"],
    "Building Materials": ["^CNXREALTY"],
    "Real Estate":        ["^CNXREALTY"],
    "Telecom":            ["^CNXMEDIA"],
    "Logistics":          ["^CNXSERVICE"],
    "Aviation":           ["^CNXSERVICE"],
    "New Age Tech":       ["^CNXIT"],
}


# ── Load data ─────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_symbols():
    if not SYMBOLS_CSV.exists():
        return []
    df = pd.read_csv(SYMBOLS_CSV)
    df = df.drop_duplicates(subset=["symbol"])
    return df.to_dict("records")


@st.cache_data(ttl=3600)
def load_fundamentals():
    if not FUND_CSV.exists():
        return {}
    df = pd.read_csv(FUND_CSV)
    fund = {}
    for _, row in df.iterrows():
        sym = str(row["symbol"])
        fund[sym] = {
            "rev_growth_score": int(row.get("rev_growth_score", 3)),
            "pat_growth_score": int(row.get("pat_growth_score", 3)),
            "roe_score":        int(row.get("roe_score", 3)),
            "de_score":         int(row.get("de_score", 2)),
            "promoter_score":   int(row.get("promoter_score", 2)),
            "pe":               float(row.get("pe", 0) or 0),
            "pb":               float(row.get("pb", 0) or 0),
            "roe_pct":          float(row.get("roe_pct", 0) or 0),
            "de_ratio":         float(row.get("de_ratio", 0) or 0),
            "rev_growth_pct":   float(row.get("rev_growth_pct", 0) or 0),
            "pat_growth_pct":   float(row.get("pat_growth_pct", 0) or 0),
            "promoter_pct":     float(row.get("promoter_pct", 0) or 0),
            "last_updated":     str(row.get("last_updated", "")),
            "source":           str(row.get("source", "cached")),
        }
    return fund


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
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0:
        return 100.0
    return round(100 - 100 / (1 + ag / al), 2)


def calc_sma(closes, period):
    if len(closes) < period:
        return None
    return round(float(np.mean(closes[-period:])), 2)


def calc_atr(highs, lows, closes, period=14):
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return float(closes[-1]) * 0.02 if closes and len(closes) > 0 else 0
    trs = [
        max(
            highs[-period + i] - lows[-period + i],
            abs(highs[-period + i] - closes[-period + i - 1]),
            abs(lows[-period + i]  - closes[-period + i - 1]),
        )
        for i in range(period)
    ]
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
    return hh or hl


def calc_vol_ratio(closes, volumes):
    n = min(20, len(closes) - 1)
    if n < 5 or len(volumes) < n + 1:
        return 1.0
    up_v, dn_v = [], []
    for i in range(len(closes) - n, len(closes)):
        if i < len(volumes):
            (up_v if closes[i] > closes[i - 1] else dn_v).append(volumes[i])
    avg_up = float(np.mean(up_v)) if up_v else 0
    avg_dn = float(np.mean(dn_v)) if dn_v else 1
    return round(avg_up / avg_dn, 3) if avg_dn > 0 else 1.0


# ── Scoring ───────────────────────────────────────────────────────

def score_trend(cmp, sma50, sma200, hh_hl):
    s, det = 0, []
    if sma200:
        if cmp > sma200:
            s += 10; det.append(f"Above 200 DMA ₹{sma200:,.0f} → +10")
        else:
            det.append(f"Below 200 DMA ₹{sma200:,.0f} → +0")
    if sma50 and sma200:
        if sma50 > sma200:
            s += 8; det.append("Golden cross (50>200 DMA) → +8")
        elif sma50 > sma200 * 0.97:
            s += 4; det.append("50 DMA approaching 200 → +4")
        else:
            det.append("50 DMA below 200 DMA → +0")
    if hh_hl:
        s += 7; det.append("Higher highs + higher lows → +7")
    else:
        det.append("No clear HH/HL structure → +0")
    return min(s, 25), det


def score_momentum(rsi, rel_str, vol_ratio):
    s, det = 0, []
    if rsi is not None:
        if 50 <= rsi <= 72:
            s += 8; det.append(f"RSI {rsi} - ideal trending zone → +8")
        elif 72 < rsi <= 80:
            s += 4; det.append(f"RSI {rsi} - slightly overbought → +4")
        elif rsi > 80:
            det.append(f"RSI {rsi} - overbought → +0")
        else:
            det.append(f"RSI {rsi} - below 50, weak → +0")
    if rel_str is not None:
        if rel_str > 0:
            s += 7; det.append(f"Outperforming Nifty 500 +{rel_str:.1f}% → +7")
        else:
            det.append(f"Underperforming Nifty 500 {rel_str:.1f}% → +0")
    if vol_ratio is not None:
        if vol_ratio > 1.15:
            s += 5; det.append(f"Volume ratio {vol_ratio}x - buying pressure → +5")
        elif vol_ratio > 0.9:
            s += 2; det.append(f"Volume ratio {vol_ratio}x - neutral → +2")
        else:
            det.append(f"Volume ratio {vol_ratio}x - selling → +0")
    return min(s, 20), det


def score_fundamental(symbol, fundamentals):
    fd = fundamentals.get(symbol)
    if not fd:
        return 13, ["Fundamental data not cached - neutral scores applied (13/25)"]
    s = (fd["rev_growth_score"] + fd["pat_growth_score"] +
         fd["roe_score"] + fd["de_score"] + fd["promoter_score"])
    det = [
        f"Revenue growth score: {fd['rev_growth_score']}/7",
        f"PAT growth score:     {fd['pat_growth_score']}/7",
        f"ROE score:            {fd['roe_score']}/6",
        f"D/E score:            {fd['de_score']}/3",
        f"Promoter score:       {fd['promoter_score']}/2",
    ]
    return min(s, 25), det


def score_rr(cmp, sma50, sma200, atr):
    s, det, sl_price, tgt_price = 0, [], None, None
    support = None
    if sma50 and cmp > sma50:
        support = sma50
    elif sma200 and cmp > sma200:
        support = sma200

    if support and atr and atr > 0:
        sl_price  = round(support - atr, 2)
        tgt_price = round(cmp + 2.5 * atr, 2)
        risk      = cmp - sl_price
        reward    = tgt_price - cmp
        rr_ratio  = reward / risk if risk > 0 else 0

        if rr_ratio >= 3:
            s = 15; det.append(f"R:R {rr_ratio:.1f}:1 - excellent → +15")
        elif rr_ratio >= 2:
            s = 12; det.append(f"R:R {rr_ratio:.1f}:1 - good → +12")
        elif rr_ratio >= 1.5:
            s = 8;  det.append(f"R:R {rr_ratio:.1f}:1 - acceptable → +8")
        else:
            s = 4;  det.append(f"R:R {rr_ratio:.1f}:1 - poor → +4")
    else:
        s = 7; det.append("Cannot determine clear support/SL → neutral +7")
    return min(s, 15), det, sl_price, tgt_price


def get_signal(total):
    if total >= 80:
        return "STRONG BUY"
    if total >= 70:
        return "BUY"
    if total >= 60:
        return "WATCH"
    return "SKIP"


# ── Sector tailwinds ──────────────────────────────────────────────

@st.cache_data(ttl=86400)
def fetch_sector_tailwinds():
    index_perf = {}
    all_indices = set()
    for idxs in SECTOR_INDEX_MAP.values():
        all_indices.update(idxs)

    for idx_sym in all_indices:
        try:
            ticker = yf.Ticker(idx_sym)
            hist   = ticker.history(period="1y")
            if hist is not None and len(hist) >= 2:
                ret = ((hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1) * 100
                index_perf[idx_sym] = round(ret, 2)
        except Exception:
            pass
        time.sleep(0.1)

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


# ── Nifty 500 benchmark return ────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_nifty500_return():
    try:
        ticker = yf.Ticker("^CRSLDX")
        hist   = ticker.history(period="1y")
        if hist is not None and len(hist) >= 2:
            return ((hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1) * 100
    except Exception:
        pass
    return 0.0


# ── Score a single stock ──────────────────────────────────────────

def score_stock(row, fundamentals, sector_scores, nifty500_ret):
    sym    = row["symbol"]
    name   = row.get("name", sym)
    sector = row.get("sector", "Unknown")

    try:
        ticker = yf.Ticker(f"{sym}.NS")
        hist   = ticker.history(period="1y")

        if hist is None or len(hist) < 50:
            return None

        closes  = hist["Close"].tolist()
        highs   = hist["High"].tolist()
        lows    = hist["Low"].tolist()
        volumes = hist["Volume"].tolist()

        cmp     = closes[-1]
        sma50   = calc_sma(closes, 50)
        sma200  = calc_sma(closes, 200)
        rsi     = calc_rsi(closes)
        hh_hl   = check_hh_hl(closes)
        vol_ratio = calc_vol_ratio(closes, volumes)
        atr     = calc_atr(highs, lows, closes)

        stock_ret = ((cmp / closes[0]) - 1) * 100
        rel_str   = round(stock_ret - nifty500_ret, 2)

        t_score, t_det = score_trend(cmp, sma50, sma200, hh_hl)
        m_score, m_det = score_momentum(rsi, rel_str, vol_ratio)
        f_score, f_det = score_fundamental(sym, fundamentals)
        s_score        = sector_scores.get(sector, 9)
        r_score, r_det, sl_price, tgt_price = score_rr(cmp, sma50, sma200, atr)

        total = t_score + m_score + f_score + s_score + r_score

        fd = fundamentals.get(sym, {})

        return {
            "symbol":       sym,
            "name":         name,
            "sector":       sector,
            "cmp":          round(cmp, 2),
            "sma50":        sma50,
            "sma200":       sma200,
            "rsi":          rsi,
            "volRatio":     vol_ratio,
            "trendScore":   t_score,
            "momScore":     m_score,
            "fundScore":    f_score,
            "secScore":     s_score,
            "rrScore":      r_score,
            "total":        total,
            "signal":       get_signal(total),
            "slPrice":      sl_price,
            "tgtPrice":     tgt_price,
            "pe":           fd.get("pe", 0),
            "pb":           fd.get("pb", 0),
            "roe":          fd.get("roe_pct", 0),
            "de":           fd.get("de_ratio", 0),
            "revGrowth":    fd.get("rev_growth_pct", 0),
            "promoter":     fd.get("promoter_pct", 0),
            "trendDet":     t_det,
            "momDet":       m_det,
            "fundDet":      f_det,
            "rrDet":        r_det,
            "dataPoints":   len(closes),
        }

    except Exception as e:
        log.debug("Error scoring %s: %s", sym, e)
        return None


# ── Main screener runner ──────────────────────────────────────────

def run_positional_screener(
    min_score: int = 60,
    signal_filter: str = "All",
    sector_filter: str = "All",
    max_stocks: int = 500,
    progress_bar=None,
    status_text=None,
):
    symbols      = load_symbols()
    fundamentals = load_fundamentals()

    if not symbols:
        return pd.DataFrame()

    if status_text:
        status_text.text("Fetching sector tailwinds...")
    sector_scores = fetch_sector_tailwinds()

    if status_text:
        status_text.text("Fetching Nifty 500 benchmark...")
    nifty500_ret = fetch_nifty500_return()

    results    = []
    total_syms = min(len(symbols), max_stocks)

    if status_text:
        status_text.text(f"Scanning {total_syms} stocks...")

    for idx, row in enumerate(symbols[:max_stocks]):
        if progress_bar is not None:
            progress_bar.progress((idx + 1) / total_syms)
        if status_text:
            status_text.text(f"Scanning {idx + 1}/{total_syms}: {row['symbol']}")

        result = score_stock(row, fundamentals, sector_scores, nifty500_ret)
        if result and result["total"] >= min_score:
            results.append(result)

        time.sleep(0.05)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    if signal_filter != "All":
        df = df[df["signal"] == signal_filter]
    if sector_filter != "All":
        df = df[df["sector"] == sector_filter]

    df = df.sort_values("total", ascending=False).reset_index(drop=True)
    return df


def get_signal_badge(signal):
    colors = {
        "STRONG BUY": "#00C853",
        "BUY":        "#69F0AE",
        "WATCH":      "#FFD740",
        "SKIP":       "#FF5252",
    }
    color = colors.get(signal, "#888")
    return f'<span style="background:{color};color:#111;padding:3px 10px;border-radius:12px;font-weight:700;font-size:0.85rem;">{signal}</span>'
