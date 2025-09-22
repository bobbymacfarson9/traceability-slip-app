import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class UltimateForecaster:
    """Ultimate forecaster with extreme holiday handling"""
    
    def __init__(self):
        self.name = "Ultimate"
        self.description = "Hybrid Smart with extreme holiday detection and ultra-conservative forecasting"
        
        # Extreme holiday detection: if total demand < threshold, use ultra-conservative forecast
        self.extreme_holiday_thresholds = {
            'Mon': 1000,   # If Monday < 1000 boxes, extreme holiday
            'Tues': 800,   # If Tuesday < 800 boxes, extreme holiday
            'Wed': 500,    # If Wednesday < 500 boxes, extreme holiday
            'Thurs': 800,  # If Thursday < 800 boxes, extreme holiday
            'Fri': 1000    # If Friday < 1000 boxes, extreme holiday
        }
        
        # Ultra-conservative holiday forecasts
        self.extreme_holiday_forecasts = {
            'Mon': 200,    # Ultra-conservative Monday holiday forecast
            'Tues': 150,   # Ultra-conservative Tuesday holiday forecast
            'Wed': 50,     # Ultra-conservative Wednesday holiday forecast
            'Thurs': 50,   # Ultra-conservative Thursday holiday forecast
            'Fri': 200     # Ultra-conservative Friday holiday forecast
        }
        
        # Regular holiday detection (less extreme)
        self.regular_holiday_thresholds = {
            'Mon': 2000,   # If Monday < 2000 boxes, regular holiday
            'Tues': 1500,  # If Tuesday < 1500 boxes, regular holiday
            'Wed': 1000,   # If Wednesday < 1000 boxes, regular holiday
            'Thurs': 1500, # If Thursday < 1500 boxes, regular holiday
            'Fri': 2000    # If Friday < 2000 boxes, regular holiday
        }
        
        # Regular holiday forecasts
        self.regular_holiday_forecasts = {
            'Mon': 800,    # Regular Monday holiday forecast
            'Tues': 600,   # Regular Tuesday holiday forecast
            'Wed': 400,    # Regular Wednesday holiday forecast
            'Thurs': 600,  # Regular Thursday holiday forecast
            'Fri': 800     # Regular Friday holiday forecast
        }
    
    def _detect_holiday_type(self, day: str, historical_data: pd.DataFrame) -> str:
        """Detect type of holiday scenario"""
        
        if len(historical_data) == 0:
            return 'normal'
        
        # Calculate total demand for this day
        total_demand = historical_data['boxes'].sum()
        
        # Check for extreme holiday
        extreme_threshold = self.extreme_holiday_thresholds.get(day, 500)
        if total_demand < extreme_threshold:
            return 'extreme_holiday'
        
        # Check for regular holiday
        regular_threshold = self.regular_holiday_thresholds.get(day, 1000)
        if total_demand < regular_threshold:
            return 'regular_holiday'
        
        return 'normal'
    
    def _get_holiday_forecast(self, day: str, holiday_type: str) -> float:
        """Get holiday forecast based on type"""
        if holiday_type == 'extreme_holiday':
            return self.extreme_holiday_forecasts.get(day, 50)
        elif holiday_type == 'regular_holiday':
            return self.regular_holiday_forecasts.get(day, 200)
        else:
            return 0.0
    
    def _calculate_normal_forecast(self, product_data: pd.DataFrame) -> float:
        """Calculate normal forecast using weighted average"""
        if len(product_data) == 0:
            return 0.0
        
        # Use weighted average favoring recent weeks
        weights = np.exp(np.linspace(-1, 0, len(product_data)))
        weights = weights / weights.sum()
        return np.average(product_data['boxes'].values, weights=weights)
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, window: int = 6, **kwargs) -> pd.DataFrame:
        """Generate forecast with ultimate holiday handling"""
        
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
        holiday_type = self._detect_holiday_type(day, recent_data)
        
        if holiday_type != 'normal':
            # Use holiday forecast
            print(f"   🎄 {holiday_type.replace('_', ' ').title()} detected for {day}")
            total_holiday_forecast = self._get_holiday_forecast(day, holiday_type)
            
            # Distribute holiday forecast proportionally across products
            forecasts = []
            for product in recent_data['product'].unique():
                product_data = recent_data[recent_data['product'] == product]
                if len(product_data) == 0:
                    continue
                
                # Calculate product's share of historical demand
                product_avg = product_data['boxes'].mean()
                total_avg = recent_data['boxes'].mean()
                product_share = product_avg / total_avg if total_avg > 0 else 0
                
                # Apply share to holiday forecast
                product_forecast = total_holiday_forecast * product_share
                product_forecast = max(0, int(round(product_forecast)))
                
                forecasts.append({
                    'product': product,
                    'forecast_boxes': product_forecast
                })
        else:
            # Use normal forecasting
            forecasts = []
            for product in recent_data['product'].unique():
                product_data = recent_data[recent_data['product'] == product]
                
                if len(product_data) == 0:
                    continue
                
                # Normal forecast
                base_forecast = self._calculate_normal_forecast(product_data)
                final_forecast = int(round(max(0, base_forecast)))
                
                forecasts.append({
                    'product': product,
                    'forecast_boxes': final_forecast
                })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

def test_ultimate_forecaster():
    """Test the ultimate forecaster"""
    print("=== TESTING ULTIMATE FORECASTER ===")
    
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
    ultimate_method = UltimateForecaster()
    
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
        
        # Test Ultimate method
        ultimate_forecast = ultimate_method.forecast_weekday(history_df, day, test_week['year'], test_week['week_num'])
        ultimate_total = ultimate_forecast['forecast_boxes'].sum()
        ultimate_error = abs(ultimate_total - day_actual) / day_actual * 100 if day_actual > 0 else 0
        
        improvement = hybrid_error - ultimate_error
        
        results.append({
            'day': day,
            'actual': day_actual,
            'hybrid_forecast': hybrid_total,
            'hybrid_error': hybrid_error,
            'ultimate_forecast': ultimate_total,
            'ultimate_error': ultimate_error,
            'improvement': improvement
        })
        
        print(f"   {day}:")
        print(f"     Actual: {day_actual:.0f}")
        print(f"     Hybrid: {hybrid_total:.0f} ({hybrid_error:.1f}%)")
        print(f"     Ultimate: {ultimate_total:.0f} ({ultimate_error:.1f}%)")
        print(f"     Improvement: {improvement:+.1f}pp")
        print()
    
    # Overall results
    total_actual = sum(r['actual'] for r in results)
    total_hybrid = sum(r['hybrid_forecast'] for r in results)
    total_ultimate = sum(r['ultimate_forecast'] for r in results)
    
    overall_hybrid_error = abs(total_hybrid - total_actual) / total_actual * 100
    overall_ultimate_error = abs(total_ultimate - total_actual) / total_actual * 100
    overall_improvement = overall_hybrid_error - overall_ultimate_error
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Actual: {total_actual:.0f}")
    print(f"   Hybrid Total: {total_hybrid:.0f} ({overall_hybrid_error:.1f}%)")
    print(f"   Ultimate Total: {total_ultimate:.0f} ({overall_ultimate_error:.1f}%)")
    print(f"   Overall Improvement: {overall_improvement:+.1f}pp")
    
    if overall_improvement > 0:
        print(f"   ✅ Ultimate forecaster shows improvement!")
    else:
        print(f"   ⚠️  Ultimate forecaster needs further tuning")
    
    return results

if __name__ == "__main__":
    test_ultimate_forecaster()
