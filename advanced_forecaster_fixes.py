import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class AdvancedForecasterFixes:
    """Advanced forecaster with fixes for extreme low-demand scenarios"""
    
    def __init__(self):
        self.name = "Advanced Fixes"
        self.description = "Hybrid Smart with advanced fixes for extreme scenarios"
        
        # Minimum forecast thresholds to prevent extreme over-prediction
        self.min_forecast_thresholds = {
            'Mon': 50,    # Minimum 50 boxes for Monday
            'Tues': 30,   # Minimum 30 boxes for Tuesday  
            'Wed': 20,    # Minimum 20 boxes for Wednesday
            'Thurs': 30,  # Minimum 30 boxes for Thursday
            'Fri': 40     # Minimum 40 boxes for Friday
        }
        
        # Holiday detection thresholds (if total demand < threshold, likely holiday)
        self.holiday_thresholds = {
            'Mon': 100,   # If Monday < 100 boxes, likely holiday
            'Tues': 80,   # If Tuesday < 80 boxes, likely holiday
            'Wed': 60,    # If Wednesday < 60 boxes, likely holiday
            'Thurs': 80,  # If Thursday < 80 boxes, likely holiday
            'Fri': 100    # If Friday < 100 boxes, likely holiday
        }
        
        # Volatility-based adjustments
        self.volatility_thresholds = {
            'low': 0.3,    # CV < 0.3 = low volatility
            'medium': 0.6, # CV 0.3-0.6 = medium volatility
            'high': 1.0    # CV > 1.0 = high volatility
        }
    
    def _detect_holiday_scenario(self, day: str, historical_data: pd.DataFrame) -> bool:
        """Detect if this might be a holiday scenario based on historical patterns"""
        
        if len(historical_data) < 3:
            return False
        
        # Calculate recent average demand
        recent_avg = historical_data['boxes'].mean()
        threshold = self.holiday_thresholds.get(day, 100)
        
        # If recent average is very low, likely holiday scenario
        return recent_avg < threshold
    
    def _calculate_volatility_category(self, product_data: pd.DataFrame) -> str:
        """Calculate volatility category for a product"""
        if len(product_data) < 3:
            return 'medium'
        
        cv = product_data['boxes'].std() / product_data['boxes'].mean() if product_data['boxes'].mean() > 0 else 0
        
        if cv < self.volatility_thresholds['low']:
            return 'low'
        elif cv < self.volatility_thresholds['medium']:
            return 'medium'
        else:
            return 'high'
    
    def _apply_holiday_adjustment(self, base_forecast: float, day: str, 
                                historical_data: pd.DataFrame) -> float:
        """Apply holiday adjustment if holiday scenario detected"""
        
        if not self._detect_holiday_scenario(day, historical_data):
            return base_forecast
        
        # Apply conservative holiday reduction (60-80% reduction)
        holiday_factor = 0.3  # 70% reduction
        adjusted_forecast = base_forecast * holiday_factor
        
        # Ensure minimum threshold
        min_threshold = self.min_forecast_thresholds.get(day, 20)
        return max(adjusted_forecast, min_threshold)
    
    def _apply_volatility_adjustment(self, base_forecast: float, product: str, 
                                   product_data: pd.DataFrame) -> float:
        """Apply volatility-based adjustment"""
        
        volatility = self._calculate_volatility_category(product_data)
        
        if volatility == 'high':
            # For high volatility products, use more conservative forecasting
            # Use median instead of mean, and apply additional smoothing
            if len(product_data) >= 3:
                median_forecast = product_data['boxes'].median()
                # Blend mean and median (70% median, 30% mean)
                adjusted_forecast = 0.7 * median_forecast + 0.3 * base_forecast
                return adjusted_forecast
        
        return base_forecast
    
    def _apply_minimum_thresholds(self, forecast: float, day: str) -> float:
        """Apply minimum forecast thresholds to prevent extreme under-prediction"""
        min_threshold = self.min_forecast_thresholds.get(day, 20)
        return max(forecast, min_threshold)
    
    def _detect_extreme_outliers(self, product_data: pd.DataFrame) -> pd.DataFrame:
        """Detect and remove extreme outliers from historical data"""
        if len(product_data) < 5:
            return product_data
        
        # Use IQR method for outlier detection
        Q1 = product_data['boxes'].quantile(0.25)
        Q3 = product_data['boxes'].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier bounds (more conservative than standard 1.5*IQR)
        lower_bound = Q1 - 2.0 * IQR
        upper_bound = Q3 + 2.0 * IQR
        
        # Filter out extreme outliers
        filtered_data = product_data[
            (product_data['boxes'] >= lower_bound) & 
            (product_data['boxes'] <= upper_bound)
        ]
        
        # If we filtered out too much data, use original
        if len(filtered_data) < len(product_data) * 0.5:
            return product_data
        
        return filtered_data
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, window: int = 6, **kwargs) -> pd.DataFrame:
        """Generate forecast with advanced fixes"""
        
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
            
            # Remove extreme outliers
            clean_product_data = self._detect_extreme_outliers(product_data)
            
            # Base forecast using weighted average
            weights = np.exp(np.linspace(-1, 0, len(clean_product_data)))
            weights = weights / weights.sum()
            base_forecast = np.average(clean_product_data['boxes'].values, weights=weights)
            
            # Apply volatility adjustment
            base_forecast = self._apply_volatility_adjustment(base_forecast, product, clean_product_data)
            
            # Apply holiday adjustment
            base_forecast = self._apply_holiday_adjustment(base_forecast, day, clean_product_data)
            
            # Apply minimum thresholds
            base_forecast = self._apply_minimum_thresholds(base_forecast, day)
            
            # Round to integer
            final_forecast = int(round(max(0, base_forecast)))
            
            forecasts.append({
                'product': product,
                'forecast_boxes': final_forecast
            })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

def test_advanced_fixes():
    """Test the advanced fixes on problematic scenarios"""
    print("=== TESTING ADVANCED FIXES ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test on Week 51 (the problematic week)
    test_week = {'week_file': 'Week 51 Loading Slip 2024.xlsx', 'week_num': 51, 'year': 2024}
    
    test_file = Path(test_week['week_file'])
    if not test_file.exists():
        print(f"❌ Test file {test_week['week_file']} not found")
        return False
    
    # Test both methods
    from smart_bias_forecaster import HybridForecaster
    
    hybrid_method = HybridForecaster()
    advanced_method = AdvancedForecasterFixes()
    
    print(f"🧪 Testing on {test_week['week_file']}...")
    
    results = []
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        # Get actual data
        actual_data = parse_daily_totals_universal(test_file, day)
        if actual_data.empty:
            continue
        
        day_actual = actual_data['boxes'].sum()
        
        # Test Hybrid method
        hybrid_forecast = hybrid_method.forecast_weekday(history_df, day, test_week['year'], test_week['week_num'])
        hybrid_total = hybrid_forecast['forecast_boxes'].sum()
        hybrid_error = abs(hybrid_total - day_actual) / day_actual * 100 if day_actual > 0 else 0
        
        # Test Advanced method
        advanced_forecast = advanced_method.forecast_weekday(history_df, day, test_week['year'], test_week['week_num'])
        advanced_total = advanced_forecast['forecast_boxes'].sum()
        advanced_error = abs(advanced_total - day_actual) / day_actual * 100 if day_actual > 0 else 0
        
        improvement = hybrid_error - advanced_error
        
        results.append({
            'day': day,
            'actual': day_actual,
            'hybrid_forecast': hybrid_total,
            'hybrid_error': hybrid_error,
            'advanced_forecast': advanced_total,
            'advanced_error': advanced_error,
            'improvement': improvement
        })
        
        print(f"   {day}:")
        print(f"     Actual: {day_actual:.0f}")
        print(f"     Hybrid: {hybrid_total:.0f} ({hybrid_error:.1f}%)")
        print(f"     Advanced: {advanced_total:.0f} ({advanced_error:.1f}%)")
        print(f"     Improvement: {improvement:+.1f}pp")
        print()
    
    # Overall results
    total_actual = sum(r['actual'] for r in results)
    total_hybrid = sum(r['hybrid_forecast'] for r in results)
    total_advanced = sum(r['advanced_forecast'] for r in results)
    
    overall_hybrid_error = abs(total_hybrid - total_actual) / total_actual * 100
    overall_advanced_error = abs(total_advanced - total_actual) / total_actual * 100
    overall_improvement = overall_hybrid_error - overall_advanced_error
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Actual: {total_actual:.0f}")
    print(f"   Hybrid Total: {total_hybrid:.0f} ({overall_hybrid_error:.1f}%)")
    print(f"   Advanced Total: {total_advanced:.0f} ({overall_advanced_error:.1f}%)")
    print(f"   Overall Improvement: {overall_improvement:+.1f}pp")
    
    if overall_improvement > 0:
        print(f"   ✅ Advanced fixes show improvement!")
    else:
        print(f"   ⚠️  Advanced fixes need further tuning")
    
    return results

if __name__ == "__main__":
    test_advanced_fixes()
