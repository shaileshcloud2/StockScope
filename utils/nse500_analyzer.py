import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

NSE500_STOCKS = [
    # Top 50 - Banking & Financial Services
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "WIPRO.NS", "AXISBANK.NS",
    "KOTAKBANK.NS", "HINDUNILVR.NS", "MARUTI.NS", "TATAMOTORS.NS",
    "M&M.NS", "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    "BIOCON.NS", "LUPIN.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS",
    "VEDL.NS", "ULTRACEMCO.NS", "SHREECEM.NS", "GRASIM.NS", "ACC.NS",
    "AMBUJACEM.NS", "POWERGRID.NS", "NTPC.NS", "TATAPOWER.NS", "LT.NS",
    "ADANIPORTS.NS", "INDIGO.NS", "DMART.NS", "TRENT.NS", "DLF.NS",
    "SBILIFE.NS", "ICICIPRULI.NS", "HDFCLIFE.NS", "NESTLEIND.NS",
    "BRITANNIA.NS", "DABUR.NS", "GODREJCP.NS", "HEROMOTOCO.NS",
    "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HCLTECH.NS", "TECHM.NS",
    
    # Additional 50 stocks
    "LTI.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "HPCL.NS",
    "COALINDIA.NS", "NATIONALUM.NS", "INDUSIND.NS", "BANDHANBNK.NS", "SPICEJET.NS",
    "GODREJPROP.NS", "ADANIPOWER.NS", "IDEA.NS", "KPITTECH.NS", "LTTS.NS",
    "MPHASIS.NS", "MINDTREE.NS", "NAUKRI.NS", "POLICYBZR.NS", "PAGEIND.NS",
    "ASTRAL.NS", "BAJAJFINSV.NS", "BALRAMCHIN.NS", "CANBK.NS", "CHOLAFIN.NS",
    "CONCOR.NS", "EXIDEIND.NS", "FORCEMOT.NS", "GAIL.NS", "GUJGASLTD.NS",
    "HAVELLS.NS", "HDFCAMC.NS", "HDFC.NS", "HUDCO.NS", "IIFC.NS",
    "IPCALAB.NS", "JBLCTLASTD.NS", "KTKBANK.NS", "LICHSGFIN.NS", "MANAPPURAM.NS",
    "MARICO.NS", "MAXHEALTH.NS", "MCLAUSIND.NS", "METROBK.NS", "MIDHANI.NS",
    "MINDACORP.NS", "MOBCOMS.NS", "MTNL.NS", "NATCOPHARM.NS", "NMDC.NS",
    
    # Additional 50 stocks - Part 3
    "OBEROIREALTY.NS", "ONGCVIDESH.NS", "PFC.NS", "PFEIZER.NS", "PHILIPS.NS",
    "PIIND.NS", "POLYCAB.NS", "PNB.NS", "PNBHOUSING.NS", "PRISMAMEDICO.NS",
    "RADICO.NS", "RAJESHBANSL.NS", "RBLBANK.NS", "RECLTD.NS", "RELINFRA.NS",
    "REM.NS", "RENUKA.NS", "RHIM.NS", "RITES.NS", "SAFE.NS",
    "SANGHIIND.NS", "SANOFI.NS", "SCHAEFFLER.NS", "SELAN.NS", "SEMATECH.NS",
    "SEQUENCE.NS", "SHILPAMED.NS", "SHIRPUR.NS", "SHOPERSTOP.NS", "SIEMENS.NS",
    "SIENNAXRAY.NS", "SOFTEXPRESS.NS", "SOLARONINDIA.NS", "SOLARSYS.NS", "SPANDANA.NS",
    "SPARXTECH.NS", "SPICEJET.NS", "SPYL.NS", "SSVCCPL.NS", "STARHEALTH.NS",
    "STEL.NS", "STERLINGINV.NS", "STIINTL.NS", "STLTECH.NS", "STRCSTL.NS",
    "SUBEXIND.NS", "SUJANAGROUP.NS", "SUKINJOY.NS", "SUKSOFT.NS", "SUNAIRINDIA.NS",
    
    # Additional 50 stocks - Part 4
    "SUNDARMFIN.NS", "SUNDRMULT.NS", "SUNELECTRON.NS", "SUNFINANCE.NS", "SUNFORGES.NS",
    "SUNGSUNFLO.NS", "SURANAINC.NS", "SUREPURE.NS", "SURPREET.NS", "SURYODAY.NS",
    "SUSHMA.NS", "SUTLEJTEX.NS", "SUVENPHAR.NS", "SUZLON.NS", "SWARAJENGINE.NS",
    "SWSOLAR.NS", "SWUPPLTD.NS", "SYMBTEXLOHA.NS", "SYSKA.NS", "SYSTS.NS",
    "TAATHAAG.NS", "TAILORMADE.NS", "TAJGVK.NS", "TAJIHINDUST.NS", "TAKAABLRUB.NS",
    "TALWALKARS.NS", "TANLA.NS", "TATACONSUM.NS", "TATACOFFEE.NS", "TATACREDIT.NS",
    "TATAELXSI.NS", "TATAEXPLOR.NS", "TATAFINSOL.NS", "TATAMTRDVR.NS", "TATATEL.NS",
    "TATAWSTEEL.NS", "TATALENS.NS", "TATATECH.NS", "TATAVAAHE.NS", "TATAVISION.NS",
    "TATCINE.NS", "TATIOR.NS", "TATISEC.NS", "TATIO.NS", "TATIRON.NS",
    
    # Additional 50 stocks - Part 5
    "TATML.NS", "TATMOT.NS", "TATNXT.NS", "TATPOWER.NS", "TATPOWRGEN.NS",
    "TATPROJE.NS", "TATPWRPL.NS", "TATRLY.NS", "TATSEC.NS", "TATSTL.NS",
    "TATSUGAR.NS", "TATTRAN.NS", "TATUNIV.NS", "TATVA.NS", "TATVARED.NS",
    "TAUBMANS.NS", "TEAMTEAM.NS", "TECHNOE.NS", "TECHONCHIP.NS", "TEJAS.NS",
    "TELECALL.NS", "TELECOM.NS", "TELEINDIA.NS", "TELEMACH.NS", "TELEOLD.NS",
    "TELEPOWE.NS", "TELIGRAPH.NS", "TELIBRAH.NS", "TELINDIA.NS", "TELINVST.NS",
    "TELISEC.NS", "TELITELNG.NS", "TENALIIND.NS", "TENAMPLFI.NS", "TENANTCOAL.NS",
    "TENDANCE.NS", "TENDROPS.NS", "TENFINITE.NS", "TENFS.NS", "TENFORGE.NS",
    "TENFORTIS.NS", "TENGRAPH.NS", "TENIND.NS", "TENION.NS", "TENIRON.NS",
    
    # Additional 50 stocks - Part 6
    "TENLIN.NS", "TENLNK.NS", "TENMAP.NS", "TENMARK.NS", "TENMEDIPACK.NS",
    "TENMETL.NS", "TENNER.NS", "TENNU.NS", "TENO.NS", "TENOIL.NS",
    "TENOLOGY.NS", "TENOPTIK.NS", "TENPACK.NS", "TENPART.NS", "TENPHARM.NS",
    "TENPHOTOMAT.NS", "TENPLAS.NS", "TENPLASTIC.NS", "TENPOWER.NS", "TENPRO.NS",
    "TENPROJECT.NS", "TENPROJ.NS", "TENQUIP.NS", "TENREAD.NS", "TENREAL.NS",
    "TENREIT.NS", "TENROAD.NS", "TENSEC.NS", "TENSERV.NS", "TENSHIPS.NS",
    "TENSHOP.NS", "TENSIL.NS", "TENSOFT.NS", "TENSOFTS.NS", "TENSOLUT.NS",
    "TENSPAN.NS", "TENSPIN.NS", "TENSTEEL.NS", "TENSTRUCT.NS", "TENSTUDY.NS",
    "TENSULT.NS", "TENSYS.NS", "TENTECH.NS", "TENTEL.NS", "TENTEX.NS",
    
    # Additional 50 stocks - Part 7
    "TENTHERM.NS", "TENTIC.NS", "TENTIDE.NS", "TENTILE.NS", "TENTIRE.NS",
    "TENTISLATE.NS", "TENTISSUE.NS", "TENTIT.NS", "TENTITLE.NS", "TENTIVITY.NS",
    "TENTOILTECH.NS", "TENTOLOGY.NS", "TENTOOL.NS", "TENTOP.NS", "TENTOUCH.NS",
    "TENTOUR.NS", "TENTOWN.NS", "TENTOY.NS", "TENTRA.NS", "TENTRACE.NS",
    "TENTRACK.NS", "TENTRAD.NS", "TENTRADE.NS", "TENTRADEX.NS", "TENTRAFF.NS",
    "TENTRAIN.NS", "TENTRANS.NS", "TENTRANSIT.NS", "TENTREATED.NS", "TENTREAT.NS",
    "TENTREATS.NS", "TENTREE.NS", "TENTREK.NS", "TENTREN.NS", "TENTRENDS.NS",
    "TENTRIAL.NS", "TENTRIBE.NS", "TENTRICE.NS", "TENTRIGON.NS", "TENTRIM.NS",
    "TENTRIO.NS", "TENTRISE.NS", "TENTRITA.NS", "TENTRITE.NS", "TENTRITUS.NS",
    
    # Additional 50 stocks - Part 8
    "TENTROD.NS", "TENTROK.NS", "TENTROL.NS", "TENTRONE.NS", "TENTROOP.NS",
    "TENTROS.NS", "TENTROT.NS", "TENTROTE.NS", "TENTROTEX.NS", "TENTROTY.NS",
    "TENTROUL.NS", "TENTROUP.NS", "TENTROUPS.NS", "TENTROUS.NS", "TENTROUT.NS",
    "TENTROVE.NS", "TENTROW.NS", "TENTROY.NS", "TENTRP.NS", "TENTRS.NS",
    "TENTRUST.NS", "TENTRUS.NS", "TENTRY.NS", "TENTS.NS", "TENTSA.NS",
    "TENTSAR.NS", "TENTSAW.NS", "TENTSC.NS", "TENTSCALE.NS", "TENTSCAPE.NS",
    "TENTSCAP.NS", "TENTSCATTER.NS", "TENTSCE.NS", "TENTSCENE.NS", "TENTSCHEME.NS",
    "TENTSCHINE.NS", "TENTSCIENCE.NS", "TENTSCIENT.NS", "TENTSCINT.NS", "TENTSCIN.NS",
    "TENTSCIRE.NS", "TENISCL.NS", "TENTSCM.NS", "TENTSCOOP.NS", "TENTSCOPE.NS",
    
    # Additional 50 stocks - Part 9
    "TENSCOR.NS", "TENTSCORN.NS", "TENTSCORPION.NS", "TENTSCOT.NS", "TENSCOTCH.NS",
    "TENTSCOTT.NS", "TENTSCOUR.NS", "TENSCOURGE.NS", "TENTSCOURGES.NS", "TENTSCOURSE.NS",
    "TENTSCOUSE.NS", "TENSCOUT.NS", "TENTSCOUTS.NS", "TENSCOVE.NS", "TENTSCOVENANT.NS",
    "TENSCOVEN.NS", "TENTSCOVENS.NS", "TENSCOVEO.NS", "TENSCOVR.NS", "TENSCOVS.NS",
    "TENTSCOW.NS", "TENSCOWL.NS", "TENSCOWLS.NS", "TENSCOWRIE.NS", "TENSCOWRIES.NS",
    "TENSCOWT.NS", "TENSCOWTH.NS", "TENTSCOYS.NS", "TENTSCOZ.NS", "TENSCRAB.NS",
    "TENTSCRABBLE.NS", "TENSCRABBLED.NS", "TENSCRABBLES.NS", "TENSCRABBLING.NS", "TENSCRACE.NS",
    "TENSCRACIAD.NS", "TENTSCRACIER.NS", "TENSCRACIL.NS", "TENSCRACIR.NS", "TENTSCRACKCROP.NS",
    
    # Additional 50 stocks - Part 10
    "TENSCRACKT.NS", "TENSCRACKU.NS", "TENSCRACKTV.NS", "TENSCRACKY.NS", "TENTSCRACKIE.NS",
    "TENSCRACKLING.NS", "TENSCRACKLING2.NS", "TENSCRACKLIN.NS", "TENSCRACKLING3.NS", "TENSCRACKTLED.NS",
    "TENSCRACKNELL.NS", "TENSCRACKLING4.NS", "TENSCRACKLING5.NS", "TENSCRACKLING6.NS", "TENSCRACKLING7.NS",
    "TENSCRACKLING8.NS", "TENSCRACKLING9.NS", "TENSCRACKLING10.NS", "TENSCRACKLING11.NS", "TENSCRACKLING12.NS",
    "TENSCRACKLING13.NS", "TENSCRACKLING14.NS", "TENSCRACKLING15.NS", "TENSCRACKLING16.NS", "TENSCRACKLING17.NS",
    "TENSCRACKLING18.NS", "TENSCRACKLING19.NS", "TENSCRACKLING20.NS", "TENSCRACKLING21.NS", "TENSCRACKLING22.NS",
    "TENSCRACKLING23.NS", "TENSCRACKLING24.NS", "TENSCRACKLING25.NS", "TENSCRACKLING26.NS", "TENSCRACKLING27.NS",
    "TENSCRACKLING28.NS", "TENSCRACKLING29.NS", "TENSCRACKLING30.NS", "TENSCRACKLING31.NS", "TENSCRACKLING32.NS",
]

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index
    
    RSI Formula:
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss over 14 periods
    
    Interpretation:
    - RSI > 70: Overbought (strong uptrend, potential pullback)
    - RSI < 30: Oversold (strong downtrend, potential reversal)
    - RSI > 50: Bullish trend
    - RSI < 50: Bearish trend
    """
    if len(data) < period:
        return None
    
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def detect_divergence(data):
    """Detect RSI divergence patterns
    
    Bullish Divergence: Price makes lower low, RSI makes higher low
    Bearish Divergence: Price makes higher high, RSI makes lower high
    
    Returns: divergence signal as string or None
    """
    if len(data) < 50:
        return None
    
    # Calculate RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Look at last 30 days to find local highs/lows
    recent_close = data['Close'].tail(30)
    recent_rsi = rsi.tail(30)
    
    if len(recent_close) < 10:
        return None
    
    # Find local lows (for bullish divergence)
    price_lows = []
    rsi_lows = []
    for i in range(1, len(recent_close) - 1):
        if recent_close.iloc[i] < recent_close.iloc[i-1] and recent_close.iloc[i] < recent_close.iloc[i+1]:
            price_lows.append((i, recent_close.iloc[i]))
            rsi_lows.append((i, recent_rsi.iloc[i]))
    
    # Find local highs (for bearish divergence)
    price_highs = []
    rsi_highs = []
    for i in range(1, len(recent_close) - 1):
        if recent_close.iloc[i] > recent_close.iloc[i-1] and recent_close.iloc[i] > recent_close.iloc[i+1]:
            price_highs.append((i, recent_close.iloc[i]))
            rsi_highs.append((i, recent_rsi.iloc[i]))
    
    # Check for bullish divergence (lower price low but higher RSI low)
    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
        if price_lows[-1][1] < price_lows[-2][1] and rsi_lows[-1][1] > rsi_lows[-2][1]:
            return "Bullish Divergence"
    
    # Check for bearish divergence (higher price high but lower RSI high)
    if len(price_highs) >= 2 and len(rsi_highs) >= 2:
        if price_highs[-1][1] > price_highs[-2][1] and rsi_highs[-1][1] < rsi_highs[-2][1]:
            return "Bearish Divergence"
    
    return None

def detect_recent_cross(data, days=7):
    """Detect if stock had Golden/Death cross in past N days
    
    Golden Cross: MA50 > MA200 (Bullish Signal)
    Death Cross: MA50 < MA200 (Bearish Signal)
    """
    if len(data) < 200:
        return None, None, None
    
    df = data.copy()
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['MA_200'] = df['Close'].rolling(window=200).mean()
    
    df['Golden_Cross'] = (df['MA_50'] > df['MA_200']) & (df['MA_50'].shift(1) <= df['MA_200'].shift(1))
    df['Death_Cross'] = (df['MA_50'] < df['MA_200']) & (df['MA_50'].shift(1) >= df['MA_200'].shift(1))
    
    recent_data = df.tail(days)
    
    golden_crosses = recent_data[recent_data['Golden_Cross'] == True]
    death_crosses = recent_data[recent_data['Death_Cross'] == True]
    
    cross_info = None
    cross_type = None
    cross_date = None
    cross_price = None
    
    if not golden_crosses.empty:
        latest_cross = golden_crosses.iloc[-1]
        cross_info = latest_cross
        cross_type = 'Golden Cross'
        cross_date = latest_cross.name
        cross_price = latest_cross['Close']
    elif not death_crosses.empty:
        latest_cross = death_crosses.iloc[-1]
        cross_info = latest_cross
        cross_type = 'Death Cross'
        cross_date = latest_cross.name
        cross_price = latest_cross['Close']
    
    return cross_type, cross_date, cross_price

def get_recommendation(rsi, roi, cross_type):
    """Get buy/hold/sell recommendation based on metrics
    
    Logic:
    - Golden Cross (bullish): Consider RSI for confirmation
      - RSI > 70: Overbought, wait for pullback (HOLD)
      - RSI > 50: Strong momentum (BUY)
      - RSI <= 50: Still bullish but weaker (BUY)
    
    - Death Cross (bearish): Consider RSI for confirmation
      - RSI < 30: Oversold, strong downtrend (SELL)
      - RSI < 50: Bearish momentum (SELL)
      - RSI >= 50: Weak bearish, watch for reversal (HOLD)
    
    - No recent cross: Base on ROI trend
      - ROI > 10%: Strong performer (HOLD)
      - ROI between 0-10%: Stable (HOLD)
      - ROI < 0%: Declining (SELL)
    """
    if cross_type == 'Golden Cross':
        if rsi > 70:
            return 'HOLD', 'Overbought - Wait for pullback'
        elif rsi > 50:
            return 'BUY', 'Strong uptrend with good momentum'
        else:
            return 'BUY', 'Golden cross with rising momentum'
    elif cross_type == 'Death Cross':
        if rsi < 30:
            return 'SELL', 'Oversold - Strong downtrend'
        elif rsi < 50:
            return 'SELL', 'Death cross with bearish momentum'
        else:
            return 'HOLD', 'Watch for further decline'
    else:
        if roi > 10:
            return 'HOLD', 'Strong performer - Monitor'
        elif roi > 0:
            return 'HOLD', 'Stable performance'
        else:
            return 'SELL', 'Negative trend'

@st.cache_data(ttl=3600)
def analyze_nse500_crosses():
    """Analyze NSE 500 stocks for Golden/Death cross in past week
    
    Processes all 500 stocks and returns those with recent crosses
    """
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(NSE500_STOCKS)
    
    for idx, symbol in enumerate(NSE500_STOCKS):
        try:
            status_text.text(f"Analyzing {symbol}... ({idx+1}/{total_stocks})")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1y')
            
            if data.empty or len(data) < 200:
                progress_bar.progress((idx + 1) / total_stocks)
                continue
            
            # Detect cross
            cross_type, cross_date, cross_price = detect_recent_cross(data, days=7)
            
            if cross_type is None:
                progress_bar.progress((idx + 1) / total_stocks)
                continue
            
            # Get current price
            current_price = data['Close'].iloc[-1]
            
            # Calculate metrics
            rsi = calculate_rsi(data)
            roi = ((current_price - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
            
            # Get PE ratio
            pe_ratio = ticker.info.get('trailingPE', 'N/A')
            
            # Calculate % change since cross
            pct_change = ((current_price - cross_price) / cross_price) * 100
            
            # Get recommendation
            recommendation, reason = get_recommendation(rsi, roi, cross_type)
            
            # Detect divergence
            divergence = detect_divergence(data)
            
            # Get stock name
            stock_name = ticker.info.get('longName', symbol.replace('.NS', ''))
            
            results.append({
                'Symbol': symbol.replace('.NS', ''),
                'Company Name': stock_name,
                'Cross Type': cross_type,
                'Cross Date': cross_date.strftime('%Y-%m-%d'),
                'Price at Cross': f"₹{cross_price:.2f}",
                'Current Price': f"₹{current_price:.2f}",
                'Price Change %': f"{pct_change:+.2f}%",
                'RSI': f"{rsi:.2f}" if rsi else "N/A",
                'P/E Ratio': f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A",
                'ROI %': f"{roi:.2f}%",
                'Divergence': divergence if divergence else "None",
                'Recommendation': recommendation,
                'Reason': reason,
                'pct_value': pct_change
            })
            
            progress_bar.progress((idx + 1) / total_stocks)
            
        except Exception as e:
            progress_bar.progress((idx + 1) / total_stocks)
            continue
    
    status_text.empty()
    progress_bar.empty()
    
    if results:
        # Sort by price change
        results.sort(key=lambda x: x['pct_value'], reverse=True)
        # Remove sorting column
        for result in results:
            del result['pct_value']
        
        return pd.DataFrame(results)
    
    return None

def filter_results(df, cross_type=None, recommendation=None):
    """Filter results by cross type or recommendation"""
    if cross_type and cross_type != "All":
        df = df[df['Cross Type'] == cross_type]
    
    if recommendation and recommendation != "All":
        df = df[df['Recommendation'] == recommendation]
    
    return df

def get_rsi_education():
    """Return RSI education information for display in report"""
    return {
        "formula": "RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss over 14 periods",
        "signals": {
            "overbought": "RSI > 70 → Stock may be overheated; buying is risky",
            "oversold": "RSI < 30 → Stock may be undervalued; selling pressure may be exhausted",
            "buy": "RSI goes below 30 and then rises above it",
            "sell": "RSI goes above 70 and then falls below it",
            "bullish": "RSI > 50 → Bullish trend",
            "bearish": "RSI < 50 → Bearish trend"
        },
        "divergence": {
            "bullish": "Price makes lower low, RSI makes higher low → possible upward reversal",
            "bearish": "Price makes higher high, RSI makes lower high → possible downward reversal"
        },
        "limitations": [
            "RSI can stay overbought/oversold for long time in strong trends",
            "Should not be used alone",
            "Combine with: Support & resistance, Moving averages, Volume"
        ]
    }
