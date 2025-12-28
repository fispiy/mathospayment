#!/usr/bin/env python3
"""
Financial modeling program for creator pricing.
Calculates costs based on base rates, posting limits, and view-based bonuses.
"""

import csv
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class PricingTier:
    """Represents a bonus tier based on views."""
    min_views: int
    bonus: float
    name: str = ""


@dataclass
class FinancialModel:
    """Represents a financial model configuration."""
    name: str
    base_rate_under_10k: float  # Base rate for accounts under 10k followers
    base_rate_over_10k: float   # Base rate for accounts over 10k followers
    trial_max_videos_per_day: int
    signed_max_videos_per_day: int
    bonus_tiers: List[PricingTier]
    follower_threshold: int = 10000
    
    def calculate_base_rate(self, follower_count: int) -> float:
        """Calculate base rate based on follower count."""
        if follower_count < self.follower_threshold:
            return self.base_rate_under_10k
        else:
            return self.base_rate_over_10k
    
    def calculate_bonus(self, total_views: int) -> float:
        """Calculate bonus based on total views (14-day sum)."""
        applicable_tiers = [tier for tier in self.bonus_tiers if total_views >= tier.min_views]
        if not applicable_tiers:
            return 0.0
        highest_tier = max(applicable_tiers, key=lambda t: t.min_views)
        return highest_tier.bonus


@dataclass
class PerformanceBasedModel:
    """Performance-based model: compensation per video based on top platform views."""
    name: str
    min_views_qualification: int  # Minimum views to qualify (10,000)
    per_video_tiers: List[PricingTier]  # Compensation tiers per video
    
    def calculate_video_compensation(self, views: int) -> float:
        """Calculate compensation for a single video based on views."""
        if views < self.min_views_qualification:
            return 0.0
        
        applicable_tiers = [tier for tier in self.per_video_tiers if views >= tier.min_views]
        if not applicable_tiers:
            return 0.0
        
        # Return the highest applicable tier
        highest_tier = max(applicable_tiers, key=lambda t: t.min_views)
        return highest_tier.bonus


@dataclass
class CreatorFinancials:
    """Financial calculations for a single creator."""
    creator_name: str
    total_videos: int  # Total unique videos across all platforms (for display)
    instagram_videos: int  # Instagram videos only (for base rate)
    total_views: int
    avg_views: float
    follower_count: int
    period_type: str
    
    # Calculated fields
    base_rate_per_video: float = 0.0
    total_base_cost: float = 0.0
    bonus: float = 0.0
    total_cost: float = 0.0
    cost_per_view: float = 0.0
    cost_per_video: float = 0.0


def create_default_model() -> FinancialModel:
    """Create the default financial model as specified."""
    bonus_tiers = [
        PricingTier(min_views=5000000, bonus=3000.0, name="5M+ views"),
        PricingTier(min_views=3000000, bonus=2000.0, name="3M+ views"),
        PricingTier(min_views=1000000, bonus=1200.0, name="1M+ views"),
        PricingTier(min_views=500000, bonus=500.0, name="500K+ views"),
        PricingTier(min_views=250000, bonus=200.0, name="250K+ views"),
        PricingTier(min_views=50000, bonus=150.0, name="50K+ views"),
        PricingTier(min_views=20000, bonus=35.0, name="20K+ views"),
    ]
    
    return FinancialModel(
        name="Default Model",
        base_rate_under_10k=30.0,
        base_rate_over_10k=40.0,
        trial_max_videos_per_day=3,
        signed_max_videos_per_day=5,
        bonus_tiers=bonus_tiers,
        follower_threshold=10000
    )


def create_performance_model() -> PerformanceBasedModel:
    """Create the performance-based model (Model 2)."""
    per_video_tiers = [
        PricingTier(min_views=10000000, bonus=3000.0, name="10M+ views"),
        PricingTier(min_views=5000000, bonus=2000.0, name="5M+ views"),
        PricingTier(min_views=3000000, bonus=1500.0, name="3M+ views"),
        PricingTier(min_views=1000000, bonus=1000.0, name="1M+ views"),
        PricingTier(min_views=500000, bonus=700.0, name="500K+ views"),
        PricingTier(min_views=250000, bonus=350.0, name="250K+ views"),
        PricingTier(min_views=100000, bonus=225.0, name="100K+ views"),
        PricingTier(min_views=50000, bonus=150.0, name="50K+ views"),
        PricingTier(min_views=10000, bonus=100.0, name="10K+ views"),
    ]
    
    return PerformanceBasedModel(
        name="Performance-Based Model",
        min_views_qualification=10000,
        per_video_tiers=per_video_tiers
    )


def create_optimized_cpm_model() -> FinancialModel:
    """
    Create Model 3: Optimized CPM-based model.
    Based on UGC industry standards: $20 base rate + 1 CPM ($1 per 1,000 views) bonuses.
    This model balances cost efficiency with creator satisfaction.
    """
    # 1 CPM = $1 per 1,000 views = $0.001 per view
    # For bonuses, we'll use a simplified CPM structure
    # Instead of complex tiers, we calculate: total_views / 1000 * $1
    # But we'll cap it at reasonable levels to control costs
    
    # Simplified bonus tiers based on 1 CPM calculation
    # Example: 100K views = $100, 500K views = $500, 1M views = $1,000
    # Note: Actual calculation uses direct CPM formula: (views / 1000) * $1
    # Cap: Maximum bonus capped at $1,200 (applies at 1M+ views)
    # These tiers are for reference/documentation only - actual calculation is done directly
    bonus_tiers = [
        PricingTier(min_views=1000000, bonus=1200.0, name="1M+ views (capped at $1,200)"),
        PricingTier(min_views=500000, bonus=500.0, name="500K+ views"),
        PricingTier(min_views=250000, bonus=250.0, name="250K+ views"),
        PricingTier(min_views=100000, bonus=100.0, name="100K+ views"),
        PricingTier(min_views=50000, bonus=50.0, name="50K+ views"),
        PricingTier(min_views=20000, bonus=20.0, name="20K+ views"),
    ]
    
    return FinancialModel(
        name="Optimized CPM Model",
        base_rate_under_10k=20.0,  # $20 base rate for all creators
        base_rate_over_10k=20.0,   # Same rate regardless of followers
        trial_max_videos_per_day=3,
        signed_max_videos_per_day=5,
        bonus_tiers=bonus_tiers,
        follower_threshold=10000
    )


def create_minimum_base_model() -> PerformanceBasedModel:
    """
    Create Model 4: Lower Threshold Performance Model.
    $50 base fee per video with 5,000 views minimum (half of Model 2's 10K threshold).
    Same tier structure as Model 2 but with lower threshold.
    """
    # Per video compensation tiers - $50 at 5K (half of Model 2's $100 at 10K)
    # Then same structure as Model 2
    per_video_tiers = [
        PricingTier(min_views=10000000, bonus=3000.0, name="10M+ views"),
        PricingTier(min_views=5000000, bonus=2000.0, name="5M+ views"),
        PricingTier(min_views=3000000, bonus=1500.0, name="3M+ views"),
        PricingTier(min_views=1000000, bonus=1000.0, name="1M+ views"),
        PricingTier(min_views=500000, bonus=700.0, name="500K+ views"),
        PricingTier(min_views=250000, bonus=350.0, name="250K+ views"),
        PricingTier(min_views=100000, bonus=225.0, name="100K+ views"),
        PricingTier(min_views=50000, bonus=150.0, name="50K+ views"),
        PricingTier(min_views=5000, bonus=50.0, name="5K+ views"),  # $50 base at 5K views (half of Model 2)
    ]
    
    return PerformanceBasedModel(
        name="Lower Threshold Performance Model",
        min_views_qualification=5000,  # Half of Model 2's 10K threshold
        per_video_tiers=per_video_tiers
    )


def create_3k_minimum_base_model() -> FinancialModel:
    """
    Create Model 6: Current Model with 3K Minimum.
    Same as Model 1 (base rate + bonuses) but base rate only applies to Instagram videos with 3k+ views.
    """
    # Same bonus tiers as Model 1
    bonus_tiers = [
        PricingTier(min_views=5000000, bonus=3000.0, name="5M+ views"),
        PricingTier(min_views=3000000, bonus=2000.0, name="3M+ views"),
        PricingTier(min_views=1000000, bonus=1200.0, name="1M+ views"),
        PricingTier(min_views=500000, bonus=500.0, name="500K+ views"),
        PricingTier(min_views=250000, bonus=200.0, name="250K+ views"),
        PricingTier(min_views=50000, bonus=150.0, name="50K+ views"),
        PricingTier(min_views=20000, bonus=35.0, name="20K+ views"),
    ]
    
    return FinancialModel(
        name="3K Minimum Base Model",
        base_rate_under_10k=30.0,
        base_rate_over_10k=40.0,
        trial_max_videos_per_day=3,
        signed_max_videos_per_day=5,
        bonus_tiers=bonus_tiers,
        follower_threshold=10000
    )


def create_2k_base_model() -> PerformanceBasedModel:
    """
    Create Model 5: $20 Base with 2K Minimum.
    $20 base fee per video with 2,000 views minimum.
    Same compensation tiers as Model 4 (5k Minimum).
    """
    # Per video compensation tiers - same as Model 4 but with $20 at 2K views
    per_video_tiers = [
        PricingTier(min_views=10000000, bonus=3000.0, name="10M+ views"),
        PricingTier(min_views=5000000, bonus=2000.0, name="5M+ views"),
        PricingTier(min_views=3000000, bonus=1500.0, name="3M+ views"),
        PricingTier(min_views=1000000, bonus=1000.0, name="1M+ views"),
        PricingTier(min_views=500000, bonus=700.0, name="500K+ views"),
        PricingTier(min_views=250000, bonus=350.0, name="250K+ views"),
        PricingTier(min_views=100000, bonus=225.0, name="100K+ views"),
        PricingTier(min_views=50000, bonus=150.0, name="50K+ views"),
        PricingTier(min_views=5000, bonus=50.0, name="5K+ views"),
        PricingTier(min_views=2000, bonus=20.0, name="2K+ views"),  # $20 base at 2K views
    ]
    
    return PerformanceBasedModel(
        name="2K Base Model",
        min_views_qualification=2000,
        per_video_tiers=per_video_tiers
    )


def estimate_follower_count(total_views: int, total_videos: int, avg_views: float) -> int:
    """Estimate follower count based on views and video count."""
    if total_videos == 0:
        return 0
    
    if avg_views > 10000:
        estimated_followers = int(avg_views * 2)
    elif avg_views > 5000:
        estimated_followers = int(avg_views * 3)
    elif avg_views > 1000:
        estimated_followers = int(avg_views * 5)
    else:
        estimated_followers = int(avg_views * 10)
    
    return max(estimated_followers, 100)


def get_creator_base_rate(creator_name: str, model: FinancialModel) -> float:
    """Get base rate for a specific creator."""
    # John Sellers and Yunski get $40, all others get $30
    if creator_name in ["John Sellers", "Yunski"]:
        return model.base_rate_over_10k  # $40
    else:
        return model.base_rate_under_10k  # $30


def calculate_creator_financials(
    creator_name: str,
    instagram_videos: int,
    total_views: int,
    avg_views: float,
    model: FinancialModel,
    follower_count: Optional[int] = None,
    period_type: str = "signed",
    total_videos: Optional[int] = None
) -> CreatorFinancials:
    """Calculate financials for a single creator."""
    video_count_for_estimation = total_videos if total_videos else instagram_videos
    
    if follower_count is None:
        follower_count = estimate_follower_count(total_views, video_count_for_estimation, avg_views)
    
    # Use creator-specific base rate for Model 1, flat $20 for Model 3
    if model.name == "Optimized CPM Model":
        base_rate = 20.0  # Flat $20 for all creators in CPM model
    else:
        base_rate = get_creator_base_rate(creator_name, model)
    
    total_base_cost = instagram_videos * base_rate
    
    # Calculate bonus based on total views summed across ALL platforms
    # For CPM model, calculate 1 CPM directly: views / 1000 * $1
    if model.name == "Optimized CPM Model":
        # 1 CPM = $1 per 1,000 views
        bonus = (total_views / 1000.0) * 1.0
        # Cap at $1,200 (applies at 1M+ views)
        bonus = min(bonus, 1200.0)
    else:
        bonus = model.calculate_bonus(total_views)
    
    total_cost = total_base_cost + bonus
    cost_per_view = total_cost / total_views if total_views > 0 else 0
    cost_per_video = total_cost / instagram_videos if instagram_videos > 0 else 0
    
    display_video_count = total_videos if total_videos else instagram_videos
    
    return CreatorFinancials(
        creator_name=creator_name,
        total_videos=display_video_count,
        instagram_videos=instagram_videos,
        total_views=total_views,
        avg_views=avg_views,
        follower_count=follower_count,
        period_type=period_type,
        base_rate_per_video=base_rate,
        total_base_cost=total_base_cost,
        bonus=bonus,
        total_cost=total_cost,
        cost_per_view=cost_per_view,
        cost_per_video=cost_per_video
    )


def load_creator_statistics(csv_file: str = None) -> List[Dict]:
    """Load creator statistics from CSV file."""
    if csv_file is None:
        csv_file = str(Path(__file__).parent.parent / "data" / "creator_statistics.csv")
    creators = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                instagram_video_count = int(float(row.get('instagram_videos', 
                                                          row.get('unique_videos', 
                                                                  row.get('total_videos', 0)))))
                total_video_count = int(float(row.get('total_videos', 0)))
                
                creators.append({
                    'creator_name': row['creator_name'],
                    'instagram_videos': instagram_video_count,
                    'total_videos': total_video_count,
                    'total_views': int(float(row['total_views'])),
                    'avg_views': float(row['avg_views']),
                })
    except FileNotFoundError:
        print(f"Error: {csv_file} not found. Please run analyze_videos.py first.")
        return []
    
    return creators


def load_video_data(video_csv: str = None) -> Dict[str, List[Dict]]:
    """Load individual video data grouped by creator."""
    from creator_registry import create_registry, match_video_to_creator
    
    if video_csv is None:
        video_csv = str(Path(__file__).parent.parent / "data" / "videos_20251226233919.csv")
    
    registry = create_registry()
    creator_videos = {}
    
    try:
        with open(video_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                creator = match_video_to_creator(
                    registry,
                    video_url=row.get('videoUrl', ''),
                    video_handle=row.get('accountUsername', ''),
                    video_author=row.get('accountDisplayName', '')
                )
                
                if creator:
                    creator_name = creator.name
                    if creator_name not in creator_videos:
                        creator_videos[creator_name] = []
                    
                    creator_videos[creator_name].append({
                        'platform': row.get('platform', '').lower(),
                        'views': int(float(row.get('viewCount', 0) or 0)),
                        'caption': row.get('caption', ''),
                        'publishedDate': row.get('publishedDate', ''),
                        'durationSeconds': row.get('durationSeconds', ''),
                        'videoUrl': row.get('videoUrl', ''),
                    })
    except FileNotFoundError:
        print(f"Error: {video_csv} not found.")
        return {}
    
    return creator_videos


def deduplicate_videos_for_performance(videos: List[Dict]) -> List[Dict]:
    """Deduplicate videos and find top-performing platform for each unique video."""
    from datetime import datetime
    
    def normalize_caption(caption):
        if not caption:
            return ""
        return " ".join(caption.lower().split())
    
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_str.split('+')[0].strip(), fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    # Group videos by signature (caption + date + duration)
    video_groups = {}
    
    for video in videos:
        caption = normalize_caption(video.get('caption', ''))
        date_str = video.get('publishedDate', '')
        date_key = date_str[:10] if date_str else ''
        duration = int(float(video.get('durationSeconds', 0) or 0))
        
        # Create signature
        signature = (caption, date_key, duration)
        
        if signature not in video_groups:
            video_groups[signature] = []
        video_groups[signature].append(video)
    
    # For each group, find the top-performing platform
    unique_videos = []
    for signature, group_videos in video_groups.items():
        # Find the video with highest views (top-performing platform)
        top_video = max(group_videos, key=lambda v: v['views'])
        unique_videos.append(top_video)
    
    return unique_videos


@dataclass
class PerformanceFinancials:
    """Financial calculations for performance-based model."""
    creator_name: str
    total_videos: int
    qualified_videos: int
    total_views: int
    total_compensation: float
    cost_per_view: float
    cost_per_video: float


def calculate_performance_based_financials(
    creator_name: str,
    videos: List[Dict],
    model: PerformanceBasedModel
) -> PerformanceFinancials:
    """Calculate financials using performance-based model."""
    # Deduplicate videos and get top-performing platform for each
    unique_videos = deduplicate_videos_for_performance(videos)
    
    # Calculate compensation for each video
    total_compensation = 0.0
    qualified_videos = 0
    total_views = 0
    
    for video in unique_videos:
        views = video['views']
        total_views += views
        
        compensation = model.calculate_video_compensation(views)
        if compensation > 0:
            qualified_videos += 1
            total_compensation += compensation
    
    avg_views = total_views / len(unique_videos) if unique_videos else 0
    cost_per_view = total_compensation / total_views if total_views > 0 else 0
    cost_per_video = total_compensation / qualified_videos if qualified_videos > 0 else 0
    
    return PerformanceFinancials(
        creator_name=creator_name,
        total_videos=len(unique_videos),
        qualified_videos=qualified_videos,
        total_views=total_views,
        total_compensation=total_compensation,
        cost_per_view=cost_per_view,
        cost_per_video=cost_per_video
    )


def calculate_all_creators_3k_minimum(model: FinancialModel, creator_videos: Dict[str, List[Dict]]) -> List[CreatorFinancials]:
    """Calculate financials for all creators using Model 6: 3K minimum base model."""
    from analyze_videos import deduplicate_videos
    
    financials_list = []
    
    for creator_name, videos in creator_videos.items():
        # Deduplicate videos across all platforms and get top-performing platform for each
        unique_videos = deduplicate_videos_for_performance(videos)
        
        # Count videos that have 3k+ views on ANY platform (using top-performing platform view count)
        qualified_videos = [v for v in unique_videos if v.get('views', 0) >= 3000]
        qualified_count = len(qualified_videos)
        
        # Calculate total views across all platforms (for bonus)
        total_views = sum(v.get('views', 0) for v in unique_videos)
        avg_views = total_views / len(unique_videos) if unique_videos else 0
        
        # Get base rate
        base_rate = get_creator_base_rate(creator_name, model)
        
        # Calculate base cost (only for qualified videos - 3k+ views on any platform)
        total_base_cost = qualified_count * base_rate
        
        # Calculate bonus (same as Model 1 - 14-day SUM)
        bonus = model.calculate_bonus(total_views)
        
        total_cost = total_base_cost + bonus
        cost_per_view = total_cost / total_views if total_views > 0 else 0
        cost_per_video = total_cost / qualified_count if qualified_count > 0 else 0
        
        financials_list.append(CreatorFinancials(
            creator_name=creator_name,
            total_videos=len(unique_videos),
            instagram_videos=qualified_count,  # Counted videos (qualified with 3k+ views on any platform)
            total_views=total_views,
            avg_views=avg_views,
            follower_count=0,
            period_type="signed",
            base_rate_per_video=base_rate,
            total_base_cost=total_base_cost,
            bonus=bonus,
            total_cost=total_cost,
            cost_per_view=cost_per_view,
            cost_per_video=cost_per_video
        ))
    
    return financials_list


def calculate_all_creators_performance(
    model: PerformanceBasedModel,
    creator_videos: Dict[str, List[Dict]]
) -> List[PerformanceFinancials]:
    """Calculate performance-based financials for all creators."""
    results = []
    
    for creator_name, videos in creator_videos.items():
        financials = calculate_performance_based_financials(creator_name, videos, model)
        results.append(financials)
    
    return results


def calculate_all_creators(
    model: FinancialModel,
    creators_data: List[Dict],
    follower_counts: Optional[Dict[str, int]] = None,
    period_type: str = "signed"
) -> List[CreatorFinancials]:
    """Calculate financials for all creators."""
    results = []
    
    for creator_data in creators_data:
        creator_name = creator_data['creator_name']
        follower_count = None
        if follower_counts and creator_name in follower_counts:
            follower_count = follower_counts[creator_name]
        
        financials = calculate_creator_financials(
            creator_name=creator_name,
            instagram_videos=creator_data['instagram_videos'],
            total_views=creator_data['total_views'],
            avg_views=creator_data['avg_views'],
            model=model,
            follower_count=follower_count,
            period_type=period_type,
            total_videos=creator_data.get('total_videos')
        )
        
        results.append(financials)
    
    return results


def print_monthly_costs(financials_list: List[CreatorFinancials], model: FinancialModel):
    """Print monthly costs report for base rate model."""
    current_month = datetime.now().strftime("%B %Y")
    
    print("\n" + "="*100)
    print(f"MONTHLY CREATOR COSTS - {current_month}")
    print(f"MODEL: {model.name}")
    print("="*100)
    print(f"Base Rate: ${model.base_rate_under_10k:.2f} (most creators) / ${model.base_rate_over_10k:.2f} (John Sellers & Yunski)")
    print(f"Bonuses: Based on total views summed across all platforms (Instagram + TikTok + YouTube)")
    print("="*100)
    
    sorted_financials = sorted(financials_list, key=lambda x: x.total_cost, reverse=True)
    
    print(f"\n{'Creator':<25} {'IG Videos':<12} {'Total Views':<15} {'Base Cost':<15} {'Bonus':<15} {'Total Cost':<15}")
    print("-" * 100)
    
    total_base_cost = 0
    total_bonus = 0
    total_cost = 0
    total_instagram_videos = 0
    total_views = 0
    
    for f in sorted_financials:
        total_base_cost += f.total_base_cost
        total_bonus += f.bonus
        total_cost += f.total_cost
        total_instagram_videos += f.instagram_videos
        total_views += f.total_views
        
        print(f"{f.creator_name:<25} {f.instagram_videos:<12} {f.total_views:<15,} "
              f"${f.total_base_cost:<14,.2f} ${f.bonus:<14,.2f} ${f.total_cost:<14,.2f}")
    
    print("-" * 100)
    print(f"{'TOTALS':<25} {total_instagram_videos:<12} {total_views:<15,} "
          f"${total_base_cost:<14,.2f} ${total_bonus:<14,.2f} ${total_cost:<14,.2f}")
    print("="*100)
    print(f"\nTotal Monthly Cost: ${total_cost:,.2f}")
    print(f"  - Base Costs: ${total_base_cost:,.2f}")
    print(f"  - Bonuses: ${total_bonus:,.2f}")
    print(f"  - Average Cost per View: ${total_cost/total_views if total_views > 0 else 0:.6f}")
    print("="*100)


def print_performance_costs(financials_list: List[PerformanceFinancials], model: PerformanceBasedModel):
    """Print monthly costs report for performance-based model."""
    current_month = datetime.now().strftime("%B %Y")
    
    print("\n" + "="*100)
    print(f"MONTHLY CREATOR COSTS - {current_month}")
    print(f"MODEL: {model.name}")
    print("="*100)
    print(f"Compensation per video based on top-performing platform views")
    print(f"Minimum qualification: {model.min_views_qualification:,} views")
    print("="*100)
    
    sorted_financials = sorted(financials_list, key=lambda x: x.total_compensation, reverse=True)
    
    print(f"\n{'Creator':<25} {'Videos':<12} {'Qualified':<12} {'Total Views':<15} {'Compensation':<15}")
    print("-" * 100)
    
    total_cost = 0
    total_videos = 0
    total_qualified = 0
    total_views = 0
    
    for f in sorted_financials:
        total_cost += f.total_compensation
        total_videos += f.total_videos
        total_qualified += f.qualified_videos
        total_views += f.total_views
        
        print(f"{f.creator_name:<25} {f.total_videos:<12} {f.qualified_videos:<12} {f.total_views:<15,} "
              f"${f.total_compensation:<14,.2f}")
    
    print("-" * 100)
    print(f"{'TOTALS':<25} {total_videos:<12} {total_qualified:<12} {total_views:<15,} "
          f"${total_cost:<14,.2f}")
    print("="*100)
    print(f"\nTotal Monthly Cost: ${total_cost:,.2f}")
    print(f"  - Qualified Videos: {total_qualified}")
    print(f"  - Average Cost per View: ${total_cost/total_views if total_views > 0 else 0:.6f}")
    print("="*100)


def main():
    """Main function to calculate and display monthly costs.
    
    Usage:
        python3 calculate_costs.py      - Run Model 1 (Base Rate + Bonuses)
        python3 calculate_costs.py 2    - Run Model 2 (Performance-Based per Video)
        python3 calculate_costs.py 3    - Run Model 3 (Optimized CPM)
        python3 calculate_costs.py 4    - Run Model 4 (Lower Threshold Performance)
    """
    import sys
    
    # Check which model to use
    if len(sys.argv) > 1 and sys.argv[1] == "2":
        # Performance-based model
        print("Loading video data for performance-based model...")
        creator_videos = load_video_data()
        
        if not creator_videos:
            print("No video data found.")
            return
        
        print(f"Loaded videos for {len(creator_videos)} creators\n")
        
        model = create_performance_model()
        financials = calculate_all_creators_performance(model, creator_videos)
        print_performance_costs(financials, model)
    elif len(sys.argv) > 1 and sys.argv[1] == "3":
        # Optimized CPM model
        print("Loading creator statistics...")
        creators_data = load_creator_statistics()
        
        if not creators_data:
            print("No creator data found. Please run analyze_videos.py first.")
            return
        
        print(f"Loaded {len(creators_data)} creators\n")
        
        model = create_optimized_cpm_model()
        financials = calculate_all_creators(model, creators_data, follower_counts=None, period_type="signed")
        print_monthly_costs(financials, model)
    elif len(sys.argv) > 1 and sys.argv[1] == "4":
        # Lower threshold performance model
        print("Loading video data for lower threshold performance model...")
        creator_videos = load_video_data()
        
        if not creator_videos:
            print("No video data found.")
            return
        
        print(f"Loaded videos for {len(creator_videos)} creators\n")
        
        model = create_minimum_base_model()
        financials = calculate_all_creators_performance(model, creator_videos)
        print_performance_costs(financials, model)
    elif len(sys.argv) > 1 and sys.argv[1] == "5":
        # 2K base model
        print("Loading video data for 2K base model...")
        creator_videos = load_video_data()
        
        if not creator_videos:
            print("No video data found.")
            return
        
        print(f"Loaded videos for {len(creator_videos)} creators\n")
        
        model = create_2k_base_model()
        financials = calculate_all_creators_performance(model, creator_videos)
        print_performance_costs(financials, model)
    elif len(sys.argv) > 1 and sys.argv[1] == "6":
        # 3K minimum base model
        print("Loading video data for 3K minimum base model...")
        creator_videos = load_video_data()
        
        if not creator_videos:
            print("No video data found.")
            return
        
        print(f"Loaded videos for {len(creator_videos)} creators\n")
        
        model = create_3k_minimum_base_model()
        financials = calculate_all_creators_3k_minimum(model, creator_videos)
        print_monthly_costs(financials, model)
    else:
        # Default base rate model
        print("Loading creator statistics...")
        creators_data = load_creator_statistics()
        
        if not creators_data:
            print("No creator data found. Please run analyze_videos.py first.")
            return
        
        print(f"Loaded {len(creators_data)} creators\n")
        
        model = create_default_model()
        financials = calculate_all_creators(model, creators_data, follower_counts=None, period_type="signed")
        print_monthly_costs(financials, model)


if __name__ == "__main__":
    main()
