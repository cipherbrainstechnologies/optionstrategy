"""
Trading filters for strategy validation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def filters_ok(row: pd.Series) -> bool:
    """
    Check if a stock passes all trading filters.
    
    Args:
        row: Series with stock data and indicators
    
    Returns:
        bool: True if all filters pass
    """
    try:
        # RSI filter: Must be above 55 (momentum)
        if pd.isna(row.get('RSI', 0)) or row['RSI'] <= 55:
            return False
        
        # Moving average alignment: WMA20 > WMA50 > WMA100
        if (pd.isna(row.get('WMA20', 0)) or pd.isna(row.get('WMA50', 0)) or 
            pd.isna(row.get('WMA100', 0))):
            return False
        
        if not (row['WMA20'] > row['WMA50'] > row['WMA100']):
            return False
        
        # Volume filter: Current volume >= 1.5x 20-day average
        if pd.isna(row.get('VOL_X20D', 0)) or row['VOL_X20D'] < 1.5:
            return False
        
        # ATR filter: ATR as % of price < 6% (not too volatile)
        if pd.isna(row.get('ATR_PCT', 0)) or row['ATR_PCT'] >= 0.06:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in filters_ok: {e}")
        return False

def advanced_filters_ok(row: pd.Series) -> bool:
    """
    Advanced filters for higher quality setups.
    
    Args:
        row: Series with stock data and indicators
    
    Returns:
        bool: True if all advanced filters pass
    """
    try:
        # Basic filters must pass first
        if not filters_ok(row):
            return False
        
        # RSI in optimal range (55-75)
        rsi = row.get('RSI', 0)
        if not (55 <= rsi <= 75):
            return False
        
        # MACD bullish
        if 'MACD' in row and 'MACD_signal' in row:
            if pd.notna(row['MACD']) and pd.notna(row['MACD_signal']):
                if row['MACD'] <= row['MACD_signal']:
                    return False
        
        # Price above Bollinger Band middle
        if 'BB_middle' in row and pd.notna(row['BB_middle']):
            if row['close'] <= row['BB_middle']:
                return False
        
        # ADX > 25 (trending market)
        if 'ADX' in row and pd.notna(row['ADX']):
            if row['ADX'] <= 25:
                return False
        
        # Williams %R not oversold
        if 'WILLIAMS_R' in row and pd.notna(row['WILLIAMS_R']):
            if row['WILLIAMS_R'] <= -80:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in advanced_filters_ok: {e}")
        return False

def volume_confirmation(row: pd.Series) -> bool:
    """
    Check volume confirmation for breakout.
    
    Args:
        row: Series with stock data
    
    Returns:
        bool: True if volume confirms
    """
    try:
        # Volume should be above average
        vol_ratio = row.get('VOL_X20D', 0)
        if pd.isna(vol_ratio) or vol_ratio < 1.2:
            return False
        
        # Volume should be increasing
        if 'volume' in row and 'volume' in row.index:
            # This would need historical data to compare
            # For now, just check current volume ratio
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"Error in volume_confirmation: {e}")
        return False

def trend_strength_filter(row: pd.Series) -> bool:
    """
    Check trend strength.
    
    Args:
        row: Series with stock data
    
    Returns:
        bool: True if trend is strong enough
    """
    try:
        # Price should be above all major moving averages
        if (pd.isna(row.get('WMA20', 0)) or pd.isna(row.get('WMA50', 0)) or 
            pd.isna(row.get('WMA100', 0))):
            return False
        
        close = row['close']
        if not (close > row['WMA20'] > row['WMA50'] > row['WMA100']):
            return False
        
        # Moving averages should be rising
        # This would need historical data to check slope
        # For now, just check alignment
        
        return True
        
    except Exception as e:
        logger.error(f"Error in trend_strength_filter: {e}")
        return False

def volatility_filter(row: pd.Series) -> bool:
    """
    Check volatility is within acceptable range.
    
    Args:
        row: Series with stock data
    
    Returns:
        bool: True if volatility is acceptable
    """
    try:
        # ATR should not be too high (already checked in basic filters)
        atr_pct = row.get('ATR_PCT', 0)
        if pd.isna(atr_pct) or atr_pct >= 0.08:  # Max 8% ATR
            return False
        
        # Bollinger Band width should not be too wide
        if 'BB_width' in row and pd.notna(row['BB_width']):
            if row['BB_width'] >= 0.15:  # Max 15% BB width
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in volatility_filter: {e}")
        return False

def get_filter_score(row: pd.Series) -> Dict:
    """
    Get detailed filter scores for analysis.
    
    Args:
        row: Series with stock data
    
    Returns:
        Dict: Filter scores and details
    """
    try:
        scores = {
            "basic_filters": filters_ok(row),
            "advanced_filters": advanced_filters_ok(row),
            "volume_confirmation": volume_confirmation(row),
            "trend_strength": trend_strength_filter(row),
            "volatility_ok": volatility_filter(row)
        }
        
        # Calculate overall score
        total_score = sum(scores.values())
        max_score = len(scores)
        overall_score = (total_score / max_score) * 100 if max_score > 0 else 0
        
        scores["overall_score"] = round(overall_score, 2)
        
        return scores
        
    except Exception as e:
        logger.error(f"Error calculating filter scores: {e}")
        return {"overall_score": 0}