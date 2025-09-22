import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class BiasAdjustedForecaster:
    """Bias-adjusted forecasting method based on error pattern analysis"""
    
    def __init__(self):
        self.name = "Bias Adjusted"
        self.description = "Simple Average with systematic bias corrections"
        
        # Bias adjustments based on our analysis
        self.day_adjustments = {
            'Mon': 0.1,      # Slightly over-predicts
            'Tues': 2.8,     # Under-predicts significantly
            'Wed': 0.1,      # Slightly under-predicts
            'Thurs': -0.3,   # Slightly over-predicts
            'Fri': 1.5       # Under-predicts
        }
        
        self.product_adjustments = {
            # Products consistently over-predicted (reduce forecast)
            'Wal GV Lg': -7.2,
            'Lob Lg': -1.3,
            
            # Products consistently under-predicted (increase forecast)
            'ED 18 LG': 4.6,
            'ED Jum': 2.3,
            'Eyk Lg': 3.5,
            'Lob 30 Lg': 6.2,
            'OC 30 Lrg': 2.6,
        }
        
        # Volume-based adjustments
        self.volume_adjustments = {
            'low': -1.2,      # Over-predicts low volume products
            'medium': -1.5,   # Over-predicts medium volume products
            'high': 9.4,      # Under-predicts high volume products
            'very_high': 21.0 # Under-predicts very high volume products
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
        
        # Calculate simple average by product
        forecasts = recent_data.groupby('product')['boxes'].mean().round().astype(int).reset_index()
        forecasts = forecasts.rename(columns={'boxes': 'forecast_boxes'})
        
        # Apply bias adjustments
        adjusted_forecasts = []
        
        for _, row in forecasts.iterrows():
            product = row['product']
            base_forecast = row['forecast_boxes']
            
            # Start with base forecast
            adjusted_forecast = base_forecast
            
            # Apply day-of-week adjustment
            if day in self.day_adjustments:
                day_adj = self.day_adjustments[day]
                adjusted_forecast += day_adj
            
            # Apply product-specific adjustment
            if product in self.product_adjustments:
                product_adj = self.product_adjustments[product]
                adjusted_forecast += product_adj
            
            # Apply volume-based adjustment
            volume_category = self._get_volume_category(base_forecast)
            if volume_category in self.volume_adjustments:
                volume_adj = self.volume_adjustments[volume_category]
                adjusted_forecast += volume_adj
            
            # Ensure non-negative
            adjusted_forecast = max(0, round(adjusted_forecast))
            
            adjusted_forecasts.append({
                'product': product,
                'forecast_boxes': adjusted_forecast
            })
        
        result = pd.DataFrame(adjusted_forecasts)
        return result.sort_values('product').reset_index(drop=True)

def test_bias_adjusted_forecaster():
    """Test the bias-adjusted forecaster against our study methods"""
    print("=== TESTING BIAS-ADJUSTED FORECASTER ===")
    
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
    
    # Import Simple Average for comparison
    from final_forecasting_study import Method1_SimpleAverage
    simple_method = Method1_SimpleAverage()
    bias_method = BiasAdjustedForecaster()
    
    # Collect results
    simple_errors = []
    bias_errors = []
    
    for week_info in test_weeks:
        week_file = week_info['week_file']
        week_num = week_info['week_num']
        year = week_info['year']
        
        print(f"\n{'='*60}")
        print(f"TESTING WEEK {week_num}, {year}")
        print(f"File: {week_file}")
        print(f"{'='*60}")
        
        test_file = Path(week_file)
        if not test_file.exists():
            print(f"File not found: {week_file}")
            continue
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            print(f"\n--- {day.upper()} ---")
            
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                print(f"No actual data for {day}")
                continue
            
            total_actual = actual_data['boxes'].sum()
            print(f"Actual: {total_actual} boxes ({len(actual_data)} products)")
            
            # Test Simple Average
            simple_forecast = simple_method.forecast_weekday(history_df, day, year, week_num)
            simple_total = simple_forecast['forecast_boxes'].sum()
            simple_error = abs(simple_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            simple_errors.append(simple_error)
            
            # Test Bias Adjusted
            bias_forecast = bias_method.forecast_weekday(history_df, day, year, week_num)
            bias_total = bias_forecast['forecast_boxes'].sum()
            bias_error = abs(bias_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            bias_errors.append(bias_error)
            
            improvement = simple_error - bias_error
            
            print(f"Simple Average: {simple_total:>4} boxes - Error: {simple_error:>6.1f}%")
            print(f"Bias Adjusted:  {bias_total:>4} boxes - Error: {bias_error:>6.1f}%")
            print(f"Improvement:    {improvement:>+6.1f} percentage points")
    
    # Overall results
    print(f"\n{'='*70}")
    print(f"BIAS-ADJUSTED FORECASTER RESULTS")
    print(f"{'='*70}")
    
    simple_avg_error = np.mean(simple_errors)
    bias_avg_error = np.mean(bias_errors)
    overall_improvement = simple_avg_error - bias_avg_error
    improvement_pct = (overall_improvement / simple_avg_error) * 100
    
    print(f"Simple Average Error: {simple_avg_error:.1f}%")
    print(f"Bias Adjusted Error:  {bias_avg_error:.1f}%")
    print(f"Overall Improvement:  {overall_improvement:+.1f} percentage points ({improvement_pct:+.1f}% better)")
    
    # Count improvements
    improvements = [bias_errors[i] < simple_errors[i] for i in range(len(simple_errors))]
    improvement_count = sum(improvements)
    total_tests = len(improvements)
    
    print(f"Days improved: {improvement_count}/{total_tests} ({improvement_count/total_tests*100:.1f}%)")
    
    # Show best improvements
    improvements_list = [(simple_errors[i] - bias_errors[i], i) for i in range(len(simple_errors))]
    improvements_list.sort(reverse=True)
    
    print(f"\n🎯 BEST IMPROVEMENTS:")
    for i, (improvement, idx) in enumerate(improvements_list[:5]):
        if improvement > 0:
            print(f"  {i+1}. {improvement:+.1f}pp improvement")
    
    return simple_errors, bias_errors, overall_improvement

if __name__ == "__main__":
    test_bias_adjusted_forecaster()
