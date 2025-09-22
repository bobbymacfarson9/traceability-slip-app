import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class BalancedForecaster:
    """Balanced forecasting system that handles outliers without being too conservative on holidays"""
    
    def __init__(self, history_df: pd.DataFrame):
        self.history_df = history_df.copy()
        self.legitimate_holidays = self._identify_legitimate_holidays()
        self.outlier_days = self._detect_outlier_days()
        self.product_patterns = self._analyze_product_patterns()
        self.day_patterns = self._analyze_day_patterns()
        
        print(f"📅 Legitimate holidays detected: {len(self.legitimate_holidays)}")
        print(f"🚫 Outlier days detected: {len(self.outlier_days)}")
        
    def _identify_legitimate_holidays(self) -> set:
        """Identify legitimate holidays (Christmas, Easter, etc.) based on known patterns"""
        # These are known holiday weeks where we expect reduced but not zero demand
        legitimate_holidays = set()
        
        # Christmas week (typically week 52 or 1)
        legitimate_holidays.add((2024, 52))  # Christmas 2024
        legitimate_holidays.add((2025, 1))   # New Year 2025
        legitimate_holidays.add((2025, 52))  # Christmas 2025
        
        # Easter (varies by year, but typically weeks 12-16)
        # Easter 2025 is around week 15
        legitimate_holidays.add((2025, 15))  # Easter 2025
        
        # Other major holidays
        legitimate_holidays.add((2025, 7))   # Family Day (February)
        legitimate_holidays.add((2025, 22))  # Victoria Day (May)
        legitimate_holidays.add((2025, 30))  # Canada Day (July)
        legitimate_holidays.add((2025, 35))  # Labour Day (September)
        legitimate_holidays.add((2025, 42))  # Thanksgiving (October)
        legitimate_holidays.add((2025, 44))  # Remembrance Day (November)
        
        return legitimate_holidays
    
    def _detect_outlier_days(self) -> set:
        """Detect days with suspiciously low demand that are likely data entry errors"""
        outlier_days = set()
        
        # Group by week and day to analyze daily totals
        daily_totals = self.history_df.groupby(['year', 'week_num', 'day'])['boxes'].sum().reset_index()
        
        # Calculate statistics for each day of the week
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            day_data = daily_totals[daily_totals['day'] == day]['boxes']
            
            if len(day_data) < 5:  # Need at least 5 data points
                continue
            
            # Calculate robust statistics (using median and IQR)
            median_demand = day_data.median()
            Q1 = day_data.quantile(0.25)
            Q3 = day_data.quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier threshold (very low demand)
            # Use a more conservative threshold for outlier detection
            outlier_threshold = max(1, Q1 - 2.5 * IQR)  # More conservative than 1.5*IQR
            
            # Find outlier days
            for _, row in daily_totals[daily_totals['day'] == day].iterrows():
                if row['boxes'] <= outlier_threshold:
                    # Check if it's not a legitimate holiday
                    if (row['year'], row['week_num']) not in self.legitimate_holidays:
                        outlier_days.add((row['year'], row['week_num'], row['day']))
        
        return outlier_days
    
    def _analyze_product_patterns(self) -> Dict:
        """Analyze demand patterns for each product, excluding outliers"""
        patterns = {}
        
        for product in self.history_df['product'].unique():
            product_data = self.history_df[self.history_df['product'] == product].copy()
            
            if len(product_data) < 3:
                continue
            
            # Remove outlier days from analysis
            product_data = product_data[~product_data.apply(
                lambda row: (row['year'], row['week_num'], row['day']) in self.outlier_days, axis=1
            )]
            
            if len(product_data) < 2:
                continue
            
            # Calculate demand statistics
            total_demand = product_data['boxes'].sum()
            avg_demand = product_data['boxes'].mean()
            demand_std = product_data['boxes'].std()
            zero_demand_weeks = len(product_data[product_data['boxes'] == 0])
            total_weeks = len(product_data)
            
            # Calculate demand frequency (how often product has demand > 0)
            demand_frequency = (total_weeks - zero_demand_weeks) / total_weeks
            
            # Calculate coefficient of variation (volatility)
            cv = demand_std / avg_demand if avg_demand > 0 else 0
            
            patterns[product] = {
                'avg_demand': avg_demand,
                'demand_std': demand_std,
                'demand_frequency': demand_frequency,
                'cv': cv,
                'zero_demand_weeks': zero_demand_weeks,
                'total_weeks': total_weeks,
                'is_volatile': cv > 1.0,  # High volatility
                'is_infrequent': demand_frequency < 0.5,  # Less than 50% of weeks
                'is_low_demand': avg_demand < 5  # Low average demand
            }
        
        return patterns
    
    def _analyze_day_patterns(self) -> Dict:
        """Analyze day-of-week demand patterns, excluding outliers"""
        day_patterns = {}
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            day_data = self.history_df[self.history_df['day'] == day].copy()
            
            if len(day_data) == 0:
                continue
            
            # Remove outlier days from analysis
            day_data = day_data[~day_data.apply(
                lambda row: (row['year'], row['week_num'], row['day']) in self.outlier_days, axis=1
            )]
            
            if len(day_data) == 0:
                continue
            
            # Calculate day-specific statistics
            total_demand = day_data['boxes'].sum()
            avg_demand = day_data['boxes'].mean()
            demand_std = day_data['boxes'].std()
            
            # Calculate weekly totals for this day
            weekly_totals = day_data.groupby(['year', 'week_num'])['boxes'].sum().reset_index()
            
            day_patterns[day] = {
                'avg_demand': avg_demand,
                'demand_std': demand_std,
                'total_demand': total_demand,
                'weekly_avg': weekly_totals['boxes'].mean(),
                'weekly_std': weekly_totals['boxes'].std(),
                'is_high_demand_day': avg_demand > self.history_df['boxes'].mean(),
                'is_volatile_day': (demand_std / avg_demand) > 1.0 if avg_demand > 0 else False
            }
        
        return day_patterns
    
    def _is_legitimate_holiday(self, year: int, week_num: int) -> bool:
        """Check if a week is a legitimate holiday"""
        return (year, week_num) in self.legitimate_holidays
    
    def _is_outlier_day(self, year: int, week_num: int, day: str) -> bool:
        """Check if a specific day is an outlier (data entry error)"""
        return (year, week_num, day) in self.outlier_days
    
    def _get_product_forecast(self, product: str, day: str, target_year: int, target_week: int, 
                            window: int = 8) -> float:
        """Get forecast for a specific product using balanced methods"""
        
        # Get historical data for this product and day
        product_data = self.history_df[
            (self.history_df['product'] == product) & 
            (self.history_df['day'] == day)
        ].copy()
        
        if len(product_data) < 2:
            return 0.0
        
        # Sort by date
        product_data = product_data.sort_values(['year', 'week_num'])
        
        # Filter out data after target week
        product_data = product_data[
            (product_data['year'] < target_year) | 
            ((product_data['year'] == target_year) & (product_data['week_num'] < target_week))
        ]
        
        if len(product_data) == 0:
            return 0.0
        
        # Remove outlier days from training data
        product_data = product_data[~product_data.apply(
            lambda row: (row['year'], row['week_num'], row['day']) in self.outlier_days, axis=1
        )]
        
        if len(product_data) == 0:
            return 0.0
        
        # Get product pattern info
        pattern = self.product_patterns.get(product, {})
        demand_frequency = pattern.get('demand_frequency', 1.0)
        is_infrequent = pattern.get('is_infrequent', False)
        is_low_demand = pattern.get('is_low_demand', False)
        
        # Check if target week is a legitimate holiday
        is_holiday = self._is_legitimate_holiday(target_year, target_week)
        
        # Check if target day is an outlier
        is_outlier = self._is_outlier_day(target_year, target_week, day)
        
        # For outlier days, return 0 (don't forecast for data entry errors)
        if is_outlier:
            return 0.0
        
        # For legitimate holidays, use moderate reduction (not too aggressive)
        if is_holiday:
            # For holiday weeks, use recent data with moderate reduction
            recent_data = product_data.tail(min(window, len(product_data)))
            
            if len(recent_data) == 0:
                return 0.0
            
            # Use weighted average with moderate holiday reduction
            weights = np.exp(np.linspace(-1, 0, len(recent_data)))
            weights = weights / weights.sum()
            
            forecast = np.average(recent_data['boxes'].values, weights=weights)
            
            # Apply moderate holiday reduction (20-30% instead of 60%)
            holiday_factor = 0.75  # 25% reduction instead of 60%
            return max(0, forecast * holiday_factor)
        
        # For normal weeks, use improved forecasting
        if is_infrequent:
            # For infrequent products, use longer window but be conservative
            window = min(window * 2, len(product_data))
            recent_data = product_data.tail(window)
            
            # Use median instead of mean for infrequent products
            forecast = recent_data['boxes'].median()
            
            # Apply conservative factor for infrequent products
            return max(0, forecast * 0.8)
        
        elif is_low_demand:
            # For low demand products, use simple average with conservative factor
            recent_data = product_data.tail(window)
            forecast = recent_data['boxes'].mean()
            return max(0, forecast * 0.9)
        
        else:
            # For normal products, use weighted average with recency bias
            recent_data = product_data.tail(window)
            
            if len(recent_data) == 0:
                return 0.0
            
            # Apply exponential weights (more recent = higher weight)
            weights = np.exp(np.linspace(-1, 0, len(recent_data)))
            weights = weights / weights.sum()
            
            forecast = np.average(recent_data['boxes'].values, weights=weights)
            
            # Apply trend adjustment if we have enough data
            if len(recent_data) >= 4:
                # Calculate simple trend
                x = np.arange(len(recent_data))
                y = recent_data['boxes'].values
                trend = np.polyfit(x, y, 1)[0]
                
                # Apply small trend adjustment (max 5% change instead of 10%)
                trend_factor = min(1.05, max(0.95, 1 + (trend / forecast * 0.05)))
                forecast *= trend_factor
            
            return max(0, forecast)
    
    def forecast_weekday(self, day: str, target_year: int, target_week: int, 
                        window: int = 8) -> pd.DataFrame:
        """Generate balanced forecast for a weekday"""
        
        # Check if this is an outlier day
        if self._is_outlier_day(target_year, target_week, day):
            print(f"⚠️  {day} Week {target_week}, {target_year} detected as outlier day - returning empty forecast")
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        # Get all products that have appeared on this day (excluding outliers)
        day_products = self.history_df[
            (self.history_df['day'] == day) & 
            (self.history_df['boxes'] > 0)
        ]['product'].unique()
        
        forecasts = []
        
        for product in day_products:
            forecast_boxes = self._get_product_forecast(product, day, target_year, target_week, window)
            
            if forecast_boxes > 0:
                forecasts.append({
                    'product': product,
                    'forecast_boxes': int(round(forecast_boxes))
                })
        
        if not forecasts:
            return pd.DataFrame(columns=['product', 'forecast_boxes'])
        
        result = pd.DataFrame(forecasts)
        return result.sort_values('product').reset_index(drop=True)
    
    def get_forecast_summary(self) -> Dict:
        """Get summary of balanced forecasting"""
        return {
            'legitimate_holidays': len(self.legitimate_holidays),
            'outlier_days_detected': len(self.outlier_days),
            'products_analyzed': len(self.product_patterns),
            'volatile_products': len([p for p in self.product_patterns.values() if p.get('is_volatile', False)]),
            'infrequent_products': len([p for p in self.product_patterns.values() if p.get('is_infrequent', False)]),
            'low_demand_products': len([p for p in self.product_patterns.values() if p.get('is_low_demand', False)]),
            'day_patterns': self.day_patterns,
            'outlier_days_list': list(self.outlier_days)
        }

def test_balanced_forecaster():
    """Test the balanced forecaster"""
    print("=== TESTING BALANCED FORECASTER ===")
    
    # Load historical data
    from egg_packing_predictor_universal import load_all_history
    history_df = load_all_history(".")
    
    # Create balanced forecaster
    forecaster = BalancedForecaster(history_df)
    
    # Get summary
    summary = forecaster.get_forecast_summary()
    print(f"\nBalanced Forecasting Summary:")
    print(f"  Legitimate holidays: {summary['legitimate_holidays']}")
    print(f"  Outlier days detected: {summary['outlier_days_detected']}")
    print(f"  Products analyzed: {summary['products_analyzed']}")
    print(f"  Volatile products: {summary['volatile_products']}")
    print(f"  Infrequent products: {summary['infrequent_products']}")
    print(f"  Low demand products: {summary['low_demand_products']}")
    
    # Test on Week 22 (holiday week that was problematic)
    print(f"\n--- Testing Week 22, 2025 (Holiday Week) ---")
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        forecast = forecaster.forecast_weekday(day, 2025, 22)
        total_forecast = forecast['forecast_boxes'].sum()
        print(f"{day}: {len(forecast)} products, {total_forecast} total boxes")
    
    # Test on Week 24 (normal week)
    print(f"\n--- Testing Week 24, 2025 (Normal Week) ---")
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        forecast = forecaster.forecast_weekday(day, 2025, 24)
        total_forecast = forecast['forecast_boxes'].sum()
        print(f"{day}: {len(forecast)} products, {total_forecast} total boxes")
    
    return forecaster

if __name__ == "__main__":
    test_balanced_forecaster()
