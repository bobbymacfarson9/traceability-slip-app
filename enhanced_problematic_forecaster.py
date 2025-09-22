import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class EnhancedProblematicForecaster:
    """Enhanced forecaster with targeted solutions for problematic products"""
    
    def __init__(self):
        self.name = "Enhanced Problematic"
        self.description = "Hybrid Smart with targeted fixes for problematic products"
        
        # Product-specific configurations based on analysis
        self.product_configs = {
            'ED 18 LG': {
                'volatility': 'high',  # CV = 1.44
                'trend': 'decreasing',  # -28.9 boxes trend
                'day_patterns': 'strong',  # Strong day-of-week patterns
                'historical_window': 10,  # Use longer window
                'method': 'weighted_median',  # Use median for volatility
                'trend_adjustment': True,
                'day_adjustments': {
                    'Mon': 0, 'Tues': 0, 'Wed': 0, 'Thurs': 0, 'Fri': -15  # Friday under-predicted
                }
            },
            'ED 18 XL': {
                'volatility': 'medium',  # CV = 0.46
                'trend': 'decreasing',  # -6.1 boxes trend
                'day_patterns': 'moderate',  # Moderate day patterns
                'historical_window': 8,
                'method': 'weighted_average',
                'trend_adjustment': True,
                'day_adjustments': {
                    'Mon': 0, 'Tues': 0, 'Wed': 0, 'Thurs': -20, 'Fri': 0  # Thursday over-predicted
                }
            },
            'Wal GV Lg': {
                'volatility': 'medium',  # CV = 0.41
                'trend': 'decreasing',  # -9.7 boxes trend
                'day_patterns': 'moderate',
                'historical_window': 8,
                'method': 'weighted_average',
                'trend_adjustment': True,
                'day_adjustments': {
                    'Mon': -10, 'Tues': 0, 'Wed': 0, 'Thurs': 0, 'Fri': 0  # Monday over-predicted
                }
            },
            'Lob Lg': {
                'volatility': 'high',  # CV = 0.80
                'trend': 'decreasing',  # -37.7 boxes trend
                'day_patterns': 'strong',  # Strong day patterns
                'historical_window': 10,
                'method': 'weighted_median',
                'trend_adjustment': True,
                'day_adjustments': {
                    'Mon': 0, 'Tues': -5, 'Wed': 0, 'Thurs': 0, 'Fri': -5  # Tues/Fri over-predicted
                }
            },
            'OC 30 Lrg': {
                'volatility': 'high',  # CV = 0.59
                'trend': 'increasing',  # +11.1 boxes trend
                'day_patterns': 'strong',  # Strong day patterns
                'historical_window': 8,
                'method': 'weighted_average',
                'trend_adjustment': True,
                'day_adjustments': {
                    'Mon': 0, 'Tues': 0, 'Wed': 0, 'Thurs': -10, 'Fri': 0  # Thursday over-predicted
                }
            }
        }
        
        # Day-specific method preferences (from Hybrid Smart)
        self.day_methods = {
            'Mon': 'simple',
            'Tues': 'bias',
            'Wed': 'simple',
            'Thurs': 'simple',
            'Fri': 'bias'
        }
    
    def _get_volume_category(self, boxes: int) -> str:
        """Categorize product volume"""
        if boxes <= 10:
            return 'low'
        elif boxes <= 50:
            return 'medium'
        elif boxes <= 100:
            return 'high'
        else:
            return 'very_high'
    
    def _calculate_trend_adjustment(self, product_data: pd.DataFrame, config: Dict) -> float:
        """Calculate trend adjustment for a product"""
        if not config.get('trend_adjustment', False):
            return 0.0
        
        if len(product_data) < 6:
            return 0.0
        
        # Sort by date
        product_data_sorted = product_data.sort_values(['year', 'week_num'])
        
        # Get recent vs older data
        recent_data = product_data_sorted.tail(6)
        older_data = product_data_sorted.head(6)
        
        if len(recent_data) == 0 or len(older_data) == 0:
            return 0.0
        
        recent_avg = recent_data['boxes'].mean()
        older_avg = older_data['boxes'].mean()
        
        # Calculate trend (recent - older)
        trend = recent_avg - older_avg
        
        # Apply conservative trend adjustment (max 20% of current average)
        current_avg = product_data['boxes'].mean()
        max_adjustment = current_avg * 0.2
        
        # Scale trend adjustment
        trend_factor = min(1.0, abs(trend) / current_avg) if current_avg > 0 else 0
        adjustment = trend * trend_factor * 0.3  # Conservative 30% of trend
        
        return max(-max_adjustment, min(max_adjustment, adjustment))
    
    def _apply_product_specific_forecasting(self, product: str, product_data: pd.DataFrame, 
                                          config: Dict, day: str) -> float:
        """Apply product-specific forecasting method"""
        
        method = config.get('method', 'weighted_average')
        window = config.get('historical_window', 6)
        
        # Get recent data
        recent_data = product_data.tail(window)
        
        if len(recent_data) == 0:
            return 0.0
        
        if method == 'weighted_median':
            # Use median for high-volatility products
            base_forecast = recent_data['boxes'].median()
        elif method == 'weighted_average':
            # Use weighted average favoring recent weeks
            weights = np.exp(np.linspace(-1, 0, len(recent_data)))
            weights = weights / weights.sum()
            base_forecast = np.average(recent_data['boxes'].values, weights=weights)
        else:
            # Default to simple average
            base_forecast = recent_data['boxes'].mean()
        
        # Apply trend adjustment
        trend_adj = self._calculate_trend_adjustment(product_data, config)
        base_forecast += trend_adj
        
        # Apply day-specific adjustment
        day_adjustments = config.get('day_adjustments', {})
        if day in day_adjustments:
            base_forecast += day_adjustments[day]
        
        return max(0, base_forecast)
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, window: int = 6, **kwargs) -> pd.DataFrame:
        
        # Get historical data for this day
        day_data = history_df[history_df['day'] == day].copy()
        
        if len(day_data) < 2:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        # Sort by date
        day_data = day_data.sort_values(['year', 'week_num'])
        
        # Filter out data after target week
        day_data = day_data[
            (day_data['year'] < target_year) | 
            ((day_data['year'] == target_year) & (day_data['week_num'] < target_week))
        ]
        
        if len(day_data) == 0:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        # Get last N weeks (not records!)
        unique_weeks = day_data[['year', 'week_num']].drop_duplicates().sort_values(['year', 'week_num'])
        if len(unique_weeks) == 0:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        last_n_weeks = unique_weeks.tail(window)
        recent_data = day_data.merge(last_n_weeks, on=['year', 'week_num'])
        
        # Calculate forecasts for each product
        forecasts = []
        
        for product in recent_data['product'].unique():
            product_data = recent_data[recent_data['product'] == product]
            
            if len(product_data) == 0:
                continue
            
            # Check if this is a problematic product
            if product in self.product_configs:
                # Use enhanced forecasting for problematic products
                config = self.product_configs[product]
                forecast = self._apply_product_specific_forecasting(product, product_data, config, day)
            else:
                # Use standard forecasting for other products
                # Choose method based on day (from Hybrid Smart)
                method = self.day_methods.get(day, 'simple')
                
                if method == 'bias':
                    # Apply basic bias adjustments
                    base_forecast = product_data['boxes'].mean()
                    
                    # Day-specific adjustments
                    if day == 'Tues':
                        base_forecast += 2.5  # Under-predicts
                    elif day == 'Fri':
                        base_forecast += 1.0  # Slightly under-predicts
                    
                    forecast = base_forecast
                else:
                    # Simple average
                    forecast = product_data['boxes'].mean()
            
            forecasts.append({
                'product': product,
                'forecast_boxes': int(round(forecast))
            })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

def test_enhanced_forecaster():
    """Test the enhanced forecaster on problematic products"""
    print("=== TESTING ENHANCED PROBLEMATIC FORECASTER ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test weeks (same as our study)
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Import methods for comparison
    from smart_bias_forecaster import HybridForecaster
    hybrid_method = HybridForecaster()
    enhanced_method = EnhancedProblematicForecaster()
    
    # Focus on problematic products
    problematic_products = ['ED 18 LG', 'ED 18 XL', 'Wal GV Lg', 'Lob Lg', 'OC 30 Lrg']
    
    # Collect results
    hybrid_errors = []
    enhanced_errors = []
    
    print(f"Testing on {len(problematic_products)} problematic products...")
    
    for week_info in test_weeks:
        week_file = week_info['week_file']
        week_num = week_info['week_num']
        year = week_info['year']
        
        test_file = Path(week_file)
        if not test_file.exists():
            continue
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                continue
            
            # Filter to problematic products only
            actual_problematic = actual_data[actual_data['product'].isin(problematic_products)]
            if actual_problematic.empty:
                continue
            
            total_actual = actual_problematic['boxes'].sum()
            
            # Test Hybrid method
            hybrid_forecast = hybrid_method.forecast_weekday(history_df, day, year, week_num)
            hybrid_problematic = hybrid_forecast[hybrid_forecast['product'].isin(problematic_products)]
            hybrid_total = hybrid_problematic['forecast_boxes'].sum()
            hybrid_error = abs(hybrid_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            hybrid_errors.append(hybrid_error)
            
            # Test Enhanced method
            enhanced_forecast = enhanced_method.forecast_weekday(history_df, day, year, week_num)
            enhanced_problematic = enhanced_forecast[enhanced_forecast['product'].isin(problematic_products)]
            enhanced_total = enhanced_problematic['forecast_boxes'].sum()
            enhanced_error = abs(enhanced_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            enhanced_errors.append(enhanced_error)
            
            if total_actual > 0:  # Only show if there's actual data
                improvement = hybrid_error - enhanced_error
                print(f"{week_file} {day}: Hybrid {hybrid_total:.0f} ({hybrid_error:.1f}%) → Enhanced {enhanced_total:.0f} ({enhanced_error:.1f}%) → {improvement:+.1f}pp")
    
    # Overall results
    print(f"\n{'='*70}")
    print(f"ENHANCED FORECASTER RESULTS (Problematic Products Only)")
    print(f"{'='*70}")
    
    hybrid_avg_error = np.mean(hybrid_errors)
    enhanced_avg_error = np.mean(enhanced_errors)
    overall_improvement = hybrid_avg_error - enhanced_avg_error
    improvement_pct = (overall_improvement / hybrid_avg_error) * 100
    
    print(f"Hybrid Smart Error:     {hybrid_avg_error:.1f}%")
    print(f"Enhanced Error:         {enhanced_avg_error:.1f}%")
    print(f"Overall Improvement:    {overall_improvement:+.1f}pp ({improvement_pct:+.1f}% better)")
    
    # Count improvements
    improvements = [enhanced_errors[i] < hybrid_errors[i] for i in range(len(hybrid_errors))]
    improvement_count = sum(improvements)
    total_tests = len(improvements)
    
    print(f"Days improved: {improvement_count}/{total_tests} ({improvement_count/total_tests*100:.1f}%)")
    
    return hybrid_errors, enhanced_errors, overall_improvement

if __name__ == "__main__":
    test_enhanced_forecaster()
