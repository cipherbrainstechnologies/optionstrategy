"""
Technical indicators calculation module.
"""
import pandas as pd
import pandas_ta as ta
import numpy as np

def compute(df):
    """
    Compute technical indicators for the given DataFrame.
    
    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
    
    Returns:
        DataFrame: Original DataFrame with added indicator columns
    """
    # RSI
    df["RSI"] = ta.rsi(df["close"])
    
    # Weighted Moving Averages
    df["WMA20"] = ta.wma(df["close"], length=20)
    df["WMA50"] = ta.wma(df["close"], length=50)
    df["WMA100"] = ta.wma(df["close"], length=100)
    
    # Average True Range
    df["ATR"] = ta.atr(df["high"], df["low"], df["close"])
    
    # ATR as percentage of close price
    df["ATR_PCT"] = df["ATR"] / df["close"]
    
    # Volume ratio (current volume vs 20-day average)
    df["VOL_X20D"] = df["volume"] / df["volume"].rolling(20).mean()
    
    # Additional useful indicators
    df["SMA20"] = df["close"].rolling(20).mean()
    df["SMA50"] = df["close"].rolling(50).mean()
    df["SMA200"] = df["close"].rolling(200).mean()
    
    # Bollinger Bands
    bb_data = ta.bbands(df["close"])
    if bb_data is not None:
        df["BB_upper"] = bb_data[f"BBU_20_2.0"]
        df["BB_lower"] = bb_data[f"BBL_20_2.0"]
        df["BB_middle"] = bb_data[f"BBM_20_2.0"]
        df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_middle"]
    else:
        df["BB_upper"] = df["BB_lower"] = df["BB_middle"] = df["BB_width"] = np.nan
    
    # MACD
    macd_data = ta.macd(df["close"])
    if macd_data is not None:
        df["MACD"] = macd_data["MACD_12_26_9"]
        df["MACD_signal"] = macd_data["MACDs_12_26_9"]
        df["MACD_histogram"] = macd_data["MACDh_12_26_9"]
    else:
        df["MACD"] = df["MACD_signal"] = df["MACD_histogram"] = np.nan
    
    # Stochastic Oscillator
    stoch_data = ta.stoch(df["high"], df["low"], df["close"])
    if stoch_data is not None:
        df["STOCH_K"] = stoch_data["STOCHk_14_3_3"]
        df["STOCH_D"] = stoch_data["STOCHd_14_3_3"]
    else:
        df["STOCH_K"] = df["STOCH_D"] = np.nan
    
    # Williams %R
    df["WILLIAMS_R"] = ta.willr(df["high"], df["low"], df["close"])
    
    # Commodity Channel Index
    df["CCI"] = ta.cci(df["high"], df["low"], df["close"])
    
    # Average Directional Index
    df["ADX"] = ta.adx(df["high"], df["low"], df["close"])
    
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
    weekly_df["WEEKLY_RSI"] = ta.rsi(weekly_df["close"])
    weekly_df["WEEKLY_ATR"] = ta.atr(weekly_df["high"], weekly_df["low"], weekly_df["close"])
    
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