#!/usr/bin/env python3
"""
Process December data CSV to identify multi-platform videos and calculate proper view counts.
This script:
1. Parses the December data CSV
2. Identifies videos posted on multiple platforms (paid videos with other links)
3. Groups same videos across platforms and sums views
4. Exports data in format compatible with existing model calculations
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from creator_registry import create_registry, match_video_to_creator

def parse_views(view_str):
    """Parse view count string (may contain commas)."""
    if not view_str:
        return 0
    try:
        return int(str(view_str).replace(',', ''))
    except (ValueError, TypeError):
        return 0

def normalize_platform(platform_str):
    """Normalize platform name."""
    if not platform_str:
        return ''
    platform = platform_str.strip().lower()
    if 'ins' in platform or 'instagram' in platform:
        return 'instagram'
    elif 'tiktok' in platform:
        return 'tiktok'
    elif 'youtube' in platform:
        return 'youtube'
    return platform

def parse_december_csv(csv_file):
    """Parse December data CSV and return raw rows."""
    rows = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:  # Ensure we have enough columns
                    rows.append(row)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
        return []
    return rows

def group_videos_by_creator(rows):
    """Group rows by creator name."""
    creator_rows = defaultdict(list)
    
    for i, row in enumerate(rows):
        if len(row) < 8:
            continue
        creator_name = row[1].strip() if len(row) > 1 else ''
        if creator_name:
            creator_rows[creator_name].append((i, row))
    
    return creator_rows

def identify_multi_platform_videos(creator_rows):
    """
    Identify videos posted on multiple platforms.
    A video is multi-platform if:
    - It's marked as "Paid" 
    - There are other links (rows) below it with the same date and creator
    """
    registry = create_registry()
    creator_videos = defaultdict(list)
    processed_rows = set()  # Track which rows we've already processed
    
    for creator_name, rows_list in creator_rows.items():
        # Sort by row index to maintain order
        rows_list.sort(key=lambda x: x[0])
        
        i = 0
        while i < len(rows_list):
            row_idx, row = rows_list[i]
            
            # Skip if already processed
            if row_idx in processed_rows:
                i += 1
                continue
            
            if len(row) < 8:
                i += 1
                continue
            
            date = row[0].strip() if len(row) > 0 else ''
            creator = row[1].strip() if len(row) > 1 else ''
            notes = row[2].strip() if len(row) > 2 else ''
            link = row[3].strip() if len(row) > 3 else ''
            platform = normalize_platform(row[4].strip() if len(row) > 4 else '')
            date2 = row[5].strip() if len(row) > 5 else ''
            views_str = row[6].strip() if len(row) > 6 else ''
            amount_str = row[7].strip() if len(row) > 7 else ''
            paid_status = row[8].strip() if len(row) > 8 else ''
            
            views = parse_views(views_str)
            amount = parse_views(amount_str)
            is_paid = paid_status.lower() == 'paid'
            
            # If this is a paid video, check if there are other links below it
            if is_paid and link:
                # Look ahead to find related videos (same date, same creator)
                video_group = []
                
                # Start with the paid video
                video_group.append({
                    'date': date,
                    'creator': creator,
                    'notes': notes,
                    'link': link,
                    'platform': platform,
                    'views': views,
                    'amount': amount,
                    'paid': True,
                    'row_idx': row_idx
                })
                processed_rows.add(row_idx)
                
                # Look for other links with same date and creator (within next few rows)
                j = i + 1
                max_lookahead = min(j + 5, len(rows_list))  # Look ahead up to 5 rows
                
                while j < max_lookahead:
                    next_row_idx, next_row = rows_list[j]
                    
                    if next_row_idx in processed_rows:
                        j += 1
                        continue
                    
                    if len(next_row) < 8:
                        j += 1
                        continue
                    
                    next_date = next_row[0].strip() if len(next_row) > 0 else ''
                    next_creator = next_row[1].strip() if len(next_row) > 1 else ''
                    next_link = next_row[3].strip() if len(next_row) > 3 else ''
                    next_paid = next_row[8].strip().lower() == 'paid' if len(next_row) > 8 else False
                    
                    # If same date and creator, and not another paid entry, it's likely the same video
                    if next_date == date and next_creator == creator and next_link and not next_paid:
                        next_platform = normalize_platform(next_row[4].strip() if len(next_row) > 4 else '')
                        next_views = parse_views(next_row[6].strip() if len(next_row) > 6 else '')
                        
                        video_group.append({
                            'date': next_date,
                            'creator': next_creator,
                            'notes': next_row[2].strip() if len(next_row) > 2 else '',
                            'link': next_link,
                            'platform': next_platform,
                            'views': next_views,
                            'amount': 0,
                            'paid': False,
                            'row_idx': next_row_idx
                        })
                        processed_rows.add(next_row_idx)
                        j += 1
                    else:
                        # Different date or creator, stop grouping
                        break
                
                # Match creator name using registry
                matched_creator = None
                for video in video_group:
                    creator_match = match_video_to_creator(
                        registry,
                        video_url=video['link'],
                        video_handle='',
                        video_author=video['creator']
                    )
                    if creator_match:
                        matched_creator = creator_match.name
                        break
                
                # If no match found, try to match by creator name directly
                if not matched_creator:
                    # Try to find creator in registry by name or handle
                    for reg_creator in registry.get_all_creators():
                        if reg_creator.name.lower() == creator.lower():
                            matched_creator = reg_creator.name
                            break
                        # Also check handles
                        for acc in reg_creator.accounts:
                            if acc.handle.lower() == creator.lower():
                                matched_creator = reg_creator.name
                                break
                        if matched_creator:
                            break
                
                # Use matched creator or original creator name
                final_creator = matched_creator if matched_creator else creator
                
                # Sum views across all platforms for this video
                total_views = sum(v['views'] for v in video_group)
                
                # Find the top-performing platform
                top_video = max(video_group, key=lambda v: v['views']) if video_group else video_group[0]
                
                # Create video entry
                video_entry = {
                    'creator_name': final_creator,
                    'platform': top_video['platform'],
                    'views': total_views,  # Sum of views across all platforms
                    'caption': top_video['notes'],
                    'publishedDate': top_video['date'],
                    'durationSeconds': '',  # Not available in December data
                    'videoUrl': top_video['link'],
                    'all_platforms': video_group,  # Keep track of all platforms
                    'amount': video_group[0]['amount'] if video_group else 0
                }
                
                creator_videos[final_creator].append(video_entry)
                
                # Move to next unprocessed row
                i += 1
            else:
                # Not a paid video, process individually (only if it has views)
                if link and views > 0 and row_idx not in processed_rows:
                    # Try to match creator
                    matched_creator = match_video_to_creator(
                        registry,
                        video_url=link,
                        video_handle='',
                        video_author=creator
                    )
                    
                    if matched_creator:
                        final_creator = matched_creator.name
                    else:
                        # Try to find by name or handle
                        final_creator = None
                        for reg_creator in registry.get_all_creators():
                            if reg_creator.name.lower() == creator.lower():
                                final_creator = reg_creator.name
                                break
                            # Also check handles
                            for acc in reg_creator.accounts:
                                if acc.handle.lower() == creator.lower():
                                    final_creator = reg_creator.name
                                    break
                            if final_creator:
                                break
                        
                        if not final_creator:
                            final_creator = creator
                    
                    video_entry = {
                        'creator_name': final_creator,
                        'platform': platform,
                        'views': views,
                        'caption': notes,
                        'publishedDate': date,
                        'durationSeconds': '',
                        'videoUrl': link,
                        'all_platforms': [{
                            'date': date,
                            'creator': creator,
                            'link': link,
                            'platform': platform,
                            'views': views
                        }],
                        'amount': amount
                    }
                    
                    creator_videos[final_creator].append(video_entry)
                    processed_rows.add(row_idx)
                
                i += 1
    
    return creator_videos

def export_to_video_csv(creator_videos, output_file):
    """Export processed videos to CSV format compatible with existing scripts."""
    fieldnames = ['videoUrl', 'accountUsername', 'accountDisplayName', 'platform', 
                  'viewCount', 'caption', 'publishedDate', 'durationSeconds']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for creator_name, videos in creator_videos.items():
            for video in videos:
                # Extract username from URL if possible
                username = ''
                if 'instagram.com' in video['videoUrl']:
                    # Try to extract username from Instagram URL
                    parts = video['videoUrl'].split('/')
                    if len(parts) > 3:
                        username = parts[3]
                elif 'tiktok.com' in video['videoUrl']:
                    # Try to extract username from TikTok URL
                    parts = video['videoUrl'].split('/')
                    for i, part in enumerate(parts):
                        if part == '@' and i + 1 < len(parts):
                            username = parts[i + 1]
                            break
                
                writer.writerow({
                    'videoUrl': video['videoUrl'],
                    'accountUsername': username,
                    'accountDisplayName': creator_name,
                    'platform': video['platform'],
                    'viewCount': video['views'],
                    'caption': video['caption'],
                    'publishedDate': video['publishedDate'],
                    'durationSeconds': video['durationSeconds']
                })

def calculate_john_payout(creator_videos):
    """Calculate John's total payout from December data."""
    john_names = ['John Sellers', 'integratingjohn', 'John']
    total_payout = 0
    
    for john_name in john_names:
        if john_name in creator_videos:
            for video in creator_videos[john_name]:
                if 'amount' in video:
                    total_payout += video['amount']
    
    # Also check for any creator that might be John
    for creator_name, videos in creator_videos.items():
        if 'john' in creator_name.lower() and creator_name not in john_names:
            for video in videos:
                if 'amount' in video:
                    total_payout += video['amount']
    
    return total_payout

def count_paid_videos_by_creator(rows):
    """Count paid videos per creator from December data."""
    creator_paid_counts = defaultdict(int)
    
    for row in rows:
        if len(row) < 9:
            continue
        
        creator = row[1].strip() if len(row) > 1 else ''
        paid = row[8].strip().lower() if len(row) > 8 else ''
        
        if paid == 'paid' and creator:
            creator_paid_counts[creator] += 1
    
    return creator_paid_counts

def main():
    """Main function to process December data."""
    data_dir = Path(__file__).parent.parent / 'data'
    december_csv = data_dir / 'December Data - Sheet1.csv'
    
    print("Processing December data...")
    print(f"Reading from: {december_csv}")
    
    # Parse CSV
    rows = parse_december_csv(december_csv)
    print(f"Loaded {len(rows)} rows")
    
    # Group by creator
    creator_rows = group_videos_by_creator(rows)
    print(f"Found {len(creator_rows)} creators")
    
    # Identify multi-platform videos
    print("Identifying multi-platform videos...")
    creator_videos = identify_multi_platform_videos(creator_rows)
    
    total_videos = sum(len(videos) for videos in creator_videos.values())
    print(f"Processed {total_videos} unique videos across {len(creator_videos)} creators")
    
    # Calculate John's payout
    john_payout = calculate_john_payout(creator_videos)
    print(f"\nJohn's total payout: ${john_payout}")
    
    if john_payout != 740:
        print(f"WARNING: Expected $740, but calculated ${john_payout}")
        print("Checking individual videos...")
        for john_name in ['John Sellers', 'integratingjohn', 'John']:
            if john_name in creator_videos:
                print(f"\n{john_name} videos:")
                for video in creator_videos[john_name]:
                    print(f"  Amount: ${video.get('amount', 0)}, Views: {video['views']}, Platform: {video['platform']}")
    else:
        print("✓ John's payout matches expected $740")
    
    # Export to video CSV format
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = data_dir / f'videos_december_{timestamp}.csv'
    print(f"\nExporting to: {output_file}")
    export_to_video_csv(creator_videos, output_file)
    print("Export complete!")
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    for creator_name in sorted(creator_videos.keys()):
        videos = creator_videos[creator_name]
        total_views = sum(v['views'] for v in videos)
        total_amount = sum(v.get('amount', 0) for v in videos)
        print(f"{creator_name}: {len(videos)} videos, {total_views:,} total views, ${total_amount:.2f} paid")
    
    return creator_videos

if __name__ == "__main__":
    main()

