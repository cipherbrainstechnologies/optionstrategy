"""
Technical indicators calculation module.
"""
import pandas as pd
import numpy as np

def compute(df):
    """
    Compute technical indicators for the given DataFrame.
    
    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
    
    Returns:
        DataFrame: Original DataFrame with added indicator columns
    """
    # RSI (Relative Strength Index)
    df["RSI"] = calculate_rsi(df["close"])
    
    # Weighted Moving Averages
    df["WMA20"] = df["close"].rolling(20).mean()  # Simplified to SMA
    df["WMA50"] = df["close"].rolling(50).mean()  # Simplified to SMA
    df["WMA100"] = df["close"].rolling(100).mean()  # Simplified to SMA
    
    # Average True Range
    df["ATR"] = calculate_atr(df["high"], df["low"], df["close"])
    
    # ATR as percentage of close price
    df["ATR_PCT"] = df["ATR"] / df["close"]
    
    # Volume ratio (current volume vs 20-day average)
    df["VOL_X20D"] = df["volume"] / df["volume"].rolling(20).mean()
    
    # Additional useful indicators
    df["SMA20"] = df["close"].rolling(20).mean()
    df["SMA50"] = df["close"].rolling(50).mean()
    df["SMA200"] = df["close"].rolling(200).mean()
    
    # Bollinger Bands
    bb_middle = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["BB_upper"] = bb_middle + (bb_std * 2)
    df["BB_lower"] = bb_middle - (bb_std * 2)
    df["BB_middle"] = bb_middle
    df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_middle"]
    
    # MACD
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_histogram"] = df["MACD"] - df["MACD_signal"]
    
    # Stochastic Oscillator
    df["STOCH_K"] = calculate_stochastic_k(df["high"], df["low"], df["close"])
    df["STOCH_D"] = df["STOCH_K"].rolling(3).mean()
    
    # Williams %R
    df["WILLIAMS_R"] = calculate_williams_r(df["high"], df["low"], df["close"])
    
    # Commodity Channel Index
    df["CCI"] = calculate_cci(df["high"], df["low"], df["close"])
    
    # Average Directional Index (simplified)
    df["ADX"] = calculate_adx(df["high"], df["low"], df["close"])
    
    # Price change percentages
    df["CHANGE_1D"] = df["close"].pct_change(1) * 100
    df["CHANGE_5D"] = df["close"].pct_change(5) * 100
    df["CHANGE_20D"] = df["close"].pct_change(20) * 100
    
    return df

def compute_weekly_indicators(weekly_df):
    """
    Compute indicators specifically for weekly data.
    
    Args:
        weekly_df: DataFrame with weekly OHLCV data
    
    Returns:
        DataFrame: Weekly DataFrame with indicators
    """
    # Basic indicators
    weekly_df = compute(weekly_df)
    
    # Weekly-specific indicators
    weekly_df["WEEKLY_RSI"] = calculate_rsi(weekly_df["close"])
    weekly_df["WEEKLY_ATR"] = calculate_atr(weekly_df["high"], weekly_df["low"], weekly_df["close"])
    
    # Weekly moving averages
    weekly_df["WEEKLY_SMA10"] = weekly_df["close"].rolling(10).mean()
    weekly_df["WEEKLY_SMA20"] = weekly_df["close"].rolling(20).mean()
    weekly_df["WEEKLY_SMA50"] = weekly_df["close"].rolling(50).mean()
    
    return weekly_df

def is_trending_up(df, lookback=20):
    """
    Check if the trend is upward based on moving averages.
    
    Args:
        df: DataFrame with price data
        lookback: Number of periods to look back
    
    Returns:
        bool: True if trending up
    """
    if len(df) < lookback:
        return False
    
    recent = df.tail(lookback)
    return (
        recent["close"].iloc[-1] > recent["SMA20"].iloc[-1] and
        recent["SMA20"].iloc[-1] > recent["SMA50"].iloc[-1] and
        recent["close"].iloc[-1] > recent["close"].iloc[-lookback]
    )

def is_consolidating(df, lookback=20, threshold=0.05):
    """
    Check if price is consolidating (sideways movement).
    
    Args:
        df: DataFrame with price data
        lookback: Number of periods to look back
        threshold: Maximum price range as percentage
    
    Returns:
        bool: True if consolidating
    """
    if len(df) < lookback:
        return False
    
    recent = df.tail(lookback)
    high = recent["high"].max()
    low = recent["low"].min()
    range_pct = (high - low) / low
    
    return range_pct <= threshold

def calculate_rsi(prices, window=14):
    """Calculate RSI (Relative Strength Index)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(high, low, close, window=14):
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr

def calculate_stochastic_k(high, low, close, window=14):
    """Calculate Stochastic %K."""
    lowest_low = low.rolling(window=window).min()
    highest_high = high.rolling(window=window).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    return k

def calculate_williams_r(high, low, close, window=14):
    """Calculate Williams %R."""
    highest_high = high.rolling(window=window).max()
    lowest_low = low.rolling(window=window).min()
    wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
    return wr

def calculate_cci(high, low, close, window=20):
    """Calculate Commodity Channel Index."""
    typical_price = (high + low + close) / 3
    sma = typical_price.rolling(window=window).mean()
    mad = typical_price.rolling(window=window).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    cci = (typical_price - sma) / (0.015 * mad)
    return cci

def calculate_adx(high, low, close, window=14):
    """Calculate Average Directional Index (simplified)."""
    # Simplified ADX calculation
    tr = calculate_atr(high, low, close, window=1)
    plus_dm = high.diff()
    minus_dm = low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    plus_di = 100 * (plus_dm.rolling(window=window).mean() / tr.rolling(window=window).mean())
    minus_di = 100 * (minus_dm.rolling(window=window).mean() / tr.rolling(window=window).mean())
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=window).mean()
    return adx