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


def create_optimized_model() -> FinancialModel:
    """
    Create Optimized Model: Balanced incentive and budget model.
    
    Design Principles:
    - 2.5k minimum threshold (better incentive than 3k, catches 27% more videos)
    - $25 base rate (slightly lower than $30 to control costs while remaining fair)
    - Optimized bonus tiers (reward top performers but control costs)
    - Hybrid approach: base + bonuses for balanced compensation
    
    This model targets $5,000-$7,000 budget range while maximizing creator incentives.
    """
    # Optimized bonus tiers - slightly reduced from Model 1 to control costs
    # but still rewarding for top performers
    bonus_tiers = [
        PricingTier(min_views=5000000, bonus=2500.0, name="5M+ views"),  # Reduced from $3k
        PricingTier(min_views=3000000, bonus=1500.0, name="3M+ views"),  # Reduced from $2k
        PricingTier(min_views=1000000, bonus=1000.0, name="1M+ views"),   # Reduced from $1.2k
        PricingTier(min_views=500000, bonus=400.0, name="500K+ views"),   # Reduced from $500
        PricingTier(min_views=250000, bonus=175.0, name="250K+ views"),  # Reduced from $200
        PricingTier(min_views=50000, bonus=125.0, name="50K+ views"),    # Reduced from $150
        PricingTier(min_views=20000, bonus=30.0, name="20K+ views"),     # Reduced from $35
    ]
    
    return FinancialModel(
        name="Optimized Balanced Model",
        base_rate_under_10k=25.0,  # $25 base (vs $30 in Model 6)
        base_rate_over_10k=35.0,   # $35 for John Sellers & Yunski (vs $40)
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


@dataclass
class HybridModel:
    """Hybrid model: base rate + per-video performance bonuses."""
    name: str
    base_rate_under_10k: float  # Base rate for accounts under 10k followers
    base_rate_over_10k: float   # Base rate for accounts over 10k followers
    min_views_for_base: int  # Minimum views to qualify for base (e.g., 3000)
    per_video_tiers: List[PricingTier] = None  # Performance bonus tiers per video (optional)
    use_cpm_bonus: bool = False  # If True, use CPM calculation instead of tiers
    cpm_rate: float = 1.0  # CPM rate: $1 per 1,000 views
    cpm_cap_per_video: float = None  # Optional cap per video (e.g., 1200.0)
    follower_threshold: int = 10000
    
    def calculate_video_bonus(self, views: int) -> float:
        """Calculate performance bonus for a single video based on views."""
        if self.use_cpm_bonus:
            # CPM calculation: (views / 1000) * cpm_rate
            bonus = (views / 1000.0) * self.cpm_rate
            if self.cpm_cap_per_video:
                bonus = min(bonus, self.cpm_cap_per_video)
            return bonus
        else:
            # Tiered bonuses
            if not self.per_video_tiers:
                return 0.0
            applicable_tiers = [tier for tier in self.per_video_tiers if views >= tier.min_views]
            if not applicable_tiers:
                return 0.0
            highest_tier = max(applicable_tiers, key=lambda t: t.min_views)
            return highest_tier.bonus


def create_3k_base_with_performance_bonuses() -> HybridModel:
    """
    Create Model 8: 3K Minimum Base + Per-Video CPM Bonuses.
    Combines Model 6's base structure ($30/$40 with 3k minimum) 
    with Model 3's CPM-based bonus structure (1 CPM = $1 per 1,000 views per video).
    """
    return HybridModel(
        name="3K Base with CPM Bonuses",
        base_rate_under_10k=30.0,
        base_rate_over_10k=40.0,
        min_views_for_base=3000,
        use_cpm_bonus=True,
        cpm_rate=1.0,  # $1 per 1,000 views
        cpm_cap_per_video=1200.0,  # Cap at $1,200 per video (same as Model 3)
        follower_threshold=10000
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
    # Model 1: 1 video posted on multiple platforms = $30 base + bonus ($40 for John/Yunski)
    if model.name == "Optimized CPM Model":
        base_rate = 20.0  # Flat $20 for all creators in CPM model
        total_base_cost = instagram_videos * base_rate
    else:
        base_rate = get_creator_base_rate(creator_name, model)
        # For Model 1, instagram_videos parameter represents unique videos (after deduplication)
        # So 1 video posted on multiple platforms counts as 1 video
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


def parse_december_data_for_model1(csv_file: str = None) -> Dict[str, Dict]:
    """
    Parse December spreadsheet data directly for Model 1.
    Returns dict mapping creator names to their video data.
    """
    from collections import defaultdict
    
    if csv_file is None:
        csv_file = str(Path(__file__).parent.parent / "data" / "December Data - Sheet1.csv")
    
    def parse_views(view_str):
        if not view_str:
            return 0
        try:
            return int(str(view_str).replace(',', ''))
        except (ValueError, TypeError):
            return 0
    
    def parse_amount(amount_str):
        if not amount_str:
            return 0
        try:
            return float(str(amount_str).replace(',', ''))
        except (ValueError, TypeError):
            return 0
    
    def clean_creator_name(name):
        """Remove special characters at end of name and normalize."""
        if not name:
            return name
        
        # Remove trailing special characters (*, +, etc.)
        name = name.rstrip('*+()- ')
        
        # Handle specific mappings for same person
        name_lower = name.lower()
        if 'cary' in name_lower or 'cary专用' in name_lower:
            return 'Cary'
        elif 'studiosjamen' in name_lower or 'jasper' in name_lower:
            return 'Jasper'
        elif 'integratingjohn' in name_lower:
            return 'John Sellers'
        elif 'maxxer yunski' in name_lower or 'yunski' in name_lower:
            return 'Yunski'
        elif 'mathwiththanush' in name_lower or 'thanush' in name_lower:
            return 'Thanush'
        elif 'lifebyuzi' in name_lower or 'huzaifa' in name_lower:
            return 'Huzaifa'
        elif 'kevdoesmath' in name_lower or 'kevin rhee' in name_lower:
            return 'Kevin Rhee'
        elif 'arnab' in name_lower:
            return 'Arnab'
        elif 'kiru' in name_lower:
            return 'Kiru'
        elif 'nbmath' in name_lower or 'nevin' in name_lower:
            return 'Nevin'
        elif 'yazzz' in name_lower or 'yaz' in name_lower:
            return 'Yaz'
        elif 'studyindark' in name_lower:
            return 'Studyindark'
        elif 'the mathcentral' in name_lower:
            return 'The Mathcentral'
        elif 'jxhn up' in name_lower or 'study.motivat10n' in name_lower:
            return 'Jxhn Up'
        elif 'sarah' in name_lower:
            return 'Sarah'
        elif 'daniel' in name_lower:
            return 'Daniel'
        elif 'jill' in name_lower:
            return 'Jill'
        elif 'kong' in name_lower:
            return 'Kong'
        elif 'riley' in name_lower:
            return 'Riley'
        elif 'jp' in name_lower:
            return 'JP'
        elif 'allen' in name_lower:
            return 'Allen'
        elif 'ann' in name_lower:
            return 'Ann'
        elif 'gustavo' in name_lower:
            return 'Gustavo'
        elif 'nadra' in name_lower:
            return 'Nadra'
        else:
            # Capitalize first letter of each word
            return ' '.join(word.capitalize() for word in name.split())
    
    # No mapping needed - we'll clean names directly
    creator_mapping = {}
    
    rows = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 9:
                    rows.append(row)
    except FileNotFoundError:
        return {}
    
    creator_data = defaultdict(lambda: {'videos': [], 'total_payment': 0, 'total_views': 0})
    
    i = 0
    while i < len(rows):
        row = rows[i]
        date = row[0].strip() if len(row) > 0 else ''
        creator_raw = row[1].strip() if len(row) > 1 else ''
        paid = row[8].strip().lower() if len(row) > 8 else ''
        
        if not creator_raw or not date:
            i += 1
            continue
        
        # Clean and normalize creator name
        # Remove special characters and combine same person entries
        creator = clean_creator_name(creator_raw)
        
        # If this is a paid video, collect it and any related entries below
        if paid == 'paid':
            video_group = []
            
            # Add the paid entry
            amount = parse_amount(row[7].strip() if len(row) > 7 else '')
            views = parse_views(row[6].strip() if len(row) > 6 else '')
            
            video_group.append({
                'amount': amount,
                'views': views
            })
            
            # Look ahead for related entries (same date, same creator, no Paid)
            j = i + 1
            while j < len(rows):
                next_row = rows[j]
                next_date = next_row[0].strip() if len(next_row) > 0 else ''
                next_creator_raw = next_row[1].strip() if len(next_row) > 1 else ''
                next_paid = next_row[8].strip().lower() if len(next_row) > 8 else ''
                
                # Clean next creator name
                next_creator = clean_creator_name(next_creator_raw)
                
                # If same date and creator, and not paid, it's the same video on different platform
                if next_date == date and next_creator == creator and next_paid != 'paid':
                    next_views = parse_views(next_row[6].strip() if len(next_row) > 6 else '')
                    video_group.append({
                        'amount': 0,
                        'views': next_views
                    })
                    j += 1
                else:
                    break
            
            # Sum views across all platforms for this unique video
            total_views = sum(v['views'] for v in video_group)
            payment_amount = video_group[0]['amount']  # Payment is per unique video
            
            creator_data[creator]['videos'].append({
                'payment': payment_amount,
                'views': total_views
            })
            creator_data[creator]['total_payment'] += payment_amount
            creator_data[creator]['total_views'] += total_views
            
            i = j
        else:
            i += 1
    
    # Convert to format expected by Model 1
    result = {}
    for creator, data in creator_data.items():
        result[creator] = {
            'paid_videos': len(data['videos']),
            'base_payment': data['total_payment'],
            'total_views': data['total_views']
        }
    
    return result


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
                
                # Get paid_videos and base_payment if available (from December data)
                paid_videos = row.get('paid_videos')
                if paid_videos:
                    try:
                        paid_videos = int(float(paid_videos))
                    except (ValueError, TypeError):
                        paid_videos = None
                
                base_payment = row.get('base_payment')
                if base_payment:
                    try:
                        base_payment = float(base_payment)
                    except (ValueError, TypeError):
                        base_payment = None
                
                creators.append({
                    'creator_name': row['creator_name'],
                    'instagram_videos': instagram_video_count,
                    'total_videos': total_video_count,
                    'total_views': int(float(row['total_views'])),
                    'avg_views': float(row['avg_views']),
                    'paid_videos': paid_videos,  # Include paid video count from December data
                    'base_payment': base_payment,  # Include actual base payment from December data
                })
    except FileNotFoundError:
        print(f"Error: {csv_file} not found. Please run analyze_videos.py first.")
        return []
    
    return creators


def load_video_data_from_december() -> Dict[str, List[Dict]]:
    """
    Load video data from December spreadsheet for Models 2-8.
    Returns video data in format expected by performance-based models.
    """
    from collections import defaultdict
    
    december_csv = str(Path(__file__).parent.parent / "data" / "December Data - Sheet1.csv")
    
    def parse_views(view_str):
        if not view_str:
            return 0
        try:
            return int(str(view_str).replace(',', ''))
        except (ValueError, TypeError):
            return 0
    
    def clean_creator_name(name):
        """Remove special characters at end of name and normalize."""
        if not name:
            return name
        name = name.rstrip('*+()- ')
        name_lower = name.lower()
        if 'cary' in name_lower or 'cary专用' in name_lower:
            return 'Cary'
        elif 'studiosjamen' in name_lower or 'jasper' in name_lower:
            return 'Jasper'
        elif 'integratingjohn' in name_lower:
            return 'John Sellers'
        elif 'maxxer yunski' in name_lower or 'yunski' in name_lower:
            return 'Yunski'
        elif 'mathwiththanush' in name_lower or 'thanush' in name_lower:
            return 'Thanush'
        elif 'lifebyuzi' in name_lower or 'huzaifa' in name_lower:
            return 'Huzaifa'
        elif 'kevdoesmath' in name_lower or 'kevin rhee' in name_lower:
            return 'Kevin Rhee'
        elif 'arnab' in name_lower:
            return 'Arnab'
        elif 'kiru' in name_lower:
            return 'Kiru'
        elif 'nbmath' in name_lower or 'nevin' in name_lower:
            return 'Nevin'
        elif 'yazzz' in name_lower or 'yaz' in name_lower:
            return 'Yaz'
        elif 'studyindark' in name_lower:
            return 'Studyindark'
        elif 'the mathcentral' in name_lower:
            return 'The Mathcentral'
        elif 'jxhn up' in name_lower or 'study.motivat10n' in name_lower:
            return 'Jxhn Up'
        elif 'sarah' in name_lower:
            return 'Sarah'
        elif 'daniel' in name_lower:
            return 'Daniel'
        elif 'jill' in name_lower:
            return 'Jill'
        elif 'kong' in name_lower:
            return 'Kong'
        elif 'riley' in name_lower:
            return 'Riley'
        elif 'jp' in name_lower:
            return 'JP'
        elif 'allen' in name_lower:
            return 'Allen'
        elif 'ann' in name_lower:
            return 'Ann'
        elif 'gustavo' in name_lower:
            return 'Gustavo'
        elif 'nadra' in name_lower:
            return 'Nadra'
        else:
            return ' '.join(word.capitalize() for word in name.split())
    
    rows = []
    try:
        with open(december_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 9:
                    rows.append(row)
    except FileNotFoundError:
        return {}
    
    creator_videos = defaultdict(list)
    
    i = 0
    while i < len(rows):
        row = rows[i]
        date = row[0].strip() if len(row) > 0 else ''
        creator_raw = row[1].strip() if len(row) > 1 else ''
        paid = row[8].strip().lower() if len(row) > 8 else ''
        
        if not creator_raw or not date:
            i += 1
            continue
        
        creator = clean_creator_name(creator_raw)
        
        # If this is a paid video, collect it and any related entries below
        if paid == 'paid':
            video_group = []
            
            # Add the paid entry
            views = parse_views(row[6].strip() if len(row) > 6 else '')
            platform = row[4].strip() if len(row) > 4 else ''
            link = row[3].strip() if len(row) > 3 else ''
            notes = row[2].strip() if len(row) > 2 else ''
            
            video_group.append({
                'views': views,
                'platform': platform.lower(),
                'link': link,
                'notes': notes
            })
            
            # Look ahead for related entries (same date, same creator, no Paid)
            j = i + 1
            while j < len(rows):
                next_row = rows[j]
                next_date = next_row[0].strip() if len(next_row) > 0 else ''
                next_creator_raw = next_row[1].strip() if len(next_row) > 1 else ''
                next_paid = next_row[8].strip().lower() if len(next_row) > 8 else ''
                
                next_creator = clean_creator_name(next_creator_raw)
                
                # If same date and creator, and not paid, it's the same video on different platform
                if next_date == date and next_creator == creator and next_paid != 'paid':
                    next_views = parse_views(next_row[6].strip() if len(next_row) > 6 else '')
                    next_platform = next_row[4].strip() if len(next_row) > 4 else ''
                    next_link = next_row[3].strip() if len(next_row) > 3 else ''
                    next_notes = next_row[2].strip() if len(next_row) > 2 else ''
                    
                    video_group.append({
                        'views': next_views,
                        'platform': next_platform.lower(),
                        'link': next_link,
                        'notes': next_notes
                    })
                    j += 1
                else:
                    break
            
            # Sum views across all platforms for this unique video
            total_views = sum(v['views'] for v in video_group)
            # Use top-performing platform's link and notes
            top_video = max(video_group, key=lambda v: v['views'])
            
            creator_videos[creator].append({
                'platform': top_video['platform'],
                'views': total_views,  # Summed across all platforms
                'caption': top_video['notes'],
                'publishedDate': date,
                'durationSeconds': '',
                'videoUrl': top_video['link'],
            })
            
            i = j
        else:
            i += 1
    
    return dict(creator_videos)


def load_video_data(video_csv: str = None) -> Dict[str, List[Dict]]:
    """Load individual video data grouped by creator."""
    # For Models 2-8, use December data directly
    # This ensures all creators are included with cleaned names and proper deduplication
    return load_video_data_from_december()


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


def calculate_all_creators_optimized(model: FinancialModel, creator_videos: Dict[str, List[Dict]]) -> List[CreatorFinancials]:
    """
    Calculate financials for all creators using Optimized Model: 2.5k minimum base model.
    Base rate applies to videos with 2.5k+ views on ANY platform.
    """
    financials_list = []
    
    for creator_name, videos in creator_videos.items():
        # Deduplicate videos across all platforms and get top-performing platform for each
        unique_videos = deduplicate_videos_for_performance(videos)
        
        # Count videos that qualify for base rate (2.5k+ views on any platform)
        qualified_videos_for_base = [v for v in unique_videos if v.get('views', 0) >= 2500]
        qualified_count = len(qualified_videos_for_base)
        
        # Calculate total views across all platforms (for bonus)
        total_views = sum(v.get('views', 0) for v in unique_videos)
        avg_views = total_views / len(unique_videos) if unique_videos else 0
        
        # Get base rate (use creator-specific logic)
        if creator_name in ["John Sellers", "Yunski"]:
            base_rate = model.base_rate_over_10k  # $35
        else:
            base_rate = model.base_rate_under_10k  # $25
        
        # Calculate total base cost (only for qualified videos)
        total_base_cost = qualified_count * base_rate
        
        # Calculate bonus (optimized tiers)
        bonus = model.calculate_bonus(total_views)
        
        total_cost = total_base_cost + bonus
        cost_per_view = total_cost / total_views if total_views > 0 else 0
        cost_per_video = total_cost / qualified_count if qualified_count > 0 else 0
        
        financials_list.append(CreatorFinancials(
            creator_name=creator_name,
            total_videos=len(unique_videos),
            instagram_videos=qualified_count,  # Counted videos (qualified with 2.5k+ views on any platform)
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


def calculate_all_creators_hybrid(model: HybridModel, creator_videos: Dict[str, List[Dict]]) -> List[CreatorFinancials]:
    """
    Calculate financials for all creators using Hybrid Model: 3K base + per-video performance bonuses.
    Base rate applies to videos with 3k+ views on ANY platform.
    Each video also gets performance bonuses based on its individual view count.
    """
    financials_list = []
    
    for creator_name, videos in creator_videos.items():
        # Deduplicate videos across all platforms and get top-performing platform for each
        unique_videos = deduplicate_videos_for_performance(videos)
        
        # Get base rate (use creator-specific logic)
        if creator_name in ["John Sellers", "Yunski"]:
            base_rate = model.base_rate_over_10k  # $40
        else:
            base_rate = model.base_rate_under_10k  # $30
        
        # Calculate base cost and per-video bonuses
        total_base_cost = 0.0
        total_performance_bonus = 0.0
        qualified_count = 0
        total_views = 0
        
        for video in unique_videos:
            views = video.get('views', 0)
            total_views += views
            
            # Base payment: only for videos with 3k+ views
            if views >= model.min_views_for_base:
                total_base_cost += base_rate
                qualified_count += 1
            
            # Performance bonus: based on individual video views
            video_bonus = model.calculate_video_bonus(views)
            total_performance_bonus += video_bonus
        
        avg_views = total_views / len(unique_videos) if unique_videos else 0
        total_cost = total_base_cost + total_performance_bonus
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
            bonus=total_performance_bonus,  # Per-video performance bonuses
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
    
    # For Model 1 (Default Model): Use December data directly for ALL creators
    if model.name == "Default Model":
        # Load December data directly - this includes ALL creators from spreadsheet
        december_data = parse_december_data_for_model1()
        
        # Process ALL creators from December data
        processed_creators = set()
        
        for creator_name, dec_data in december_data.items():
            processed_creators.add(creator_name.lower())
            
            paid_videos = dec_data['paid_videos']
            base_payment = dec_data['base_payment']
            total_views = dec_data['total_views']
            
            # Calculate bonus based on total views
            bonus = model.calculate_bonus(total_views)
            total_cost = base_payment + bonus
            
            # Calculate avg views
            avg_views = total_views / paid_videos if paid_videos > 0 else 0
            
            # Get follower count if available
            follower_count = None
            if follower_counts and creator_name in follower_counts:
                follower_count = follower_counts[creator_name]
            
            financials = CreatorFinancials(
                creator_name=creator_name,
                total_videos=paid_videos,
                instagram_videos=paid_videos,  # For display purposes
                total_views=total_views,
                avg_views=avg_views,
                follower_count=follower_count or 0,
                period_type=period_type,
                base_rate_per_video=base_payment / paid_videos if paid_videos > 0 else 0,
                total_base_cost=base_payment,
                bonus=bonus,
                total_cost=total_cost,
                cost_per_view=total_cost / total_views if total_views > 0 else 0,
                cost_per_video=total_cost / paid_videos if paid_videos > 0 else 0
            )
            
            results.append(financials)
        
        # Model 1 uses ONLY December data - no fallback to creator_statistics
        # This ensures clean names and accurate totals
    else:
        # For other models, use creator_statistics as before
        for creator_data in creators_data:
            creator_name = creator_data['creator_name']
            follower_count = None
            if follower_counts and creator_name in follower_counts:
                follower_count = follower_counts[creator_name]
            
            video_count_for_base = creator_data['instagram_videos']
            financials = calculate_creator_financials(
                creator_name=creator_name,
                instagram_videos=video_count_for_base,
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
        # Optimized CPM model - use December data
        print("Loading December data for CPM model...")
        december_data = parse_december_data_for_model1()
        
        if not december_data:
            print("No December data found.")
            return
        
        # Convert December data to creator_statistics format for Model 3
        creators_data = []
        for creator_name, dec_data in december_data.items():
            creators_data.append({
                'creator_name': creator_name,
                'instagram_videos': dec_data['paid_videos'],
                'total_videos': dec_data['paid_videos'],
                'total_views': dec_data['total_views'],
                'avg_views': dec_data['total_views'] / dec_data['paid_videos'] if dec_data['paid_videos'] > 0 else 0
            })
        
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
    elif len(sys.argv) > 1 and sys.argv[1] == "7":
        # Optimized balanced model
        print("Loading video data for Optimized Balanced Model...")
        creator_videos = load_video_data()
        
        if not creator_videos:
            print("No video data found.")
            return
        
        print(f"Loaded videos for {len(creator_videos)} creators\n")
        
        model = create_optimized_model()
        financials = calculate_all_creators_optimized(model, creator_videos)
        print_monthly_costs(financials, model)
    elif len(sys.argv) > 1 and sys.argv[1] == "8":
        # 3K base with per-video performance bonuses
        print("Loading video data for 3K Base with Performance Bonuses...")
        creator_videos = load_video_data()
        
        if not creator_videos:
            print("No video data found.")
            return
        
        print(f"Loaded videos for {len(creator_videos)} creators\n")
        
        model = create_3k_base_with_performance_bonuses()
        financials = calculate_all_creators_hybrid(model, creator_videos)
        
        # Print hybrid model costs
        current_month = datetime.now().strftime("%B %Y")
        print("\n" + "="*100)
        print(f"MONTHLY CREATOR COSTS - {current_month}")
        print(f"MODEL: {model.name}")
        print("="*100)
        print(f"Base Rate: ${model.base_rate_under_10k:.2f} (most creators) / ${model.base_rate_over_10k:.2f} (John Sellers & Yunski)")
        print(f"Base Qualification: {model.min_views_for_base:,}+ views on any platform")
        print(f"Performance Bonuses: Per-video bonuses based on individual video views")
        print("="*100)
        
        sorted_financials = sorted(financials, key=lambda x: x.total_cost, reverse=True)
        
        print(f"\n{'Creator':<25} {'Qualified':<12} {'Total Views':<15} {'Base Cost':<15} {'Per-Video Bonus':<18} {'Total Cost':<15}")
        print("-" * 100)
        
        total_base_cost = 0
        total_bonus = 0
        total_cost = 0
        total_qualified = 0
        total_views = 0
        
        for f in sorted_financials:
            total_base_cost += f.total_base_cost
            total_bonus += f.bonus
            total_cost += f.total_cost
            total_qualified += f.instagram_videos
            total_views += f.total_views
            
            print(f"{f.creator_name:<25} {f.instagram_videos:<12} {f.total_views:<15,} "
                  f"${f.total_base_cost:<14,.2f} ${f.bonus:<17,.2f} ${f.total_cost:<14,.2f}")
        
        print("-" * 100)
        print(f"{'TOTALS':<25} {total_qualified:<12} {total_views:<15,} "
              f"${total_base_cost:<14,.2f} ${total_bonus:<17,.2f} ${total_cost:<14,.2f}")
        print("="*100)
        print(f"\nTotal Monthly Cost: ${total_cost:,.2f}")
        print(f"  - Base Costs: ${total_base_cost:,.2f}")
        print(f"  - Per-Video Performance Bonuses: ${total_bonus:,.2f}")
        print(f"  - Average Cost per View: ${total_cost/total_views if total_views > 0 else 0:.6f}")
        print("="*100)
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
