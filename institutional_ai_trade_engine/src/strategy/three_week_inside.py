"""
Three Week Inside (3WI) strategy implementation.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def detect_3wi(weekly_df: pd.DataFrame) -> List[Dict]:
    """
    Detect Three Week Inside patterns in weekly data.
    
    Args:
        weekly_df: DataFrame with weekly OHLCV data
    
    Returns:
        List[Dict]: List of detected 3WI patterns
    """
    res = []
    
    if len(weekly_df) < 3:
        return res
    
    try:
        for i in range(2, len(weekly_df)):
            # Mother candle (2 weeks ago)
            m = weekly_df.iloc[i-2]
            # First inside week
            w1 = weekly_df.iloc[i-1]
            # Second inside week (current)
            w2 = weekly_df.iloc[i]
            
            # Check 3WI conditions:
            # Both w1 and w2 are inside the mother candle
            if (w1['high'] <= m['high'] and w1['low'] >= m['low'] and
                w2['high'] <= m['high'] and w2['low'] >= m['low']):
                
                pattern = {
                    "mother_high": float(m['high']),
                    "mother_low": float(m['low']),
                    "index": i,
                    "week_start": weekly_df.iloc[i]['timestamp'].strftime('%Y-%m-%d'),
                    "inside_weeks": 2,
                    "mother_range": float(m['high'] - m['low']),
                    "mother_range_pct": float((m['high'] - m['low']) / m['close'] * 100)
                }
                res.append(pattern)
                
    except Exception as e:
        logger.error(f"Error detecting 3WI patterns: {e}")
    
    return res

def breakout(weekly_df: pd.DataFrame, pattern_index: int) -> Optional[str]:
    """
    Check for breakout from 3WI pattern.
    
    Args:
        weekly_df: DataFrame with weekly OHLCV data
        pattern_index: Index of the pattern to check
    
    Returns:
        str: 'up' for upward breakout, 'down' for downward, None if no breakout
    """
    try:
        if pattern_index < 2 or pattern_index >= len(weekly_df):
            return None
        
        # Mother candle
        m = weekly_df.iloc[pattern_index - 2]
        # Current week (latest)
        w2 = weekly_df.iloc[pattern_index]
        
        # Check for breakouts
        up_breakout = w2['close'] > m['high']
        down_breakout = w2['close'] < m['low']
        
        if up_breakout:
            return "up"
        elif down_breakout:
            return "down"
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error checking breakout: {e}")
        return None

def is_near_breakout(weekly_df: pd.DataFrame, pattern: Dict, threshold: float = 0.99) -> bool:
    """
    Check if price is near breakout level.
    
    Args:
        weekly_df: DataFrame with weekly OHLCV data
        pattern: 3WI pattern dictionary
        threshold: Threshold for near breakout (0.99 = 99% of mother high)
    
    Returns:
        bool: True if near breakout
    """
    try:
        if len(weekly_df) == 0:
            return False
        
        current_price = weekly_df.iloc[-1]['close']
        mother_high = pattern['mother_high']
        
        # Check if current price is within threshold of mother high
        return current_price >= (mother_high * threshold)
        
    except Exception as e:
        logger.error(f"Error checking near breakout: {e}")
        return False

def calculate_breakout_strength(weekly_df: pd.DataFrame, pattern: Dict) -> Dict:
    """
    Calculate breakout strength metrics.
    
    Args:
        weekly_df: DataFrame with weekly OHLCV data
        pattern: 3WI pattern dictionary
    
    Returns:
        Dict: Breakout strength metrics
    """
    try:
        if len(weekly_df) == 0:
            return {}
        
        current = weekly_df.iloc[-1]
        mother_high = pattern['mother_high']
        mother_low = pattern['mother_low']
        
        # Distance to breakout levels
        distance_to_high = ((mother_high - current['close']) / current['close']) * 100
        distance_to_low = ((current['close'] - mother_low) / current['close']) * 100
        
        # Volume analysis
        avg_volume = weekly_df['volume'].rolling(20).mean().iloc[-1]
        volume_ratio = current['volume'] / avg_volume if avg_volume > 0 else 1
        
        # Volatility analysis
        atr = weekly_df['ATR'].iloc[-1] if 'ATR' in weekly_df.columns else 0
        atr_pct = (atr / current['close']) * 100 if current['close'] > 0 else 0
        
        return {
            "distance_to_high_pct": round(distance_to_high, 2),
            "distance_to_low_pct": round(distance_to_low, 2),
            "volume_ratio": round(volume_ratio, 2),
            "atr_pct": round(atr_pct, 2),
            "current_price": float(current['close']),
            "mother_high": mother_high,
            "mother_low": mother_low
        }
        
    except Exception as e:
        logger.error(f"Error calculating breakout strength: {e}")
        return {}

def get_pattern_quality_score(pattern: Dict, weekly_df: pd.DataFrame) -> float:
    """
    Calculate quality score for a 3WI pattern.
    
    Args:
        pattern: 3WI pattern dictionary
        weekly_df: DataFrame with weekly OHLCV data
    
    Returns:
        float: Quality score (0-100)
    """
    try:
        score = 0
        
        # Mother range quality (not too tight, not too wide)
        range_pct = pattern.get('mother_range_pct', 0)
        if 2 <= range_pct <= 8:  # 2-8% range is ideal
            score += 30
        elif 1 <= range_pct <= 12:  # Acceptable range
            score += 20
        
        # Volume confirmation
        if len(weekly_df) > 0:
            current_volume = weekly_df.iloc[-1]['volume']
            avg_volume = weekly_df['volume'].rolling(20).mean().iloc[-1]
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                if volume_ratio >= 1.5:
                    score += 25
                elif volume_ratio >= 1.2:
                    score += 15
        
        # Trend alignment
        if len(weekly_df) >= 20:
            sma20 = weekly_df['close'].rolling(20).mean().iloc[-1]
            sma50 = weekly_df['close'].rolling(50).mean().iloc[-1]
            current_price = weekly_df.iloc[-1]['close']
            
            if current_price > sma20 > sma50:  # Uptrend
                score += 25
            elif current_price > sma20:  # Partial uptrend
                score += 15
        
        # RSI momentum
        if 'RSI' in weekly_df.columns and len(weekly_df) > 0:
            rsi = weekly_df['RSI'].iloc[-1]
            if 55 <= rsi <= 75:  # Good momentum zone
                score += 20
            elif 50 <= rsi <= 80:  # Acceptable zone
                score += 10
        
        return min(score, 100)  # Cap at 100
        
    except Exception as e:
        logger.error(f"Error calculating pattern quality score: {e}")
        return 0