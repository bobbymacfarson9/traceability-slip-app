import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class HolidayAwareForecaster:
    """Holiday-aware forecaster that detects and handles holiday scenarios"""
    
    def __init__(self):
        self.name = "Holiday Aware"
        self.description = "Hybrid Smart with holiday detection and handling"
        
        # Holiday detection thresholds (if total demand < threshold, likely holiday)
        self.holiday_thresholds = {
            'Mon': 1000,   # If Monday < 1000 boxes, likely holiday
            'Tues': 800,   # If Tuesday < 800 boxes, likely holiday
            'Wed': 600,    # If Wednesday < 600 boxes, likely holiday
            'Thurs': 800,  # If Thursday < 800 boxes, likely holiday
            'Fri': 1000    # If Friday < 1000 boxes, likely holiday
        }
        
        # Holiday adjustment factors (reduction percentages)
        self.holiday_factors = {
            'Mon': 0.3,    # 70% reduction for Monday holidays
            'Tues': 0.2,   # 80% reduction for Tuesday holidays
            'Wed': 0.1,    # 90% reduction for Wednesday holidays
            'Thurs': 0.2,  # 80% reduction for Thursday holidays
            'Fri': 0.3     # 70% reduction for Friday holidays
        }
        
        # Minimum forecast thresholds to prevent extreme under-prediction
        self.min_forecast_thresholds = {
            'Mon': 200,    # Minimum 200 boxes for Monday
            'Tues': 150,   # Minimum 150 boxes for Tuesday
            'Wed': 100,    # Minimum 100 boxes for Wednesday
            'Thurs': 150,  # Minimum 150 boxes for Thursday
            'Fri': 200     # Minimum 200 boxes for Friday
        }
    
    def _detect_holiday_scenario(self, day: str, historical_data: pd.DataFrame) -> bool:
        """Detect if this might be a holiday scenario based on historical patterns"""
        
        if len(historical_data) < 3:
            return False
        
        # Calculate recent average demand
        recent_avg = historical_data['boxes'].sum()
        threshold = self.holiday_thresholds.get(day, 1000)
        
        # If recent average is very low, likely holiday scenario
        return recent_avg < threshold
    
    def _apply_holiday_adjustment(self, base_forecast: float, day: str, 
                                historical_data: pd.DataFrame) -> float:
        """Apply holiday adjustment if holiday scenario detected"""
        
        if not self._detect_holiday_scenario(day, historical_data):
            return base_forecast
        
        # Apply holiday reduction
        holiday_factor = self.holiday_factors.get(day, 0.2)
        adjusted_forecast = base_forecast * holiday_factor
        
        # Ensure minimum threshold
        min_threshold = self.min_forecast_thresholds.get(day, 100)
        return max(adjusted_forecast, min_threshold)
    
    def _calculate_base_forecast(self, product_data: pd.DataFrame) -> float:
        """Calculate base forecast using weighted average"""
        if len(product_data) == 0:
            return 0.0
        
        # Use weighted average favoring recent weeks
        weights = np.exp(np.linspace(-1, 0, len(product_data)))
        weights = weights / weights.sum()
        return np.average(product_data['boxes'].values, weights=weights)
    
    def _detect_extreme_outliers(self, product_data: pd.DataFrame) -> pd.DataFrame:
        """Detect and remove extreme outliers from historical data"""
        if len(product_data) < 5:
            return product_data
        
        # Use IQR method for outlier detection
        Q1 = product_data['boxes'].quantile(0.25)
        Q3 = product_data['boxes'].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier bounds (conservative)
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Filter out extreme outliers
        filtered_data = product_data[
            (product_data['boxes'] >= lower_bound) & 
            (product_data['boxes'] <= upper_bound)
        ]
        
        # If we filtered out too much data, use original
        if len(filtered_data) < len(product_data) * 0.3:
            return product_data
        
        return filtered_data
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, window: int = 6, **kwargs) -> pd.DataFrame:
        """Generate forecast with holiday awareness"""
        
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
        
        # Check for holiday scenario
        is_holiday = self._detect_holiday_scenario(day, recent_data)
        
        # Calculate forecasts for each product
        forecasts = []
        
        for product in recent_data['product'].unique():
            product_data = recent_data[recent_data['product'] == product]
            
            if len(product_data) == 0:
                continue
            
            # Remove extreme outliers
            clean_product_data = self._detect_extreme_outliers(product_data)
            
            # Base forecast
            base_forecast = self._calculate_base_forecast(clean_product_data)
            
            # Apply holiday adjustment
            final_forecast = self._apply_holiday_adjustment(base_forecast, day, clean_product_data)
            
            # Round to integer
            final_forecast = int(round(max(0, final_forecast)))
            
            forecasts.append({
                'product': product,
                'forecast_boxes': final_forecast
            })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

def test_holiday_aware_forecaster():
    """Test the holiday-aware forecaster"""
    print("=== TESTING HOLIDAY-AWARE FORECASTER ===")
    
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
    holiday_method = HolidayAwareForecaster()
    
    print(f"🧪 Testing on {test_week['week_file']} (Christmas week)...")
    
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
        
        # Test Holiday method
        holiday_forecast = holiday_method.forecast_weekday(history_df, day, test_week['year'], test_week['week_num'])
        holiday_total = holiday_forecast['forecast_boxes'].sum()
        holiday_error = abs(holiday_total - day_actual) / day_actual * 100 if day_actual > 0 else 0
        
        improvement = hybrid_error - holiday_error
        
        results.append({
            'day': day,
            'actual': day_actual,
            'hybrid_forecast': hybrid_total,
            'hybrid_error': hybrid_error,
            'holiday_forecast': holiday_total,
            'holiday_error': holiday_error,
            'improvement': improvement
        })
        
        print(f"   {day}:")
        print(f"     Actual: {day_actual:.0f}")
        print(f"     Hybrid: {hybrid_total:.0f} ({hybrid_error:.1f}%)")
        print(f"     Holiday: {holiday_total:.0f} ({holiday_error:.1f}%)")
        print(f"     Improvement: {improvement:+.1f}pp")
        print()
    
    # Overall results
    total_actual = sum(r['actual'] for r in results)
    total_hybrid = sum(r['hybrid_forecast'] for r in results)
    total_holiday = sum(r['holiday_forecast'] for r in results)
    
    overall_hybrid_error = abs(total_hybrid - total_actual) / total_actual * 100
    overall_holiday_error = abs(total_holiday - total_actual) / total_actual * 100
    overall_improvement = overall_hybrid_error - overall_holiday_error
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Actual: {total_actual:.0f}")
    print(f"   Hybrid Total: {total_hybrid:.0f} ({overall_hybrid_error:.1f}%)")
    print(f"   Holiday Total: {total_holiday:.0f} ({overall_holiday_error:.1f}%)")
    print(f"   Overall Improvement: {overall_improvement:+.1f}pp")
    
    if overall_improvement > 0:
        print(f"   ✅ Holiday-aware forecaster shows improvement!")
    else:
        print(f"   ⚠️  Holiday-aware forecaster needs further tuning")
    
    return results

if __name__ == "__main__":
    test_holiday_aware_forecaster()
