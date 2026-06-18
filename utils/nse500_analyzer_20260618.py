import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

NSE500_STOCKS = [
    "360ONE.NS", "3MINDIA.NS", "ABB.NS", "ACC.NS", "ACMESOLAR.NS",
    "AIAENG.NS", "APLAPOLLO.NS", "AUBANK.NS", "AWL.NS", "AADHARHFC.NS",
    "AARTIIND.NS", "AAVAS.NS", "ABBOTINDIA.NS", "ACE.NS", "ADANIENSOL.NS",
    "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", "ATGL.NS",
    "ABCAPITAL.NS", "ABFRL.NS", "ABLBL.NS", "ABREL.NS", "ABSLAMC.NS",
    "AEGISLOG.NS", "AEGISVOPAK.NS", "AFCONS.NS", "AFFLE.NS", "AJANTPHARM.NS",
    "AKUMS.NS", "AKZOINDIA.NS", "APLLTD.NS", "ALKEM.NS", "ALKYLAMINE.NS",
    "ALOKINDS.NS", "ARE&M.NS", "AMBER.NS", "AMBUJACEM.NS", "ANANDRATHI.NS",
    "ANANTRAJ.NS", "ANGELONE.NS", "APARINDS.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS",
    "APTUS.NS", "ASAHIINDIA.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTERDM.NS",
    "ASTRAZEN.NS", "ASTRAL.NS", "ATHERENERG.NS", "ATUL.NS", "AUROPHARMA.NS",
    "AIIL.NS", "DMART.NS", "AXISBANK.NS", "BASF.NS", "BEML.NS",
    "BLS.NS", "BSE.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BAJAJHLDNG.NS", "BAJAJHFL.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS",
    "BANKBARODA.NS", "BANKINDIA.NS", "MAHABANK.NS", "BATAINDIA.NS", "BAYERCROP.NS",
    "BERGEPAINT.NS", "BDL.NS", "BEL.NS", "BHARATFORG.NS", "BHEL.NS",
    "BPCL.NS", "BHARTIARTL.NS", "BHARTIHEXA.NS", "BIKAJI.NS", "BIOCON.NS",
    "BSOFT.NS", "BLUEDART.NS", "BLUEJET.NS", "BLUESTARCO.NS", "BBTC.NS",
    "BOSCHLTD.NS", "FIRSTCRY.NS", "BRIGADE.NS", "BRITANNIA.NS", "MAPMYINDIA.NS",
    "CCL.NS", "CESC.NS", "CGPOWER.NS", "CRISIL.NS", "CAMPUS.NS",
    "CANFINHOME.NS", "CANBK.NS", "CAPLIPOINT.NS", "CGCL.NS", "CARBORUNIV.NS",
    "CASTROLIND.NS", "CEATLTD.NS", "CENTRALBK.NS", "CDSL.NS", "CENTURYPLY.NS",
    "CERA.NS", "CHALET.NS", "CHAMBLFERT.NS", "CHENNPETRO.NS", "CHOICEIN.NS",
    "CHOLAHLDNG.NS", "CHOLAFIN.NS", "CIPLA.NS", "CUB.NS", "CLEAN.NS",
    "COALINDIA.NS", "COCHINSHIP.NS", "COFORGE.NS", "COHANCE.NS", "COLPAL.NS",
    "CAMS.NS", "CONCORDBIO.NS", "CONCOR.NS", "COROMANDEL.NS", "CRAFTSMAN.NS",
    "CREDITACC.NS", "CROMPTON.NS", "CUMMINSIND.NS", "CYIENT.NS", "DCMSHRIRAM.NS",
    "DLF.NS", "DOMS.NS", "DABUR.NS", "DALBHARAT.NS", "DATAPATTNS.NS",
    "DEEPAKFERT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DEVYANI.NS", "DIVISLAB.NS",
    "DIXON.NS", "AGARWALEYE.NS", "LALPATHLAB.NS", "DRREDDY.NS", "DUMMYHDLVR.NS",
    "EIDPARRY.NS", "EIHOTEL.NS", "EICHERMOT.NS", "ELECON.NS", "ELGIEQUIP.NS",
    "EMAMILTD.NS", "EMCURE.NS", "ENDURANCE.NS", "ENGINERSIN.NS", "ERIS.NS",
    "ESCORTS.NS", "ETERNAL.NS", "EXIDEIND.NS", "NYKAA.NS", "FEDERALBNK.NS",
    "FACT.NS", "FINCABLES.NS", "FINPIPE.NS", "FSL.NS", "FIVESTAR.NS",
    "FORCEMOT.NS", "FORTIS.NS", "GAIL.NS", "GVT&D.NS", "GMRAIRPORT.NS",
    "GRSE.NS", "GICRE.NS", "GILLETTE.NS", "GLAND.NS", "GLAXO.NS",
    "GLENMARK.NS", "MEDANTA.NS", "GODIGIT.NS", "GPIL.NS", "GODFRYPHLP.NS",
    "GODREJAGRO.NS", "GODREJCP.NS", "GODREJIND.NS", "GODREJPROP.NS", "GRANULES.NS",
    "GRAPHITE.NS", "GRASIM.NS", "GRAVITA.NS", "GESHIP.NS", "FLUOROCHEM.NS",
    "GUJGASLTD.NS", "GMDCLTD.NS", "GSPL.NS", "HEG.NS", "HBLENGINE.NS",
    "HCLTECH.NS", "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HFCL.NS",
    "HAPPSTMNDS.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HEXT.NS", "HSCL.NS",
    "HINDALCO.NS", "HAL.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS",
    "HINDZINC.NS", "POWERINDIA.NS", "HOMEFIRST.NS", "HONASA.NS", "HONAUT.NS",
    "HUDCO.NS", "HYUNDAI.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS",
    "IDBI.NS", "IDFCFIRSTB.NS", "IFCI.NS", "IIFL.NS", "INOXINDIA.NS",
    "IRB.NS", "IRCON.NS", "ITCHOTELS.NS", "ITC.NS", "ITI.NS",
    "INDGN.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIANB.NS", "IEX.NS",
    "INDHOTEL.NS", "IOC.NS", "IOB.NS", "IRCTC.NS", "IRFC.NS",
    "IREDA.NS", "IGL.NS", "INDUSTOWER.NS", "INDUSINDBK.NS", "NAUKRI.NS",
    "INFY.NS", "INOXWIND.NS", "INTELLECT.NS", "INDIGO.NS", "IGIL.NS",
    "IKS.NS", "IPCALAB.NS", "JBCHEPHARM.NS", "JKCEMENT.NS", "JBMA.NS",
    "JKTYRE.NS", "JMFINANCIL.NS", "JSWENERGY.NS", "JSWINFRA.NS", "JSWSTEEL.NS",
    "JPPOWER.NS", "J&KBANK.NS", "JINDALSAW.NS", "JSL.NS", "JINDALSTEL.NS",
    "JIOFIN.NS", "JUBLFOOD.NS", "JUBLINGREA.NS", "JUBLPHARMA.NS", "JWL.NS",
    "JYOTHYLAB.NS", "JYOTICNC.NS", "KPRMILL.NS", "KEI.NS", "KPITTECH.NS",
    "KSB.NS", "KAJARIACER.NS", "KPIL.NS", "KALYANKJIL.NS", "KARURVYSYA.NS",
    "KAYNES.NS", "KEC.NS", "KFINTECH.NS", "KIRLOSBROS.NS", "KIRLOSENG.NS",
    "KOTAKBANK.NS", "KIMS.NS", "LTF.NS", "LTTS.NS", "LICHSGFIN.NS",
    "LTFOODS.NS", "LTIM.NS", "LT.NS", "LATENTVIEW.NS", "LAURUSLABS.NS",
    "THELEELA.NS", "LEMONTREE.NS", "LICI.NS", "LINDEINDIA.NS", "LLOYDSME.NS",
    "LODHA.NS", "LUPIN.NS", "MMTC.NS", "MRF.NS", "MGL.NS",
    "MAHSCOOTER.NS", "MAHSEAMLES.NS", "M&MFIN.NS", "M&M.NS", "MANAPPURAM.NS",
    "MRPL.NS", "MANKIND.NS", "MARICO.NS", "MARUTI.NS", "MFSL.NS",
    "MAXHEALTH.NS", "MAZDOCK.NS", "METROPOLIS.NS", "MINDACORP.NS", "MSUMI.NS",
    "MOTILALOFS.NS", "MPHASIS.NS", "MCX.NS", "MUTHOOTFIN.NS", "NATCOPHARM.NS",
    "NBCC.NS", "NCC.NS", "NHPC.NS", "NLCINDIA.NS", "NMDC.NS",
    "NSLNISP.NS", "NTPCGREEN.NS", "NTPC.NS", "NH.NS", "NATIONALUM.NS",
    "NAVA.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NETWEB.NS", "NEULANDLAB.NS",
    "NEWGEN.NS", "NAM-INDIA.NS", "NIVABUPA.NS", "NUVAMA.NS", "NUVOCO.NS",
    "OBEROIRLTY.NS", "ONGC.NS", "OIL.NS", "OLAELEC.NS", "OLECTRA.NS",
    "PAYTM.NS", "ONESOURCE.NS", "OFSS.NS", "POLICYBZR.NS", "PCBL.NS",
    "PGEL.NS", "PIIND.NS", "PNBHOUSING.NS", "PTCIL.NS", "PVRINOX.NS",
    "PAGEIND.NS", "PATANJALI.NS", "PERSISTENT.NS", "PETRONET.NS", "PFIZER.NS",
    "PHOENIXLTD.NS", "PIDILITIND.NS", "PPLPHARMA.NS", "POLYMED.NS", "POLYCAB.NS",
    "POONAWALLA.NS", "PFC.NS", "POWERGRID.NS", "PRAJIND.NS", "PREMIERENE.NS",
    "PRESTIGE.NS", "PGHH.NS", "PNB.NS", "RRKABEL.NS", "RBLBANK.NS",
    "RECLTD.NS", "RHIM.NS", "RITES.NS", "RADICO.NS", "RVNL.NS",
    "RAILTEL.NS", "RAINBOW.NS", "RKFORGE.NS", "RCF.NS", "REDINGTON.NS",
    "RELIANCE.NS", "RELINFRA.NS", "RPOWER.NS", "SBFC.NS", "SBICARD.NS",
    "SBILIFE.NS", "SJVN.NS", "SKFINDIA.NS", "SRF.NS", "SAGILITY.NS",
    "SAILIFE.NS", "SAMMAANCAP.NS", "MOTHERSON.NS", "SAPPHIRE.NS", "SARDAEN.NS",
    "SAREGAMA.NS", "SCHAEFFLER.NS", "SCHNEIDER.NS", "SCI.NS", "SHREECEM.NS",
    "SHRIRAMFIN.NS", "SHYAMMETL.NS", "ENRIN.NS", "SIEMENS.NS", "SIGNATURE.NS",
    "SOBHA.NS", "SOLARINDS.NS", "SONACOMS.NS", "SONATSOFTW.NS", "STARHEALTH.NS",
    "SBIN.NS", "SAIL.NS", "SUMICHEM.NS", "SUNPHARMA.NS", "SUNTV.NS",
    "SUNDARMFIN.NS", "SUNDRMFAST.NS", "SUPREMEIND.NS", "SUZLON.NS", "SWANCORP.NS",
    "SWIGGY.NS", "SYNGENE.NS", "SYRMA.NS", "TBOTEK.NS", "TVSMOTOR.NS",
    "TATACHEM.NS", "TATACOMM.NS", "TCS.NS", "TATACONSUM.NS", "TATAELXSI.NS",
    "TATAINVEST.NS", "TMPV.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TATATECH.NS",
    "TTML.NS", "TECHM.NS", "TECHNOE.NS", "TEJASNET.NS", "NIACL.NS",
    "RAMCOCEM.NS", "THERMAX.NS", "TIMKEN.NS", "TITAGARH.NS", "TITAN.NS",
    "TORNTPHARM.NS", "TORNTPOWER.NS", "TARIL.NS", "TRENT.NS", "TRIDENT.NS",
    "TRIVENI.NS", "TRITURBINE.NS", "TIINDIA.NS", "UCOBANK.NS", "UNOMINDA.NS",
    "UPL.NS", "UTIAMC.NS", "ULTRACEMCO.NS", "UNIONBANK.NS", "UBL.NS",
    "UNITDSPR.NS", "USHAMART.NS", "VGUARD.NS", "DBREALTY.NS", "VTL.NS",
    "VBL.NS", "MANYAVAR.NS", "VEDL.NS", "VENTIVE.NS", "VIJAYA.NS",
    "VMM.NS", "IDEA.NS", "VOLTAS.NS", "WAAREEENER.NS", "WELCORP.NS",
    "WELSPUNLIV.NS", "WHIRLPOOL.NS", "WIPRO.NS", "WOCKPHARMA.NS", "YESBANK.NS",
    "ZFCVINDIA.NS", "ZEEL.NS", "ZENTEC.NS", "ZENSARTECH.NS", "ZYDUSLIFE.NS",
    "ECLERX.NS"
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
