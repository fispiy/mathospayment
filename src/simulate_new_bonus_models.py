#!/usr/bin/env python3
"""
Simulate new bonus models with individual video bonus vs summed video bonus.

New Bonus Structure:
- 10,000 – 49,999 views: $45
- 50,000 – 99,999 views: $170
- 100,000 – 499,999 views: $470
- 500,000 – 1,999,999 views: $1,270
- 2,000,000 – 4,999,999 views: $2,270
- 5,000,000+ views: $2,970 (capped)

This script simulates:
1. December 2025: Based on actual data
2. January 2026: Projected with 1.2% of videos >100k views being viral
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import csv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from calculate_costs import load_video_data_from_december


@dataclass
class BonusTier:
    """Represents a bonus tier based on views."""
    min_views: int
    max_views: Optional[int]  # None means no upper limit
    bonus: float
    name: str = ""


# New bonus structure
NEW_BONUS_TIERS = [
    BonusTier(min_views=5000000, max_views=None, bonus=2970.0, name="5M+ views (capped)"),
    BonusTier(min_views=2000000, max_views=4999999, bonus=2270.0, name="2M-4.99M views"),
    BonusTier(min_views=500000, max_views=1999999, bonus=1270.0, name="500K-1.99M views"),
    BonusTier(min_views=100000, max_views=499999, bonus=470.0, name="100K-499K views"),
    BonusTier(min_views=50000, max_views=99999, bonus=170.0, name="50K-99K views"),
    BonusTier(min_views=10000, max_views=49999, bonus=45.0, name="10K-49K views"),
]


def calculate_bonus_for_views(views: int) -> float:
    """Calculate bonus for a given view count using new tier structure."""
    if views < 10000:
        return 0.0
    
    # Find the highest applicable tier
    for tier in sorted(NEW_BONUS_TIERS, key=lambda t: t.min_views, reverse=True):
        if views >= tier.min_views:
            if tier.max_views is None or views <= tier.max_views:
                return tier.bonus
    
    return 0.0


def load_december_video_data() -> Dict[str, List[Dict]]:
    """Load December 2025 video data."""
    try:
        data = load_video_data_from_december()
        if data:
            return data
    except (FileNotFoundError, Exception) as e:
        print(f"Warning: Could not load December CSV ({type(e).__name__}). Using model data as fallback.")
    
    # Fallback: use model1 data structure to infer video counts
    model1_path = Path(__file__).parent.parent / "data" / "model1_data.json"
    if model1_path.exists():
        with open(model1_path, 'r') as f:
            model1_data = json.load(f)
            
            # Create synthetic video data based on model1 stats
            # Use a power-law distribution to simulate realistic video view patterns
            import random
            import math
            random.seed(42)  # For reproducibility
            
            creator_videos = {}
            for creator in model1_data['creators']:
                creator_name = creator['creator_name']
                total_views = creator['total_views']
                video_count = creator['instagram_videos']
                
                if video_count == 0:
                    continue
                
                # Create a realistic distribution: few high-performing videos, many low-performing
                # Use Pareto distribution (80/20 rule approximation)
                videos = []
                remaining_views = total_views
                
                # Sort videos by expected performance (some will be viral, most will be average)
                for i in range(video_count):
                    # First 20% of videos get 80% of views (Pareto principle)
                    if i < max(1, int(video_count * 0.2)):
                        # High-performing videos
                        if i == 0 and video_count > 5:
                            # Top video gets significant share
                            views = int(remaining_views * random.uniform(0.15, 0.35))
                        else:
                            views = int(remaining_views * random.uniform(0.05, 0.15))
                    else:
                        # Regular videos - distributed evenly among remaining views
                        remaining_video_count = video_count - i
                        avg_remaining = remaining_views / remaining_video_count if remaining_video_count > 0 else 0
                        views = int(avg_remaining * random.uniform(0.5, 1.5))
                    
                    views = max(0, min(views, remaining_views))  # Ensure non-negative and don't exceed total
                    remaining_views -= views
                    
                    videos.append({
                        'views': views,
                        'platform': 'instagram',
                        'publishedDate': f'2025-12-{(i % 28) + 1:02d}',
                    })
                
                # Distribute any remaining views to the top video
                if remaining_views > 0 and videos:
                    videos[0]['views'] += remaining_views
                
                # Ensure total matches (account for rounding)
                actual_total = sum(v['views'] for v in videos)
                if actual_total != total_views:
                    diff = total_views - actual_total
                    if videos:
                        videos[0]['views'] += diff
                
                creator_videos[creator_name] = videos
            
            print(f"Created synthetic data for {len(creator_videos)} creators based on model1_data.json")
            total_vids = sum(len(v) for v in creator_videos.values())
            total_views = sum(sum(v['views'] for v in videos) for videos in creator_videos.values())
            print(f"  Total videos: {total_vids}, Total views: {total_views:,}")
            return creator_videos
    else:
        print(f"ERROR: model1_data.json not found at {model1_path}")
    
    return {}


def calculate_individual_video_bonus_model(creator_videos: Dict[str, List[Dict]]) -> Dict:
    """
    Model A: $30 Base + Individual Video Bonus
    $30 base per video with 3k+ views, plus individual video bonuses.
    """
    BASE_RATE = 30.0
    MIN_VIEWS_FOR_BASE = 3000
    
    results = {
        'model_name': 'Model A: $30 Base + Individual Video Bonus',
        'total_cost': 0.0,
        'total_bonus': 0.0,
        'total_base_cost': 0.0,
        'total_videos': 0,
        'total_views': 0,
        'creators': []
    }
    
    for creator_name, videos in creator_videos.items():
        creator_base_cost = 0.0
        creator_bonus = 0.0
        creator_total_views = 0
        qualified_videos = 0
        video_details = []
        
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
            
            if video_bonus > 0:
                video_details.append({
                    'views': views,
                    'bonus': video_bonus
                })
        
        creator_total_cost = creator_base_cost + creator_bonus
        
        results['creators'].append({
            'creator_name': creator_name,
            'total_videos': len(videos),
            'qualified_videos': qualified_videos,
            'total_views': creator_total_views,
            'total_base_cost': creator_base_cost,
            'total_bonus': creator_bonus,
            'total_cost': creator_total_cost,
            'video_details': video_details[:10]  # Show top 10 for reference
        })
        
        results['total_cost'] += creator_total_cost
        results['total_bonus'] += creator_bonus
        results['total_base_cost'] += creator_base_cost
        results['total_videos'] += len(videos)
        results['total_views'] += creator_total_views
    
    results['cost_per_view'] = results['total_cost'] / results['total_views'] if results['total_views'] > 0 else 0
    
    return results


def calculate_summed_video_bonus_model(creator_videos: Dict[str, List[Dict]]) -> Dict:
    """
    Model B: $30 Base + Summed Video Bonus
    $30 base per video with 3k+ views, plus summed video bonus.
    """
    BASE_RATE = 30.0
    MIN_VIEWS_FOR_BASE = 3000
    
    results = {
        'model_name': 'Model B: $30 Base + Summed Video Bonus',
        'total_cost': 0.0,
        'total_bonus': 0.0,
        'total_base_cost': 0.0,
        'total_videos': 0,
        'total_views': 0,
        'creators': []
    }
    
    for creator_name, videos in creator_videos.items():
        creator_total_views = sum(video.get('views', 0) for video in videos)
        
        # Base payment: $30 per video with 3k+ views (all videos meeting threshold)
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
        
        results['creators'].append({
            'creator_name': creator_name,
            'total_videos': len(videos),
            'qualified_videos': qualified_videos,
            'total_views': creator_total_views,
            'total_base_cost': creator_base_cost,
            'total_bonus': creator_bonus,
            'total_cost': creator_total_cost,
        })
        
        results['total_cost'] += creator_total_cost
        results['total_bonus'] += creator_bonus
        results['total_base_cost'] += creator_base_cost
        results['total_videos'] += len(videos)
        results['total_views'] += creator_total_views
    
    results['cost_per_view'] = results['total_cost'] / results['total_views'] if results['total_views'] > 0 else 0
    
    return results


def project_january_2026_data(december_data: Dict[str, List[Dict]], january_target_percentage: float = 0.012, target_total_videos: int = 1600) -> Dict[str, List[Dict]]:
    """
    Project January 2026 data based on December 2025 data.
    
    Generates 1600 videos total using statistical sampling from December patterns.
    
    Assumptions:
    - January: 1600 total videos (scaled from December)
    - December: ~0.8% of videos are >100k views
    - January: ~1.2% of videos should be >100k views (target = 19 videos)
    - Uses December's view distribution patterns for realistic sampling
    - Videos are distributed across creators proportionally to December
    
    Args:
        december_data: December 2025 video data
        january_target_percentage: Target percentage of videos >100k in January (default 1.2%)
        target_total_videos: Target total number of videos for January (default 1600)
    """
    import random
    random.seed(42)  # For reproducibility
    
    # Extract all December videos and their view counts
    december_videos = []
    december_creators = []
    for creator_name, videos in december_data.items():
        for video in videos:
            views = video.get('views', 0)
            december_videos.append({
                'views': views,
                'platform': video.get('platform', 'instagram'),
                'creator': creator_name
            })
            december_creators.append(creator_name)
    
    december_total = len(december_videos)
    december_high_count = sum(1 for v in december_videos if v['views'] >= 100000)
    december_percentage = december_high_count / december_total if december_total > 0 else 0
    
    # Calculate target: 1.2% of 1600 videos = 19.2, round to 19
    target_high_count = max(1, int(target_total_videos * january_target_percentage))
    
    print(f"December: {december_high_count}/{december_total} videos >100k ({december_percentage*100:.2f}%)")
    print(f"January target: {target_high_count}/{target_total_videos} videos >100k ({january_target_percentage*100:.2f}%)")
    print(f"Scaling from {december_total} to {target_total_videos} videos ({target_total_videos/december_total:.2f}x)")
    
    # Extract view distribution patterns from December
    december_views = [v['views'] for v in december_videos]
    
    # Group December videos by view ranges for realistic sampling
    view_ranges = {
        'viral': [v for v in december_views if v >= 100000],
        'high': [v for v in december_views if 50000 <= v < 100000],
        'medium': [v for v in december_views if 10000 <= v < 50000],
        'low': [v for v in december_views if 3000 <= v < 10000],
        'very_low': [v for v in december_views if v < 3000],
    }
    
    # Calculate how many videos in each range for January
    scale_factor = target_total_videos / december_total
    range_counts = {
        'viral': target_high_count,  # Target viral count
        'high': max(1, int(len(view_ranges['high']) * scale_factor)),
        'medium': max(1, int(len(view_ranges['medium']) * scale_factor)),
        'low': max(1, int(len(view_ranges['low']) * scale_factor)),
        'very_low': max(1, int(len(view_ranges['very_low']) * scale_factor)),
    }
    
    # Adjust to ensure total = target_total_videos
    current_total = sum(range_counts.values())
    if current_total != target_total_videos:
        diff = target_total_videos - current_total
        # Adjust the largest non-viral category
        if diff > 0:
            range_counts['very_low'] += diff
        else:
            range_counts['very_low'] = max(0, range_counts['very_low'] + diff)
    
    print(f"\nView range distribution:")
    print(f"  Viral (>100k): {range_counts['viral']} videos")
    print(f"  High (50k-99k): {range_counts['high']} videos")
    print(f"  Medium (10k-49k): {range_counts['medium']} videos")
    print(f"  Low (3k-9k): {range_counts['low']} videos")
    print(f"  Very Low (<3k): {range_counts['very_low']} videos")
    
    # Generate January videos by sampling from December patterns
    january_videos_list = []
    
    # Generate viral videos (>100k)
    if range_counts['viral'] > 0:
        if len(view_ranges['viral']) > 0:
            # Sample from existing viral videos and apply multipliers
            for _ in range(range_counts['viral']):
                base_views = random.choice(view_ranges['viral'])
                multiplier = random.uniform(3.0, 10.0)
                new_views = int(base_views * multiplier)
                january_videos_list.append({
                    'views': new_views,
                    'is_viral': True,
                    'range': 'viral'
                })
        else:
            # No viral videos in December, create new ones from high performers
            high_candidates = view_ranges['high'] if view_ranges['high'] else view_ranges['medium']
            if not high_candidates:
                high_candidates = [50000]  # Fallback
            for _ in range(range_counts['viral']):
                base_views = random.choice(high_candidates)
                multiplier = random.uniform(2.0, 8.0)
                new_views = max(100001, int(base_views * multiplier))
                january_videos_list.append({
                    'views': new_views,
                    'is_viral': True,
                    'range': 'viral'
                })
    
    # Generate high videos (50k-99k)
    for _ in range(range_counts['high']):
        if view_ranges['high']:
            base_views = random.choice(view_ranges['high'])
            variation = random.uniform(0.8, 1.3)
            new_views = max(50000, min(99999, int(base_views * variation)))
        else:
            # Sample from medium and scale up
            base_views = random.choice(view_ranges['medium']) if view_ranges['medium'] else 25000
            multiplier = random.uniform(2.0, 3.5)
            new_views = max(50000, min(99999, int(base_views * multiplier)))
        january_videos_list.append({
            'views': new_views,
            'is_viral': False,
            'range': 'high'
        })
    
    # Generate medium videos (10k-49k)
    for _ in range(range_counts['medium']):
        if view_ranges['medium']:
            base_views = random.choice(view_ranges['medium'])
            variation = random.uniform(0.7, 1.3)
            new_views = max(10000, min(49999, int(base_views * variation)))
        else:
            # Sample from low and scale up
            base_views = random.choice(view_ranges['low']) if view_ranges['low'] else 5000
            multiplier = random.uniform(2.0, 8.0)
            new_views = max(10000, min(49999, int(base_views * multiplier)))
        january_videos_list.append({
            'views': new_views,
            'is_viral': False,
            'range': 'medium'
        })
    
    # Generate low videos (3k-9k)
    for _ in range(range_counts['low']):
        if view_ranges['low']:
            base_views = random.choice(view_ranges['low'])
            variation = random.uniform(0.7, 1.4)
            new_views = max(3000, min(9999, int(base_views * variation)))
        else:
            # Sample from very low and scale up
            base_views = random.choice(view_ranges['very_low']) if view_ranges['very_low'] else 1000
            multiplier = random.uniform(3.0, 9.0)
            new_views = max(3000, min(9999, int(base_views * multiplier)))
        january_videos_list.append({
            'views': new_views,
            'is_viral': False,
            'range': 'low'
        })
    
    # Generate very low videos (<3k)
    for _ in range(range_counts['very_low']):
        if view_ranges['very_low']:
            base_views = random.choice(view_ranges['very_low'])
            variation = random.uniform(0.5, 2.0)
            new_views = max(0, min(2999, int(base_views * variation)))
        else:
            # Generate from distribution
            import math
            new_views = int(random.lognormvariate(math.log(100), 1.0))  # Log-normal for realistic small views
            new_views = max(0, min(2999, new_views))
        january_videos_list.append({
            'views': new_views,
            'is_viral': False,
            'range': 'very_low'
        })
    
    # Shuffle to randomize order
    random.shuffle(january_videos_list)
    
    # Distribute videos across creators proportionally to December
    creator_video_counts = {}
    for creator_name in december_data.keys():
        creator_video_counts[creator_name] = len(december_data[creator_name])
    
    total_december_videos = sum(creator_video_counts.values())
    if total_december_videos == 0:
        total_december_videos = 1
    
    # Calculate target video counts per creator for January
    january_creator_counts = {}
    remaining_videos = target_total_videos
    creators_list = list(creator_video_counts.keys())
    
    # Distribute proportionally
    for creator_name in creators_list[:-1]:  # All but last
        proportion = creator_video_counts[creator_name] / total_december_videos
        count = max(1, int(target_total_videos * proportion))
        january_creator_counts[creator_name] = count
        remaining_videos -= count
    
    # Last creator gets remaining videos
    if creators_list:
        january_creator_counts[creators_list[-1]] = max(1, remaining_videos)
    
    # Assign videos to creators
    january_data = {}
    video_idx = 0
    for creator_name, target_count in january_creator_counts.items():
        creator_videos = []
        for i in range(target_count):
            if video_idx < len(january_videos_list):
                video_data = january_videos_list[video_idx]
                # Get platform from December data if available
                platform = 'instagram'
                if creator_name in december_data and december_data[creator_name]:
                    platform = december_data[creator_name][0].get('platform', 'instagram')
                
                creator_videos.append({
                    'views': video_data['views'],
                    'platform': platform,
                    'publishedDate': f'2026-01-{(i % 31) + 1:02d}',
                    'is_viral': video_data['is_viral']
                })
                video_idx += 1
        january_data[creator_name] = creator_videos
    
    # Verify January results
    january_total = sum(len(videos) for videos in january_data.values())
    january_high_count = sum(
        1 for videos in january_data.values()
        for video in videos
        if video.get('views', 0) >= 100000
    )
    january_percentage = january_high_count / january_total if january_total > 0 else 0
    
    print(f"\nJanuary result: {january_high_count}/{january_total} videos >100k ({january_percentage*100:.2f}%)")
    print(f"Total January videos: {january_total}")
    
    return january_data


def print_model_summary(model_data: Dict, month: str):
    """Print a formatted summary of model results."""
    print(f"\n{'='*80}")
    print(f"{model_data['model_name']} - {month}")
    print(f"{'='*80}")
    print(f"Total Cost: ${model_data['total_cost']:,.2f}")
    print(f"Total Bonus: ${model_data['total_bonus']:,.2f}")
    print(f"Total Videos: {model_data['total_videos']:,}")
    print(f"Total Views: {model_data['total_views']:,}")
    print(f"Cost per View: ${model_data['cost_per_view']:.6f}")
    print(f"\nTop 10 Creators by Cost:")
    print(f"{'Creator':<25} {'Videos':<10} {'Views':<15} {'Bonus':<15} {'Total Cost':<15}")
    print("-" * 80)
    
    sorted_creators = sorted(
        model_data['creators'],
        key=lambda x: x['total_cost'],
        reverse=True
    )[:10]
    
    for creator in sorted_creators:
        print(f"{creator['creator_name']:<25} "
              f"{creator['total_videos']:<10} "
              f"{creator['total_views']:<15,} "
              f"${creator['total_bonus']:<14,.2f} "
              f"${creator['total_cost']:<14,.2f}")


def print_assumptions():
    """Print key assumptions and inputs for the simulation."""
    print("\n" + "="*80)
    print("KEY ASSUMPTIONS AND INPUTS")
    print("="*80)
    print("\n1. BONUS STRUCTURE:")
    for tier in sorted(NEW_BONUS_TIERS, key=lambda t: t.min_views, reverse=True):
        if tier.max_views:
            print(f"   - {tier.min_views:,} – {tier.max_views:,} views: ${tier.bonus:,.2f}")
        else:
            print(f"   - {tier.min_views:,}+ views: ${tier.bonus:,.2f} (capped)")
    
    print("\n2. MODEL VARIANTS:")
    print("   - Model A (Individual Video Bonus): Each video gets bonus based on its own views")
    print("   - Model B (Summed Video Bonus): Total bonus based on sum of all creator's video views")
    
    print("\n3. DECEMBER 2025 DATA:")
    print("   - Source: December Data - Sheet1.csv (or model1_data.json as fallback)")
    print("   - Uses actual video counts and view data from December")
    
    print("\n4. JANUARY 2026 PROJECTION:")
    print("   - Target: 1600 total videos (scaled from December using statistical sampling)")
    print("   - Videos distributed across creators proportionally to December")
    print("   - Uses December's view distribution patterns for realistic sampling")
    print("   - Viral video assumption: 1.2% of videos (>100k views) = 19 viral videos")
    print("   - Viral videos: 3x-10x view multiplier (randomly distributed)")
    print("   - Regular videos: sampled from December patterns with realistic variation")
    print("   - Random seed: 42 (for reproducibility)")
    
    print("\n5. CALCULATION METHOD:")
    print("   - Base: $30 per video with 3,000+ views (all videos meeting threshold)")
    print("   - Videos with <10,000 views: $0 bonus")
    print("   - Videos/creators qualify for highest applicable tier")
    print("   - Individual model: Sum of bonuses for each video")
    print("   - Summed model: Single bonus based on total views")


def main():
    """Main function to run the simulation."""
    print("="*80)
    print("NEW BONUS MODEL SIMULATION")
    print("="*80)
    
    # Print assumptions first
    print_assumptions()
    
    # Load December 2025 data
    print("\n" + "="*80)
    print("Loading December 2025 data...")
    print("="*80)
    december_data = load_december_video_data()
    
    if not december_data:
        print("ERROR: Could not load December data!")
        return
    
    print(f"Loaded data for {len(december_data)} creators")
    total_videos = sum(len(videos) for videos in december_data.values())
    print(f"Total videos: {total_videos}")
    
    # Calculate December models
    print("\n" + "="*80)
    print("DECEMBER 2025 SIMULATION")
    print("="*80)
    
    dec_model_a = calculate_individual_video_bonus_model(december_data)
    dec_model_b = calculate_summed_video_bonus_model(december_data)
    
    print_model_summary(dec_model_a, "December 2025")
    print_model_summary(dec_model_b, "December 2025")
    
    # Project January 2026 data
    print("\n" + "="*80)
    print("Projecting January 2026 data...")
    print("="*80)
    january_data = project_january_2026_data(december_data, january_target_percentage=0.012, target_total_videos=1600)
    
    # Count viral videos
    total_viral = sum(
        sum(1 for v in videos if v.get('is_viral', False))
        for videos in january_data.values()
    )
    print(f"Projected {total_viral} viral videos in January 2026")
    
    # Calculate January models
    print("\n" + "="*80)
    print("JANUARY 2026 SIMULATION")
    print("="*80)
    
    jan_model_a = calculate_individual_video_bonus_model(january_data)
    jan_model_b = calculate_summed_video_bonus_model(january_data)
    
    print_model_summary(jan_model_a, "January 2026")
    print_model_summary(jan_model_b, "January 2026")
    
    # Save results to JSON
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    results = {
        'assumptions': {
            'bonus_tiers': [asdict(tier) for tier in NEW_BONUS_TIERS],
            'viral_percentage': 0.012,
            'viral_multiplier_range': [3.0, 10.0],
            'regular_video_variation': 0.2
        },
        'december_2025': {
            'individual_bonus': dec_model_a,
            'summed_bonus': dec_model_b
        },
        'january_2026': {
            'individual_bonus': jan_model_a,
            'summed_bonus': jan_model_b
        }
    }
    
    output_file = output_dir / "new_bonus_models_simulation.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
    
    # Print comparison summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"\nDecember 2025:")
    print(f"  Model A (Individual): ${dec_model_a['total_cost']:,.2f}")
    print(f"  Model B (Summed):     ${dec_model_b['total_cost']:,.2f}")
    print(f"  Difference:           ${abs(dec_model_a['total_cost'] - dec_model_b['total_cost']):,.2f}")
    
    print(f"\nJanuary 2026:")
    print(f"  Model A (Individual): ${jan_model_a['total_cost']:,.2f}")
    print(f"  Model B (Summed):     ${jan_model_b['total_cost']:,.2f}")
    print(f"  Difference:           ${abs(jan_model_a['total_cost'] - jan_model_b['total_cost']):,.2f}")
    
    print(f"\nMonth-over-Month Change:")
    print(f"  Model A: ${jan_model_a['total_cost'] - dec_model_a['total_cost']:+,.2f} "
          f"({((jan_model_a['total_cost'] / dec_model_a['total_cost'] - 1) * 100):+.1f}%)")
    print(f"  Model B: ${jan_model_b['total_cost'] - dec_model_b['total_cost']:+,.2f} "
          f"({((jan_model_b['total_cost'] / dec_model_b['total_cost'] - 1) * 100):+.1f}%)")


if __name__ == "__main__":
    main()

