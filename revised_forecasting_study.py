import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

class ForecastingMethod:
    """Base class for all forecasting methods"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, **kwargs) -> pd.DataFrame:
        """Generate forecast for a weekday - to be implemented by subclasses"""
        raise NotImplementedError

class Method1_SimpleAverage(ForecastingMethod):
    """Method 1: Simple average of last N weeks"""
    
    def __init__(self):
        super().__init__("Simple Average", "Average of last 6 weeks, no adjustments")
    
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
        
        # Get last N weeks
        recent_data = day_data.tail(window)
        
        # Calculate simple average by product
        forecasts = recent_data.groupby('product')['boxes'].mean().round().astype(int).reset_index()
        forecasts = forecasts.rename(columns={'boxes': 'forecast_boxes'})
        
        return forecasts.sort_values('product').reset_index(drop=True)

class Method2_WeightedAverage(ForecastingMethod):
    """Method 2: Weighted average with recency bias"""
    
    def __init__(self):
        super().__init__("Weighted Average", "Exponential weights favoring recent weeks")
    
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
        
        # Get last N weeks
        recent_data = day_data.tail(window)
        
        forecasts = []
        for product in recent_data['product'].unique():
            product_data = recent_data[recent_data['product'] == product]
            
            if len(product_data) == 0:
                continue
            
            # Apply exponential weights (more recent = higher weight)
            weights = np.exp(np.linspace(-1, 0, len(product_data)))
            weights = weights / weights.sum()
            
            forecast = np.average(product_data['boxes'].values, weights=weights)
            forecasts.append({
                'product': product,
                'forecast_boxes': int(round(forecast))
            })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

class Method3_MedianRobust(ForecastingMethod):
    """Method 3: Median-based robust forecasting"""
    
    def __init__(self):
        super().__init__("Median Robust", "Uses median to handle outliers, more conservative")
    
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
        
        # Get last N weeks
        recent_data = day_data.tail(window)
        
        # Calculate median by product (more robust to outliers)
        forecasts = recent_data.groupby('product')['boxes'].median().round().astype(int).reset_index()
        forecasts = forecasts.rename(columns={'boxes': 'forecast_boxes'})
        
        return forecasts.sort_values('product').reset_index(drop=True)

class Method4_TrendAdjusted(ForecastingMethod):
    """Method 4: Trend-adjusted forecasting"""
    
    def __init__(self):
        super().__init__("Trend Adjusted", "Detects trends and adjusts forecasts accordingly")
    
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
        
        # Get last N weeks
        recent_data = day_data.tail(window)
        
        forecasts = []
        for product in recent_data['product'].unique():
            product_data = recent_data[recent_data['product'] == product]
            
            if len(product_data) < 3:  # Need at least 3 points for trend
                # Fall back to simple average
                forecast = product_data['boxes'].mean()
            else:
                # Calculate trend
                x = np.arange(len(product_data))
                y = product_data['boxes'].values
                trend = np.polyfit(x, y, 1)[0]
                
                # Base forecast (weighted average)
                weights = np.exp(np.linspace(-1, 0, len(product_data)))
                weights = weights / weights.sum()
                base_forecast = np.average(y, weights=weights)
                
                # Apply trend adjustment (max 20% change)
                trend_factor = min(1.2, max(0.8, 1 + (trend / base_forecast * 0.2)))
                forecast = base_forecast * trend_factor
            
            forecasts.append({
                'product': product,
                'forecast_boxes': int(round(forecast))
            })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

class Method5_SeasonalBlend(ForecastingMethod):
    """Method 5: Seasonal blending with last year data"""
    
    def __init__(self):
        super().__init__("Seasonal Blend", "Blends recent data with same week last year")
    
    def forecast_weekday(self, history_df: pd.DataFrame, day: str, target_year: int, 
                        target_week: int, window: int = 6, alpha: float = 0.7, **kwargs) -> pd.DataFrame:
        
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
        
        # Get recent data (last N weeks)
        recent_data = day_data.tail(window)
        
        # Get same week last year data
        last_year_data = day_data[
            (day_data['year'] == target_year - 1) & 
            (day_data['week_num'] == target_week)
        ]
        
        forecasts = []
        for product in recent_data['product'].unique():
            # Recent average
            recent_product_data = recent_data[recent_data['product'] == product]
            if len(recent_product_data) == 0:
                continue
            
            # Weighted average of recent data
            weights = np.exp(np.linspace(-1, 0, len(recent_product_data)))
            weights = weights / weights.sum()
            recent_avg = np.average(recent_product_data['boxes'].values, weights=weights)
            
            # Last year data
            last_year_product_data = last_year_data[last_year_data['product'] == product]
            if len(last_year_product_data) > 0:
                last_year_avg = last_year_product_data['boxes'].mean()
                # Blend recent and last year
                forecast = alpha * recent_avg + (1 - alpha) * last_year_avg
            else:
                # No last year data, use recent only
                forecast = recent_avg
            
            forecasts.append({
                'product': product,
                'forecast_boxes': int(round(forecast))
            })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)

class RevisedForecastingStudy:
    """Revised study using weeks with sufficient historical data"""
    
    def __init__(self):
        self.methods = [
            Method1_SimpleAverage(),
            Method2_WeightedAverage(),
            Method3_MedianRobust(),
            Method4_TrendAdjusted(),
            Method5_SeasonalBlend()
        ]
        self.results = []
    
    def run_study(self, test_weeks: List[Dict], history_df: pd.DataFrame):
        """Run the revised study"""
        print("=== REVISED FORECASTING STUDY ===")
        print(f"Testing {len(self.methods)} methods on {len(test_weeks)} weeks with sufficient data")
        
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
            
            week_results = {
                'week_file': week_file,
                'week_num': week_num,
                'year': year,
                'method_results': {}
            }
            
            for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
                print(f"\n--- {day.upper()} ---")
                
                # Get actual data
                actual_data = parse_daily_totals_universal(test_file, day)
                if actual_data.empty:
                    print(f"No actual data for {day}")
                    continue
                
                total_actual = actual_data['boxes'].sum()
                print(f"Actual: {total_actual} boxes ({len(actual_data)} products)")
                
                day_results = {
                    'actual': total_actual,
                    'actual_products': len(actual_data),
                    'method_errors': {}
                }
                
                # Test each method
                for method in self.methods:
                    try:
                        forecast = method.forecast_weekday(history_df, day, year, week_num)
                        total_forecast = forecast['forecast_boxes'].sum()
                        error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
                        
                        day_results['method_errors'][method.name] = {
                            'forecast': total_forecast,
                            'error': error,
                            'products': len(forecast)
                        }
                        
                        print(f"{method.name:<20}: {total_forecast:>4} boxes ({len(forecast):>2} products) - Error: {error:>6.1f}%")
                        
                    except Exception as e:
                        print(f"{method.name:<20}: ERROR - {str(e)}")
                        day_results['method_errors'][method.name] = {
                            'forecast': 0,
                            'error': 100,
                            'products': 0
                        }
                
                week_results['method_results'][day] = day_results
            
            self.results.append(week_results)
        
        return self.results
    
    def analyze_results(self):
        """Analyze and compare results across all methods"""
        print(f"\n{'='*70}")
        print(f"REVISED STUDY RESULTS")
        print(f"{'='*70}")
        
        # Calculate average errors for each method
        method_errors = {method.name: [] for method in self.methods}
        
        for week_result in self.results:
            for day, day_result in week_result['method_results'].items():
                for method_name, method_data in day_result['method_errors'].items():
                    method_errors[method_name].append(method_data['error'])
        
        # Calculate statistics
        method_stats = {}
        for method_name, errors in method_errors.items():
            if errors:
                method_stats[method_name] = {
                    'avg_error': np.mean(errors),
                    'median_error': np.median(errors),
                    'std_error': np.std(errors),
                    'min_error': np.min(errors),
                    'max_error': np.max(errors),
                    'num_tests': len(errors)
                }
        
        # Sort by average error
        sorted_methods = sorted(method_stats.items(), key=lambda x: x[1]['avg_error'])
        
        print(f"\n📊 METHOD RANKINGS (by average error):")
        print(f"{'Rank':<4} {'Method':<20} {'Avg Error':<10} {'Median':<10} {'Std Dev':<10} {'Tests':<6}")
        print(f"{'-'*70}")
        
        for i, (method_name, stats) in enumerate(sorted_methods, 1):
            print(f"{i:<4} {method_name:<20} {stats['avg_error']:<10.1f} {stats['median_error']:<10.1f} {stats['std_error']:<10.1f} {stats['num_tests']:<6}")
        
        # Best method analysis
        best_method = sorted_methods[0]
        print(f"\n🏆 BEST METHOD: {best_method[0]}")
        print(f"   Average Error: {best_method[1]['avg_error']:.1f}%")
        print(f"   Median Error: {best_method[1]['median_error']:.1f}%")
        print(f"   Standard Deviation: {best_method[1]['std_error']:.1f}%")
        
        # Improvement over worst method
        worst_method = sorted_methods[-1]
        improvement = worst_method[1]['avg_error'] - best_method[1]['avg_error']
        improvement_pct = (improvement / worst_method[1]['avg_error']) * 100
        
        print(f"\n📈 IMPROVEMENT:")
        print(f"   Best vs Worst: {improvement:.1f} percentage points ({improvement_pct:.1f}% better)")
        
        return method_stats, sorted_methods

def run_revised_study():
    """Run the revised forecasting study with sufficient historical data"""
    # Load historical data
    history_df = load_all_history(".")
    
    # Use weeks that have sufficient historical data (starting from Week 45, 2024)
    # This gives us at least 6 weeks of historical data for forecasting
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Create and run study
    study = RevisedForecastingStudy()
    results = study.run_study(test_weeks, history_df)
    
    # Analyze results
    method_stats, sorted_methods = study.analyze_results()
    
    return study, results, method_stats, sorted_methods

if __name__ == "__main__":
    run_revised_study()
