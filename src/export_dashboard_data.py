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
    create_optimized_model, create_3k_base_with_performance_bonuses,
    load_creator_statistics, load_video_data,
    calculate_all_creators, calculate_all_creators_performance, calculate_all_creators_3k_minimum,
    calculate_all_creators_optimized, calculate_all_creators_hybrid
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
    # Use December data for consistency
    from calculate_costs import parse_december_data_for_model1
    
    december_data = parse_december_data_for_model1()
    if not december_data:
        return None
    
    # Convert December data to creator_statistics format
    creators_data = []
    for creator_name, dec_data in december_data.items():
        creators_data.append({
            'creator_name': creator_name,
            'instagram_videos': dec_data['paid_videos'],
            'total_videos': dec_data['paid_videos'],
            'total_views': dec_data['total_views'],
            'avg_views': dec_data['total_views'] / dec_data['paid_videos'] if dec_data['paid_videos'] > 0 else 0
        })
    
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


def generate_model_7_data():
    """Generate Model 7 data (Optimized Balanced Model)."""
    creator_videos = load_video_data()
    if not creator_videos:
        return None

    model = create_optimized_model()
    financials = calculate_all_creators_optimized(model, creator_videos)

    total_base_cost = sum(f.total_base_cost for f in financials)
    total_bonus = sum(f.bonus for f in financials)
    total_cost = sum(f.total_cost for f in financials)
    total_instagram_videos = sum(f.instagram_videos for f in financials)
    total_views = sum(f.total_views for f in financials)

    data = {
        'model_name': 'Model 7: Optimized Balanced Model',
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
    with open(data_dir / 'model7_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    return data


def generate_model_8_data():
    """Generate Model 8 data (3K Base with Per-Video Performance Bonuses)."""
    creator_videos = load_video_data()
    if not creator_videos:
        return None

    model = create_3k_base_with_performance_bonuses()
    financials = calculate_all_creators_hybrid(model, creator_videos)

    total_base_cost = sum(f.total_base_cost for f in financials)
    total_bonus = sum(f.bonus for f in financials)
    total_cost = sum(f.total_cost for f in financials)
    total_instagram_videos = sum(f.instagram_videos for f in financials)
    total_views = sum(f.total_views for f in financials)

    data = {
        'model_name': 'Model 8: 3K Base with Performance Bonuses',
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
    with open(data_dir / 'model8_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    return data

def generate_new_model_a_data():
    """Generate Model A data ($30 Base + Individual Video Bonus) from simulation."""
    data_dir = Path(__file__).parent.parent / 'data'
    sim_file = data_dir / 'new_bonus_models_simulation.json'
    
    if not sim_file.exists():
        print("Warning: new_bonus_models_simulation.json not found. Running simulation...")
        from simulate_new_bonus_models import main as run_simulation
        run_simulation()
    
    with open(sim_file, 'r') as f:
        sim_data = json.load(f)
    
    dec_data = sim_data['december_2025']['individual_bonus']
    
    # Convert to dashboard format
    data = {
        'model_name': dec_data['model_name'],
        'total_cost': dec_data['total_cost'],
        'total_bonus': dec_data['total_bonus'],
        'total_base_cost': dec_data.get('total_base_cost', 0.0),
        'total_videos': dec_data['total_videos'],
        'total_views': dec_data['total_views'],
        'cost_per_view': dec_data['cost_per_view'],
        'creators': [
            {
                'creator_name': c['creator_name'],
                'total_videos': c['total_videos'],
                'qualified_videos': c.get('qualified_videos', 0),
                'total_views': c['total_views'],
                'total_base_cost': c.get('total_base_cost', 0.0),
                'total_bonus': c['total_bonus'],
                'total_cost': c['total_cost']
            }
            for c in sorted(dec_data['creators'], key=lambda x: x['total_cost'], reverse=True)
        ]
    }
    
    with open(data_dir / 'new_model_a_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_new_model_b_data():
    """Generate Model B data ($30 Base + Summed Video Bonus) from simulation."""
    data_dir = Path(__file__).parent.parent / 'data'
    sim_file = data_dir / 'new_bonus_models_simulation.json'
    
    if not sim_file.exists():
        print("Warning: new_bonus_models_simulation.json not found. Running simulation...")
        from simulate_new_bonus_models import main as run_simulation
        run_simulation()
    
    with open(sim_file, 'r') as f:
        sim_data = json.load(f)
    
    dec_data = sim_data['december_2025']['summed_bonus']
    
    # Convert to dashboard format
    data = {
        'model_name': dec_data['model_name'],
        'total_cost': dec_data['total_cost'],
        'total_bonus': dec_data['total_bonus'],
        'total_base_cost': dec_data.get('total_base_cost', 0.0),
        'total_videos': dec_data['total_videos'],
        'total_views': dec_data['total_views'],
        'cost_per_view': dec_data['cost_per_view'],
        'creators': [
            {
                'creator_name': c['creator_name'],
                'total_videos': c['total_videos'],
                'qualified_videos': c.get('qualified_videos', 0),
                'total_views': c['total_views'],
                'total_base_cost': c.get('total_base_cost', 0.0),
                'total_bonus': c['total_bonus'],
                'total_cost': c['total_cost']
            }
            for c in sorted(dec_data['creators'], key=lambda x: x['total_cost'], reverse=True)
        ]
    }
    
    with open(data_dir / 'new_model_b_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_new_model_c_data():
    """Generate Model C data ($30 Base + Individual Video Bonus - January 2026 Projection) from simulation."""
    data_dir = Path(__file__).parent.parent / 'data'
    sim_file = data_dir / 'new_bonus_models_simulation.json'
    
    if not sim_file.exists():
        print("Warning: new_bonus_models_simulation.json not found. Running simulation...")
        from simulate_new_bonus_models import main as run_simulation
        run_simulation()
    
    with open(sim_file, 'r') as f:
        sim_data = json.load(f)
    
    jan_data = sim_data['january_2026']['individual_bonus']
    
    # Convert to dashboard format
    data = {
        'model_name': 'Model C: $30 Base + Individual Video Bonus (Jan 2026 Projection)',
        'total_cost': jan_data['total_cost'],
        'total_bonus': jan_data['total_bonus'],
        'total_base_cost': jan_data.get('total_base_cost', 0.0),
        'total_videos': jan_data['total_videos'],
        'total_views': jan_data['total_views'],
        'cost_per_view': jan_data['cost_per_view'],
        'creators': [
            {
                'creator_name': c['creator_name'],
                'total_videos': c['total_videos'],
                'qualified_videos': c.get('qualified_videos', 0),
                'total_views': c['total_views'],
                'total_base_cost': c.get('total_base_cost', 0.0),
                'total_bonus': c['total_bonus'],
                'total_cost': c['total_cost']
            }
            for c in sorted(jan_data['creators'], key=lambda x: x['total_cost'], reverse=True)
        ]
    }
    
    with open(data_dir / 'new_model_c_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_new_model_d_data():
    """Generate Model D data ($30 Base + Summed Video Bonus - January 2026 Projection) from simulation."""
    data_dir = Path(__file__).parent.parent / 'data'
    sim_file = data_dir / 'new_bonus_models_simulation.json'
    
    if not sim_file.exists():
        print("Warning: new_bonus_models_simulation.json not found. Running simulation...")
        from simulate_new_bonus_models import main as run_simulation
        run_simulation()
    
    with open(sim_file, 'r') as f:
        sim_data = json.load(f)
    
    jan_data = sim_data['january_2026']['summed_bonus']
    
    # Convert to dashboard format
    data = {
        'model_name': 'Model D: $30 Base + Summed Video Bonus (Jan 2026 Projection)',
        'total_cost': jan_data['total_cost'],
        'total_bonus': jan_data['total_bonus'],
        'total_base_cost': jan_data.get('total_base_cost', 0.0),
        'total_videos': jan_data['total_videos'],
        'total_views': jan_data['total_views'],
        'cost_per_view': jan_data['cost_per_view'],
        'creators': [
            {
                'creator_name': c['creator_name'],
                'total_videos': c['total_videos'],
                'qualified_videos': c.get('qualified_videos', 0),
                'total_views': c['total_views'],
                'total_base_cost': c.get('total_base_cost', 0.0),
                'total_bonus': c['total_bonus'],
                'total_cost': c['total_cost']
            }
            for c in sorted(jan_data['creators'], key=lambda x: x['total_cost'], reverse=True)
        ]
    }
    
    with open(data_dir / 'new_model_d_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def calculate_bonus_for_views(views: int) -> float:
    """Calculate bonus for a given view count using new tier structure."""
    if views < 10000:
        return 0.0
    elif views >= 5000000:
        return 2970.0
    elif views >= 2000000:
        return 2270.0
    elif views >= 500000:
        return 1270.0
    elif views >= 100000:
        return 470.0
    elif views >= 50000:
        return 170.0
    elif views >= 10000:
        return 45.0
    return 0.0

def generate_new_model_e_data():
    """Generate Model E data (Individual Video Bonus - January 2026 Actual Data).
    
    Model: $30 base per video (3k minimum views) + individual video bonuses.
    """
    from process_january_data import process_january_data
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / 'data'
    january_dir = Path(__file__).parent.parent / 'januaryinfo'
    csv_files = list(january_dir.glob('videos_*.csv'))
    
    if not csv_files:
        print("Warning: No January CSV file found. Model E will be empty.")
        data = {
            'model_name': 'Model E: $30 Base + Individual Video Bonus (Jan 2026 Actual)',
            'total_cost': 0.0,
            'total_bonus': 0.0,
            'total_base_cost': 0.0,
            'total_videos': 0,
            'total_views': 0,
            'cost_per_view': 0.0,
            'creators': []
        }
        with open(data_dir / 'new_model_e_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        return data
    
    # Use the most recent CSV file
    csv_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    creator_videos = process_january_data(csv_file)
    
    BASE_RATE = 30.0
    MIN_VIEWS_FOR_BASE = 3000
    
    # Calculate base + individual video bonuses
    total_cost = 0.0
    total_bonus = 0.0
    total_base_cost = 0.0
    total_videos = 0
    total_views = 0
    creators_data = []
    
    for creator_name, videos in creator_videos.items():
        creator_base_cost = 0.0
        creator_bonus = 0.0
        creator_total_views = 0
        qualified_videos = 0
        
        for video in videos:
            views = video.get('views', 0)
            creator_total_views += views
            
            # Base payment: $30 per video with 3k+ views
            if views >= MIN_VIEWS_FOR_BASE:
                creator_base_cost += BASE_RATE
                qualified_videos += 1
            
            # Calculate bonus for this individual video
            video_bonus = calculate_bonus_for_views(views)
            creator_bonus += video_bonus
        
        creator_total_cost = creator_base_cost + creator_bonus
        
        creators_data.append({
            'creator_name': creator_name,
            'total_videos': len(videos),
            'qualified_videos': qualified_videos,
            'total_views': creator_total_views,
            'total_base_cost': creator_base_cost,
            'total_bonus': creator_bonus,
            'total_cost': creator_total_cost
        })
        
        total_cost += creator_total_cost
        total_bonus += creator_bonus
        total_base_cost += creator_base_cost
        total_videos += len(videos)
        total_views += creator_total_views
    
    cost_per_view = total_cost / total_views if total_views > 0 else 0.0
    
    data = {
        'model_name': 'Model E: $30 Base + Individual Video Bonus (Jan 2026 Actual)',
        'total_cost': total_cost,
        'total_bonus': total_bonus,
        'total_base_cost': total_base_cost,
        'total_videos': total_videos,
        'total_views': total_views,
        'cost_per_view': cost_per_view,
        'creators': sorted(creators_data, key=lambda x: x['total_cost'], reverse=True)
    }
    
    with open(data_dir / 'new_model_e_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def generate_new_model_f_data():
    """Generate Model F data (Summed Video Bonus - January 2026 Actual Data).
    
    Model: $30 base per video (3k minimum views) + summed video bonus.
    """
    from process_january_data import process_january_data
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / 'data'
    january_dir = Path(__file__).parent.parent / 'januaryinfo'
    csv_files = list(january_dir.glob('videos_*.csv'))
    
    if not csv_files:
        print("Warning: No January CSV file found. Model F will be empty.")
        data = {
            'model_name': 'Model F: $30 Base + Summed Video Bonus (Jan 2026 Actual)',
            'total_cost': 0.0,
            'total_bonus': 0.0,
            'total_base_cost': 0.0,
            'total_videos': 0,
            'total_views': 0,
            'cost_per_view': 0.0,
            'creators': []
        }
        with open(data_dir / 'new_model_f_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        return data
    
    # Use the most recent CSV file
    csv_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    creator_videos = process_january_data(csv_file)
    
    BASE_RATE = 30.0
    MIN_VIEWS_FOR_BASE = 3000
    
    # Calculate base + summed video bonuses
    total_cost = 0.0
    total_bonus = 0.0
    total_base_cost = 0.0
    total_videos = 0
    total_views = 0
    creators_data = []
    
    for creator_name, videos in creator_videos.items():
        creator_total_views = sum(video.get('views', 0) for video in videos)
        
        # Base payment: $30 per video with 3k+ views (all videos that meet threshold)
        creator_base_cost = 0.0
        qualified_videos = 0
        for video in videos:
            views = video.get('views', 0)
            if views >= MIN_VIEWS_FOR_BASE:
                creator_base_cost += BASE_RATE
                qualified_videos += 1
        
        # Calculate bonus based on summed views
        creator_bonus = calculate_bonus_for_views(creator_total_views)
        
        creator_total_cost = creator_base_cost + creator_bonus
        
        creators_data.append({
            'creator_name': creator_name,
            'total_videos': len(videos),
            'qualified_videos': qualified_videos,
            'total_views': creator_total_views,
            'total_base_cost': creator_base_cost,
            'total_bonus': creator_bonus,
            'total_cost': creator_total_cost
        })
        
        total_cost += creator_total_cost
        total_bonus += creator_bonus
        total_base_cost += creator_base_cost
        total_videos += len(videos)
        total_views += creator_total_views
    
    cost_per_view = total_cost / total_views if total_views > 0 else 0.0
    
    data = {
        'model_name': 'Model F: $30 Base + Summed Video Bonus (Jan 2026 Actual)',
        'total_cost': total_cost,
        'total_bonus': total_bonus,
        'total_base_cost': total_base_cost,
        'total_videos': total_videos,
        'total_views': total_views,
        'cost_per_view': cost_per_view,
        'creators': sorted(creators_data, key=lambda x: x['total_cost'], reverse=True)
    }
    
    with open(data_dir / 'new_model_f_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == '__main__':
    print("Generating data files...")
    print("Generating new models (A, B, C, D, E, F)...")
    generate_new_model_a_data()
    generate_new_model_b_data()
    generate_new_model_c_data()
    generate_new_model_d_data()
    generate_new_model_e_data()
    generate_new_model_f_data()
    print("Generating old models (1-8)...")
    generate_model_1_data()
    generate_model_2_data()
    generate_model_3_data()
    generate_model_4_data()
    generate_model_5_data()
    generate_model_6_data()
    generate_model_7_data()
    generate_model_8_data()
    print("Done! Data files generated:")
    print("  New models: new_model_a_data.json through new_model_f_data.json")
    print("  Old models: model1_data.json through model8_data.json")

