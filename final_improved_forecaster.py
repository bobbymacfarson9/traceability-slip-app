import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class FinalImprovedForecaster:
    """Final improved forecaster with simple but effective holiday handling"""
    
    def __init__(self):
        self.name = "Final Improved"
        self.description = "Hybrid Smart with simple holiday detection and conservative forecasting"
        
        # Simple holiday detection: if total demand < threshold, apply conservative forecast
        self.holiday_thresholds = {
            'Mon': 500,    # If Monday < 500 boxes, likely holiday
            'Tues': 400,   # If Tuesday < 400 boxes, likely holiday
            'Wed': 300,    # If Wednesday < 300 boxes, likely holiday
            'Thurs': 400,  # If Thursday < 400 boxes, likely holiday
            'Fri': 500     # If Friday < 500 boxes, likely holiday
        }
        
        # Conservative holiday forecasts (much lower than normal)
        self.holiday_forecasts = {
            'Mon': 300,    # Conservative Monday holiday forecast
            'Tues': 200,   # Conservative Tuesday holiday forecast
            'Wed': 100,    # Conservative Wednesday holiday forecast
            'Thurs': 200,  # Conservative Thursday holiday forecast
            'Fri': 300     # Conservative Friday holiday forecast
        }
    
    def _detect_holiday_scenario(self, day: str, historical_data: pd.DataFrame) -> bool:
        """Simple holiday detection based on total demand"""
        
        if len(historical_data) == 0:
            return False
        
        # Calculate total demand for this day
        total_demand = historical_data['boxes'].sum()
        threshold = self.holiday_thresholds.get(day, 500)
        
        return total_demand < threshold
    
    def _get_holiday_forecast(self, day: str) -> float:
        """Get conservative holiday forecast for a day"""
        return self.holiday_forecasts.get(day, 200)
    
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
        """Generate forecast with simple holiday handling"""
        
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
        
        if is_holiday:
            # Use conservative holiday forecast
            print(f"   🎄 Holiday detected for {day} - using conservative forecast")
            total_holiday_forecast = self._get_holiday_forecast(day)
            
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

def test_final_improved_forecaster():
    """Test the final improved forecaster"""
    print("=== TESTING FINAL IMPROVED FORECASTER ===")
    
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
    final_method = FinalImprovedForecaster()
    
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
        
        # Test Final method
        final_forecast = final_method.forecast_weekday(history_df, day, test_week['year'], test_week['week_num'])
        final_total = final_forecast['forecast_boxes'].sum()
        final_error = abs(final_total - day_actual) / day_actual * 100 if day_actual > 0 else 0
        
        improvement = hybrid_error - final_error
        
        results.append({
            'day': day,
            'actual': day_actual,
            'hybrid_forecast': hybrid_total,
            'hybrid_error': hybrid_error,
            'final_forecast': final_total,
            'final_error': final_error,
            'improvement': improvement
        })
        
        print(f"   {day}:")
        print(f"     Actual: {day_actual:.0f}")
        print(f"     Hybrid: {hybrid_total:.0f} ({hybrid_error:.1f}%)")
        print(f"     Final: {final_total:.0f} ({final_error:.1f}%)")
        print(f"     Improvement: {improvement:+.1f}pp")
        print()
    
    # Overall results
    total_actual = sum(r['actual'] for r in results)
    total_hybrid = sum(r['hybrid_forecast'] for r in results)
    total_final = sum(r['final_forecast'] for r in results)
    
    overall_hybrid_error = abs(total_hybrid - total_actual) / total_actual * 100
    overall_final_error = abs(total_final - total_actual) / total_actual * 100
    overall_improvement = overall_hybrid_error - overall_final_error
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Actual: {total_actual:.0f}")
    print(f"   Hybrid Total: {total_hybrid:.0f} ({overall_hybrid_error:.1f}%)")
    print(f"   Final Total: {total_final:.0f} ({overall_final_error:.1f}%)")
    print(f"   Overall Improvement: {overall_improvement:+.1f}pp")
    
    if overall_improvement > 0:
        print(f"   ✅ Final improved forecaster shows improvement!")
    else:
        print(f"   ⚠️  Final improved forecaster needs further tuning")
    
    return results

if __name__ == "__main__":
    test_final_improved_forecaster()
