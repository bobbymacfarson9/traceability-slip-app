import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class SmartBiasForecaster:
    """Smart bias-adjusted forecasting method with conditional adjustments"""
    
    def __init__(self):
        self.name = "Smart Bias Adjusted"
        self.description = "Simple Average with smart conditional bias corrections"
        
        # More nuanced adjustments based on analysis
        self.day_adjustments = {
            'Mon': 0,        # Neutral
            'Tues': 2.5,     # Under-predicts significantly
            'Wed': 0,        # Neutral
            'Thurs': 0,      # Neutral
            'Fri': 1.0       # Slightly under-predicts
        }
        
        # Only adjust products with very clear patterns
        self.product_adjustments = {
            # Products consistently over-predicted (reduce forecast)
            'Wal GV Lg': -5.0,  # Reduced from -7.2
            
            # Products consistently under-predicted (increase forecast)
            'ED 18 LG': 3.0,    # Reduced from 4.6
            'ED Jum': 1.5,      # Reduced from 2.3
            'Eyk Lg': 2.0,      # Reduced from 3.5
            'Lob 30 Lg': 4.0,   # Reduced from 6.2
            'OC 30 Lrg': 1.5,   # Reduced from 2.6
        }
        
        # Volume-based adjustments (more conservative)
        self.volume_adjustments = {
            'low': -0.5,      # Slightly over-predicts low volume
            'medium': -1.0,   # Slightly over-predicts medium volume
            'high': 3.0,      # Under-predicts high volume
            'very_high': 8.0  # Under-predicts very high volume
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
    
    def _should_apply_adjustment(self, product: str, base_forecast: int, day: str) -> bool:
        """Determine if we should apply adjustments based on conditions"""
        
        # Don't adjust very small forecasts
        if base_forecast < 3:
            return False
        
        # Don't adjust if the adjustment would be too large relative to forecast
        if product in self.product_adjustments:
            adj = abs(self.product_adjustments[product])
            if adj > base_forecast * 0.5:  # Don't adjust more than 50% of forecast
                return False
        
        # Don't apply volume adjustments to very small forecasts
        volume_category = self._get_volume_category(base_forecast)
        if volume_category in self.volume_adjustments:
            adj = abs(self.volume_adjustments[volume_category])
            if adj > base_forecast * 0.3:  # Don't adjust more than 30% of forecast
                return False
        
        return True
    
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
        
        # Apply smart bias adjustments
        adjusted_forecasts = []
        
        for _, row in forecasts.iterrows():
            product = row['product']
            base_forecast = row['forecast_boxes']
            
            # Start with base forecast
            adjusted_forecast = base_forecast
            
            # Only apply adjustments if conditions are met
            if self._should_apply_adjustment(product, base_forecast, day):
                
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

class HybridForecaster:
    """Hybrid forecaster that chooses the best method per day"""
    
    def __init__(self):
        self.name = "Hybrid Smart"
        self.description = "Chooses best method per day based on historical performance"
        
        # Day-specific method preferences based on our analysis
        self.day_methods = {
            'Mon': 'simple',      # Simple Average works well
            'Tues': 'bias',       # Bias adjustment helps significantly
            'Wed': 'simple',      # Simple Average works well
            'Thurs': 'simple',    # Simple Average works well
            'Fri': 'bias'         # Bias adjustment helps
        }
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, window: int = 6, **kwargs) -> pd.DataFrame:
        
        # Choose method based on day
        method = self.day_methods.get(day, 'simple')
        
        if method == 'bias':
            # Use smart bias-adjusted method
            smart_bias = SmartBiasForecaster()
            return smart_bias.forecast_weekday(history_df, day, target_year, target_week, window)
        else:
            # Use simple average method
            from final_forecasting_study import Method1_SimpleAverage
            simple_method = Method1_SimpleAverage()
            return simple_method.forecast_weekday(history_df, day, target_year, target_week, window)

def test_smart_forecasters():
    """Test the smart forecasters"""
    print("=== TESTING SMART FORECASTERS ===")
    
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
    from final_forecasting_study import Method1_SimpleAverage
    simple_method = Method1_SimpleAverage()
    smart_bias_method = SmartBiasForecaster()
    hybrid_method = HybridForecaster()
    
    # Collect results
    simple_errors = []
    smart_bias_errors = []
    hybrid_errors = []
    
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
            
            # Test all methods
            simple_forecast = simple_method.forecast_weekday(history_df, day, year, week_num)
            simple_total = simple_forecast['forecast_boxes'].sum()
            simple_error = abs(simple_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            simple_errors.append(simple_error)
            
            smart_bias_forecast = smart_bias_method.forecast_weekday(history_df, day, year, week_num)
            smart_bias_total = smart_bias_forecast['forecast_boxes'].sum()
            smart_bias_error = abs(smart_bias_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            smart_bias_errors.append(smart_bias_error)
            
            hybrid_forecast = hybrid_method.forecast_weekday(history_df, day, year, week_num)
            hybrid_total = hybrid_forecast['forecast_boxes'].sum()
            hybrid_error = abs(hybrid_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            hybrid_errors.append(hybrid_error)
            
            print(f"Simple Average:    {simple_total:>4} boxes - Error: {simple_error:>6.1f}%")
            print(f"Smart Bias:        {smart_bias_total:>4} boxes - Error: {smart_bias_error:>6.1f}%")
            print(f"Hybrid Smart:      {hybrid_total:>4} boxes - Error: {hybrid_error:>6.1f}%")
            
            # Show best method for this day
            errors = [simple_error, smart_bias_error, hybrid_error]
            methods = ['Simple', 'Smart Bias', 'Hybrid']
            best_idx = errors.index(min(errors))
            print(f"Best for {day}:     {methods[best_idx]} ({min(errors):.1f}% error)")
    
    # Overall results
    print(f"\n{'='*70}")
    print(f"SMART FORECASTER RESULTS")
    print(f"{'='*70}")
    
    simple_avg_error = np.mean(simple_errors)
    smart_bias_avg_error = np.mean(smart_bias_errors)
    hybrid_avg_error = np.mean(hybrid_errors)
    
    print(f"Simple Average Error:    {simple_avg_error:.1f}%")
    print(f"Smart Bias Error:        {smart_bias_avg_error:.1f}%")
    print(f"Hybrid Smart Error:      {hybrid_avg_error:.1f}%")
    
    # Improvements
    smart_improvement = simple_avg_error - smart_bias_avg_error
    hybrid_improvement = simple_avg_error - hybrid_avg_error
    
    print(f"\nSmart Bias Improvement:  {smart_improvement:+.1f}pp ({(smart_improvement/simple_avg_error*100):+.1f}%)")
    print(f"Hybrid Smart Improvement: {hybrid_improvement:+.1f}pp ({(hybrid_improvement/simple_avg_error*100):+.1f}%)")
    
    # Count improvements
    smart_improvements = [smart_bias_errors[i] < simple_errors[i] for i in range(len(simple_errors))]
    hybrid_improvements = [hybrid_errors[i] < simple_errors[i] for i in range(len(simple_errors))]
    
    print(f"\nSmart Bias improved:     {sum(smart_improvements)}/{len(smart_improvements)} days ({sum(smart_improvements)/len(smart_improvements)*100:.1f}%)")
    print(f"Hybrid Smart improved:   {sum(hybrid_improvements)}/{len(hybrid_improvements)} days ({sum(hybrid_improvements)/len(hybrid_improvements)*100:.1f}%)")
    
    return simple_errors, smart_bias_errors, hybrid_errors

if __name__ == "__main__":
    test_smart_forecasters()
