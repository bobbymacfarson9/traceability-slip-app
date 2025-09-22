import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ImprovedForecaster:
    """Enhanced forecasting system with holiday detection, product-specific models, and better accuracy"""
    
    def __init__(self, history_df: pd.DataFrame):
        self.history_df = history_df.copy()
        self.holiday_weeks = self._detect_holiday_weeks()
        self.product_patterns = self._analyze_product_patterns()
        self.day_patterns = self._analyze_day_patterns()
        
    def _detect_holiday_weeks(self) -> set:
        """Detect weeks with unusually low demand (likely holidays)"""
        weekly_totals = self.history_df.groupby(['year', 'week_num'])['boxes'].sum().reset_index()
        
        if len(weekly_totals) < 4:
            return set()
        
        # Calculate IQR for outlier detection
        Q1 = weekly_totals['boxes'].quantile(0.25)
        Q3 = weekly_totals['boxes'].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define holiday weeks as those with very low demand
        holiday_threshold = Q1 - 1.5 * IQR
        
        holiday_weeks = set()
        for _, row in weekly_totals.iterrows():
            if row['boxes'] < holiday_threshold:
                holiday_weeks.add((row['year'], row['week_num']))
        
        print(f"Detected {len(holiday_weeks)} holiday weeks: {holiday_weeks}")
        return holiday_weeks
    
    def _analyze_product_patterns(self) -> Dict:
        """Analyze demand patterns for each product"""
        patterns = {}
        
        for product in self.history_df['product'].unique():
            product_data = self.history_df[self.history_df['product'] == product].copy()
            
            if len(product_data) < 3:
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
        """Analyze day-of-week demand patterns"""
        day_patterns = {}
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            day_data = self.history_df[self.history_df['day'] == day].copy()
            
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
    
    def _is_holiday_week(self, year: int, week_num: int) -> bool:
        """Check if a week is likely a holiday week"""
        return (year, week_num) in self.holiday_weeks
    
    def _get_product_forecast(self, product: str, day: str, target_year: int, target_week: int, 
                            window: int = 8) -> float:
        """Get forecast for a specific product using improved methods"""
        
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
        
        # Get product pattern info
        pattern = self.product_patterns.get(product, {})
        demand_frequency = pattern.get('demand_frequency', 1.0)
        is_infrequent = pattern.get('is_infrequent', False)
        is_low_demand = pattern.get('is_low_demand', False)
        
        # Check if target week is a holiday
        is_holiday = self._is_holiday_week(target_year, target_week)
        
        # For holiday weeks, use very conservative forecasting
        if is_holiday:
            # For holiday weeks, only forecast products that are very consistent
            if demand_frequency < 0.8:  # Less than 80% of weeks have demand
                return 0.0
            
            # Use only the most recent data and be very conservative
            recent_data = product_data.tail(3)
            if len(recent_data) == 0:
                return 0.0
            
            # Use minimum of recent demand
            return max(0, recent_data['boxes'].min() * 0.5)
        
        # For normal weeks, use improved forecasting
        if is_infrequent:
            # For infrequent products, use longer window but be conservative
            window = min(window * 2, len(product_data))
            recent_data = product_data.tail(window)
            
            # Use median instead of mean for infrequent products
            forecast = recent_data['boxes'].median()
            
            # Apply conservative factor for infrequent products
            return max(0, forecast * 0.7)
        
        elif is_low_demand:
            # For low demand products, use simple average with conservative factor
            recent_data = product_data.tail(window)
            forecast = recent_data['boxes'].mean()
            return max(0, forecast * 0.8)
        
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
                
                # Apply small trend adjustment (max 10% change)
                trend_factor = min(1.1, max(0.9, 1 + (trend / forecast * 0.1)))
                forecast *= trend_factor
            
            return max(0, forecast)
    
    def forecast_weekday(self, day: str, target_year: int, target_week: int, 
                        window: int = 8) -> pd.DataFrame:
        """Generate improved forecast for a weekday"""
        
        # Get all products that have appeared on this day
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
        """Get summary of forecasting improvements"""
        return {
            'holiday_weeks_detected': len(self.holiday_weeks),
            'products_analyzed': len(self.product_patterns),
            'volatile_products': len([p for p in self.product_patterns.values() if p.get('is_volatile', False)]),
            'infrequent_products': len([p for p in self.product_patterns.values() if p.get('is_infrequent', False)]),
            'low_demand_products': len([p for p in self.product_patterns.values() if p.get('is_low_demand', False)]),
            'day_patterns': self.day_patterns
        }

def test_improved_forecaster():
    """Test the improved forecaster"""
    print("=== TESTING IMPROVED FORECASTER ===")
    
    # Load historical data
    from egg_packing_predictor_universal import load_all_history
    history_df = load_all_history(".")
    
    # Create improved forecaster
    forecaster = ImprovedForecaster(history_df)
    
    # Get summary
    summary = forecaster.get_forecast_summary()
    print(f"Forecasting Summary:")
    print(f"  Holiday weeks detected: {summary['holiday_weeks_detected']}")
    print(f"  Products analyzed: {summary['products_analyzed']}")
    print(f"  Volatile products: {summary['volatile_products']}")
    print(f"  Infrequent products: {summary['infrequent_products']}")
    print(f"  Low demand products: {summary['low_demand_products']}")
    
    # Test on Week 24 (normal week)
    print(f"\n--- Testing Week 24, 2025 (Normal Week) ---")
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        forecast = forecaster.forecast_weekday(day, 2025, 24)
        total_forecast = forecast['forecast_boxes'].sum()
        print(f"{day}: {len(forecast)} products, {total_forecast} total boxes")
    
    # Test on Week 32 (holiday week)
    print(f"\n--- Testing Week 32, 2025 (Holiday Week) ---")
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        forecast = forecaster.forecast_weekday(day, 2025, 32)
        total_forecast = forecast['forecast_boxes'].sum()
        print(f"{day}: {len(forecast)} products, {total_forecast} total boxes")
    
    return forecaster

if __name__ == "__main__":
    test_improved_forecaster()