# Synthetic Order Patterns Summary

## Overview
Generated 1,254 orders from April 1, 2025 to September 13, 2025 with realistic business patterns for accurate forecasting.

## Key Patterns Implemented

### 📈 Monthly Growth Trend
- **3% monthly growth rate** built into base demand
- Clear progression from April to August:
  - April: 179 orders ($3,794 revenue)
  - May: 204 orders ($4,305 revenue)
  - June: 255 orders ($5,141 revenue) 
  - July: 263 orders ($5,202 revenue)
  - August: 258 orders ($5,089 revenue)
  - September: 95 orders ($1,978 revenue) [partial month]

### 📅 Seasonal Variations
- **Summer Peak Factor**: 1.4x multiplier for June-August
- **Spring/Fall Factor**: 1.2x multiplier for April-May, September
- Clear seasonal trend visible in order volumes

### 📊 Weekly Cycles
Strong weekend preference pattern:
- **Monday**: 128 orders (10.2%)
- **Tuesday**: 106 orders (8.5%)
- **Wednesday**: 125 orders (10.0%)
- **Thursday**: 154 orders (12.3%)
- **Friday**: 202 orders (16.1%)
- **Saturday**: 290 orders (23.1%) ⭐ Peak day
- **Sunday**: 249 orders (19.9%)

**Weekend vs Weekday**:
- Weekday: 715 orders (57.0%)
- Weekend: 539 orders (43.0%)

### 🕐 Daily Patterns
Clear lunch and dinner peaks:
- **10 AM**: 34 orders (2.7%)
- **11 AM-2 PM (Lunch Peak)**: 520 orders (41.5%)
  - 11 AM: 108 orders
  - 12 PM: 138 orders ⭐ Peak hour
  - 1 PM: 144 orders ⭐ Peak hour
  - 2 PM: 130 orders
- **3-5 PM (Afternoon Lull)**: 75 orders (6.0%)
- **6-9 PM (Dinner Peak)**: 585 orders (46.6%)
  - 6 PM: 148 orders
  - 7 PM: 134 orders
  - 8 PM: 154 orders ⭐ Peak hour
  - 9 PM: 149 orders
- **10 PM**: 40 orders (3.2%)

### 🎉 Special Events
Implemented event spikes with realistic multipliers:
- **April 15**: Local festival (2.0x multiplier)
- **May 1**: May Day holiday (1.8x multiplier)
- **May 15**: University graduation (1.6x multiplier)
- **June 1**: Start of summer season (1.7x multiplier)
- **June 21**: Summer solstice celebration (2.2x multiplier)
- **July 4**: Independence Day (2.5x multiplier) ⭐ Biggest spike
- **July 20**: Summer food festival (1.9x multiplier)
- **August 15**: Back to school promotion (1.8x multiplier)
- **September 1**: Labor Day weekend (1.6x multiplier)

### 🌤️ Weather Impact Simulation
- **10%** chance of bad weather (1.4x multiplier - more delivery orders)
- **10%** chance of perfect weather (0.8x multiplier - fewer orders)
- **80%** chance of normal weather (1.0x multiplier)

### 👤 User Behavior Patterns
Each user has distinct ordering patterns:
- **Alice**: Regular office worker, prefers weekday lunch
- **Bob**: Social eater, active on weekends
- **Charlie**: Price-sensitive student, smaller orders
- **Diana**: Health-conscious, moderate ordering
- **Eve**: Busy professional, dinner preference
- **ayeshmadusanka**: Varied pattern across all times

## Forecasting Benefits

These patterns enable realistic forecasting models to:

1. **Predict seasonal demand** - Summer growth, holiday spikes
2. **Plan staffing** - Weekend and peak hour coverage
3. **Inventory management** - Higher demand periods
4. **Marketing campaigns** - Target low-demand periods
5. **Revenue forecasting** - Monthly growth trends
6. **Capacity planning** - Handle event-driven spikes

## Data Quality
- **Realistic order sizes**: 1-3 items per order based on user behavior
- **Varied pricing**: $1.99 - $14.99 range with user price sensitivity
- **Geographic distribution**: 10 different delivery addresses
- **Order status realism**: Recent orders more likely to be pending
- **Time precision**: Realistic timestamps with minute/second variations

This synthetic dataset provides the foundation for accurate time series forecasting, demand prediction, and business intelligence analytics.