#!/usr/bin/env python3
"""Generate JSON data files for the web UI."""

import json
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from calculate_costs import (
    create_default_model, create_performance_model, create_optimized_cpm_model,
    create_minimum_base_model, create_2k_base_model, create_3k_minimum_base_model,
    load_creator_statistics, load_video_data,
    calculate_all_creators, calculate_all_creators_performance, calculate_all_creators_3k_minimum
)

def generate_model_1_data():
    """Generate Model 1 data."""
    creators_data = load_creator_statistics()
    if not creators_data:
        return None
    
    model = create_default_model()
    financials = calculate_all_creators(model, creators_data, follower_counts=None, period_type="signed")
    
    total_base_cost = sum(f.total_base_cost for f in financials)
    total_bonus = sum(f.bonus for f in financials)
    total_cost = sum(f.total_cost for f in financials)
    total_instagram_videos = sum(f.instagram_videos for f in financials)
    total_views = sum(f.total_views for f in financials)
    
    data = {
        'model_name': 'Model 1: Base Rate + Bonuses',
        'total_cost': total_cost,
        'total_base_cost': total_base_cost,
        'total_bonus': total_bonus,
        'total_instagram_videos': total_instagram_videos,
        'total_views': total_views,
        'cost_per_view': total_cost / total_views if total_views > 0 else 0,
        'creators': [
            {
                'creator_name': f.creator_name,
                'instagram_videos': f.instagram_videos,
                'total_views': f.total_views,
                'total_base_cost': f.total_base_cost,
                'bonus': f.bonus,
                'total_cost': f.total_cost
            }
            for f in sorted(financials, key=lambda x: x.total_cost, reverse=True)
        ]
    }
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / 'model1_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_model_2_data():
    """Generate Model 2 data."""
    creator_videos = load_video_data()
    if not creator_videos:
        return None
    
    model = create_performance_model()
    financials = calculate_all_creators_performance(model, creator_videos)
    
    total_cost = sum(f.total_compensation for f in financials)
    total_videos = sum(f.total_videos for f in financials)
    total_qualified = sum(f.qualified_videos for f in financials)
    total_views = sum(f.total_views for f in financials)
    
    data = {
        'model_name': 'Model 2: Performance-Based Per Video',
        'total_cost': total_cost,
        'total_videos': total_videos,
        'total_qualified': total_qualified,
        'total_views': total_views,
        'cost_per_view': total_cost / total_views if total_views > 0 else 0,
        'creators': [
            {
                'creator_name': f.creator_name,
                'total_videos': f.total_videos,
                'qualified_videos': f.qualified_videos,
                'total_views': f.total_views,
                'total_compensation': f.total_compensation
            }
            for f in sorted(financials, key=lambda x: x.total_compensation, reverse=True)
        ]
    }
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / 'model2_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_model_3_data():
    """Generate Model 3 data (Optimized CPM)."""
    creators_data = load_creator_statistics()
    if not creators_data:
        return None
    
    model = create_optimized_cpm_model()
    financials = calculate_all_creators(model, creators_data, follower_counts=None, period_type="signed")
    
    total_base_cost = sum(f.total_base_cost for f in financials)
    total_bonus = sum(f.bonus for f in financials)
    total_cost = sum(f.total_cost for f in financials)
    total_instagram_videos = sum(f.instagram_videos for f in financials)
    total_views = sum(f.total_views for f in financials)
    
    data = {
        'model_name': 'Model 3: Optimized CPM Model',
        'total_cost': total_cost,
        'total_base_cost': total_base_cost,
        'total_bonus': total_bonus,
        'total_instagram_videos': total_instagram_videos,
        'total_views': total_views,
        'cost_per_view': total_cost / total_views if total_views > 0 else 0,
        'creators': [
            {
                'creator_name': f.creator_name,
                'instagram_videos': f.instagram_videos,
                'total_views': f.total_views,
                'total_base_cost': f.total_base_cost,
                'bonus': f.bonus,
                'total_cost': f.total_cost
            }
            for f in sorted(financials, key=lambda x: x.total_cost, reverse=True)
        ]
    }
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / 'model3_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_model_5_data():
    """Generate Model 5 data ($20 Base with 2K Minimum)."""
    creator_videos = load_video_data()
    if not creator_videos:
        return None
    
    model = create_2k_base_model()
    financials = calculate_all_creators_performance(model, creator_videos)
    
    total_cost = sum(f.total_compensation for f in financials)
    total_videos = sum(f.total_videos for f in financials)
    total_qualified = sum(f.qualified_videos for f in financials)
    total_views = sum(f.total_views for f in financials)
    
    data = {
        'model_name': 'Model 5: $20 Base with 2K Minimum',
        'total_cost': total_cost,
        'total_videos': total_videos,
        'total_qualified': total_qualified,
        'total_views': total_views,
        'cost_per_view': total_cost / total_views if total_views > 0 else 0,
        'creators': [
            {
                'creator_name': f.creator_name,
                'total_videos': f.total_videos,
                'qualified_videos': f.qualified_videos,
                'total_views': f.total_views,
                'total_compensation': f.total_compensation
            }
            for f in sorted(financials, key=lambda x: x.total_compensation, reverse=True)
        ]
    }
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / 'model5_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_model_4_data():
    """Generate Model 4 data (Lower Threshold Performance)."""
    creator_videos = load_video_data()
    if not creator_videos:
        return None
    
    model = create_minimum_base_model()
    financials = calculate_all_creators_performance(model, creator_videos)
    
    total_cost = sum(f.total_compensation for f in financials)
    total_videos = sum(f.total_videos for f in financials)
    total_qualified = sum(f.qualified_videos for f in financials)
    total_views = sum(f.total_views for f in financials)
    
    data = {
        'model_name': 'Model 4: Lower Threshold Performance Model',
        'total_cost': total_cost,
        'total_videos': total_videos,
        'total_qualified': total_qualified,
        'total_views': total_views,
        'cost_per_view': total_cost / total_views if total_views > 0 else 0,
        'creators': [
            {
                'creator_name': f.creator_name,
                'total_videos': f.total_videos,
                'qualified_videos': f.qualified_videos,
                'total_views': f.total_views,
                'total_compensation': f.total_compensation
            }
            for f in sorted(financials, key=lambda x: x.total_compensation, reverse=True)
        ]
    }
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / 'model4_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_model_6_data():
    """Generate Model 6 data (Current Model with 3K Minimum)."""
    creator_videos = load_video_data()
    if not creator_videos:
        return None
    
    model = create_3k_minimum_base_model()
    financials = calculate_all_creators_3k_minimum(model, creator_videos)
    
    total_base_cost = sum(f.total_base_cost for f in financials)
    total_bonus = sum(f.bonus for f in financials)
    total_cost = sum(f.total_cost for f in financials)
    total_instagram_videos = sum(f.instagram_videos for f in financials)
    total_views = sum(f.total_views for f in financials)
    
    data = {
        'model_name': 'Model 6: Current Model with 3K Minimum',
        'total_cost': total_cost,
        'total_base_cost': total_base_cost,
        'total_bonus': total_bonus,
        'total_instagram_videos': total_instagram_videos,
        'total_views': total_views,
        'cost_per_view': total_cost / total_views if total_views > 0 else 0,
        'creators': [
            {
                'creator_name': f.creator_name,
                'instagram_videos': f.instagram_videos,
                'total_views': f.total_views,
                'total_base_cost': f.total_base_cost,
                'bonus': f.bonus,
                'total_cost': f.total_cost
            }
            for f in sorted(financials, key=lambda x: x.total_cost, reverse=True)
        ]
    }
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / 'model6_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == '__main__':
    print("Generating data files...")
    generate_model_1_data()
    generate_model_2_data()
    generate_model_3_data()
    generate_model_4_data()
    generate_model_5_data()
    generate_model_6_data()
    print("Done! Data files generated: model1_data.json, model2_data.json, model3_data.json, model4_data.json, model5_data.json, model6_data.json")

