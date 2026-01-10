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


def project_january_2026_data(december_data: Dict[str, List[Dict]], january_target_percentage: float = 0.012) -> Dict[str, List[Dict]]:
    """
    Project January 2026 data based on December 2025 data.
    
    Assumptions:
    - Same number of videos per creator
    - December: ~0.8% of videos are >100k views
    - January: ~1.2% of videos should be >100k views (target)
    - Videos that cross the 100k threshold get boosted (3x-10x multiplier)
    - Other videos maintain similar view counts (with small variation)
    
    Args:
        december_data: December 2025 video data
        january_target_percentage: Target percentage of videos >100k in January (default 1.2%)
    """
    import random
    random.seed(42)  # For reproducibility
    
    # Count total videos and videos >100k in December
    # Store videos with their index for accurate matching
    all_videos = []
    high_view_videos = []  # Videos already >100k: (creator_name, video_index, views)
    candidate_videos = []   # Videos that can be boosted to cross 100k threshold
    
    for creator_name, videos in december_data.items():
        for video_idx, video in enumerate(videos):
            views = video.get('views', 0)
            all_videos.append((creator_name, video_idx, views))
            if views >= 100000:
                high_view_videos.append((creator_name, video_idx, views))
            elif views >= 20000:  # Candidates: videos with 20k+ views can be boosted to cross 100k
                candidate_videos.append((creator_name, video_idx, views))
    
    total_videos = len(all_videos)
    december_high_count = len(high_view_videos)
    december_percentage = december_high_count / total_videos if total_videos > 0 else 0
    
    # Calculate target: 1.2% of total videos should be >100k in January
    target_high_count = max(1, int(total_videos * january_target_percentage))
    additional_needed = max(0, target_high_count - december_high_count)
    
    print(f"December: {december_high_count}/{total_videos} videos >100k ({december_percentage*100:.2f}%)")
    print(f"January target: {target_high_count}/{total_videos} videos >100k ({january_target_percentage*100:.2f}%)")
    print(f"Need to boost {additional_needed} additional videos to cross 100k threshold")
    
    # Select videos to boost:
    # 1. All existing >100k videos get boosted (3x-10x)
    # 2. Additional videos from candidate pool get boosted to cross 100k
    videos_to_boost = list(high_view_videos)  # Start with existing >100k
    
    if additional_needed > 0 and len(candidate_videos) > 0:
        # Select additional videos from candidate pool (prioritize higher-view videos)
        # Sort by views descending to prioritize videos closer to 100k
        candidate_videos_sorted = sorted(candidate_videos, key=lambda x: x[2], reverse=True)
        num_to_select = min(additional_needed, len(candidate_videos_sorted))
        # Select from top candidates (higher views = more likely to cross threshold)
        selected_candidates = candidate_videos_sorted[:num_to_select]
        videos_to_boost.extend(selected_candidates)
    
    # Create a set of (creator_name, video_index) tuples for quick lookup
    boost_set = set((name, idx) for name, idx, _ in videos_to_boost)
    
    # Project January data
    january_data = {}
    for creator_name, videos in december_data.items():
        january_videos = []
        
        for video_idx, video in enumerate(videos):
            views = video.get('views', 0)
            
            # Check if this video should be boosted using (creator_name, video_index)
            should_boost = (creator_name, video_idx) in boost_set
            
            if should_boost:
                if views >= 100000:
                    # Already >100k: apply 3x-10x multiplier
                    multiplier = random.uniform(3.0, 10.0)
                    new_views = int(views * multiplier)
                else:
                    # Candidate video: boost to cross 100k threshold
                    # For videos 20k-99k, apply multiplier to ensure they cross 100k
                    # Lower view videos need higher multipliers
                    if views >= 50000:
                        multiplier = random.uniform(2.0, 5.0)  # 2x-5x for 50k-99k
                    elif views >= 30000:
                        multiplier = random.uniform(3.5, 6.0)  # 3.5x-6x for 30k-49k
                    else:
                        multiplier = random.uniform(5.0, 8.0)  # 5x-8x for 20k-29k
                    new_views = max(100001, int(views * multiplier))  # Ensure >100k
                is_viral = True
            else:
                # Regular video: small variation (±20%)
                variation = random.uniform(0.8, 1.2)
                new_views = int(views * variation)
                is_viral = False
            
            january_videos.append({
                'views': new_views,
                'platform': video.get('platform', 'instagram'),
                'publishedDate': video.get('publishedDate', '2026-01-01'),
                'is_viral': is_viral
            })
        
        january_data[creator_name] = january_videos
    
    # Verify January percentage
    january_high_count = sum(
        1 for videos in january_data.values()
        for video in videos
        if video.get('views', 0) >= 100000
    )
    january_percentage = january_high_count / total_videos if total_videos > 0 else 0
    print(f"January result: {january_high_count}/{total_videos} videos >100k ({january_percentage*100:.2f}%)")
    
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
    print("   - Assumes same number of videos per creator as December")
    print("   - Viral video assumption: 1.2% of videos >100k views become viral")
    print("   - Viral videos: 3x-10x view multiplier (randomly distributed)")
    print("   - Regular videos: ±20% view variation")
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
    january_data = project_january_2026_data(december_data, january_target_percentage=0.012)
    
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

