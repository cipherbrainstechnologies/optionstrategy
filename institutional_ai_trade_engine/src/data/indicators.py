"""
Technical indicators calculation module.
"""
import pandas as pd
import ta
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
    df["RSI"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    
    # Weighted Moving Averages
    df["WMA20"] = df["close"].rolling(20).mean()
    df["WMA50"] = df["close"].rolling(50).mean()
    df["WMA100"] = df["close"].rolling(100).mean()
    
    # Average True Range
    df["ATR"] = ta.volatility.AverageTrueRange(
        df["high"], df["low"], df["close"]
    ).average_true_range()
    
    # ATR as percentage of close price
    df["ATR_PCT"] = df["ATR"] / df["close"]
    
    # Volume ratio (current volume vs 20-day average)
    df["VOL_X20D"] = df["volume"] / df["volume"].rolling(20).mean()
    
    # Additional useful indicators
    df["SMA20"] = df["close"].rolling(20).mean()
    df["SMA50"] = df["close"].rolling(50).mean()
    df["SMA200"] = df["close"].rolling(200).mean()
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"])
    df["BB_upper"] = bb.bollinger_hband()
    df["BB_lower"] = bb.bollinger_lband()
    df["BB_middle"] = bb.bollinger_mavg()
    df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_middle"]
    
    # MACD
    macd = ta.trend.MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    df["MACD_histogram"] = macd.macd_diff()
    
    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()
    
    # Williams %R
    df["WILLIAMS_R"] = ta.momentum.WilliamsRIndicator(df["high"], df["low"], df["close"]).williams_r()
    
    # Commodity Channel Index
    df["CCI"] = ta.trend.CCIIndicator(df["high"], df["low"], df["close"]).cci()
    
    # Average Directional Index
    df["ADX"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"]).adx()
    
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
    weekly_df["WEEKLY_RSI"] = ta.momentum.RSIIndicator(weekly_df["close"], window=14).rsi()
    weekly_df["WEEKLY_ATR"] = ta.volatility.AverageTrueRange(
        weekly_df["high"], weekly_df["low"], weekly_df["close"]
    ).average_true_range()
    
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