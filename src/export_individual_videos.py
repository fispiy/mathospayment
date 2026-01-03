#!/usr/bin/env python3
"""
Script to export individual videos with summed view counts and scripted column.
Uses the exact same deduplication logic as analyze_videos.py, but groups videos
to sum views across platforms for each unique video.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the exact deduplication functions from analyze_videos
from analyze_videos import deduplicate_videos, normalize_caption, parse_date, safe_int
from creator_registry import create_registry, match_video_to_creator

def group_videos_for_summing(videos_list):
    """
    Group videos that are the same content across platforms.
    Uses the same matching logic as deduplicate_videos, but groups them instead.
    Returns a list of groups, where each group contains videos that are the same content.
    """
    if not videos_list:
        return []
    
    video_groups = []
    seen_groups = set()  # Track which groups we've created
    
    for video in videos_list:
        creator_name = video.get('creator_name', '')
        caption = normalize_caption(video.get('caption', ''))
        published_date = parse_date(video.get('publishedDate', ''))
        duration = safe_int(video.get('durationSeconds', 0))
        
        if published_date:
            date_key = published_date.strftime('%Y-%m-%d')
        else:
            date_key = video.get('publishedDate', '')[:10] if video.get('publishedDate') else ''
        
        # Try to find matching group using same logic as deduplicate_videos
        found_match = False
        matching_group = None
        
        for seen_key in seen_groups:
            seen_creator, seen_caption, seen_date, seen_duration = seen_key
            
            # Same creator
            if seen_creator != creator_name:
                continue
            
            # Same or very similar caption
            if caption and seen_caption:
                caption_match = (caption == seen_caption or 
                               (len(caption) > 10 and len(seen_caption) > 10 and 
                                (caption in seen_caption or seen_caption in caption)))
            else:
                caption_match = (not caption and not seen_caption)
            
            if not caption_match:
                continue
            
            # Same date or within 1 day
            date_match = False
            if seen_date == date_key:
                date_match = True
            elif date_key and seen_date:
                try:
                    date1 = datetime.strptime(date_key, '%Y-%m-%d')
                    date2 = datetime.strptime(seen_date, '%Y-%m-%d')
                    if abs((date1 - date2).days) <= 1:
                        date_match = True
                except:
                    pass
            
            if not date_match:
                continue
            
            # Similar duration (within 5 seconds)
            if abs(seen_duration - duration) <= 5:
                # Find the group that matches this signature
                for group in video_groups:
                    if group and normalize_caption(group[0].get('caption', '')) == seen_caption:
                        matching_group = group
                        break
                found_match = True
                break
        
        if found_match and matching_group:
            # Add to existing group
            matching_group.append(video)
        else:
            # Create new group
            group_key = (creator_name, caption, date_key, duration)
            seen_groups.add(group_key)
            video_groups.append([video])
    
    return video_groups

def main():
    # Load creator registry
    print("Loading creator registry...")
    registry = create_registry()
    print(f"Loaded {len(registry.get_all_creators())} creators\n")
    
    # Load video data
    print("Loading video data...")
    csv_file = str(Path(__file__).parent.parent / "data" / "videos_20251226233919.csv")
    
    creator_videos = defaultdict(list)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Match to creator
                creator = match_video_to_creator(
                    registry,
                    video_url=row.get('videoUrl', ''),
                    video_handle=row.get('accountUsername', ''),
                    video_author=row.get('accountDisplayName', '')
                )
                
                if creator:
                    # Add creator name to row
                    row['creator_name'] = creator.name
                    creator_videos[creator.name].append(row)
    
    except FileNotFoundError:
        print(f"ERROR: File {csv_file} not found!")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    total_entries = sum(len(videos) for videos in creator_videos.values())
    print(f"Loaded {total_entries} video entries")
    
    # Process each creator's videos - group and sum views
    print("Grouping videos by creator and deduplicating...")
    
    unique_video_rows = []
    
    for creator_name, videos in creator_videos.items():
        # Group videos that are the same content
        video_groups = group_videos_for_summing(videos)
        
        for group in video_groups:
            # Sum views across all platforms for this unique video
            total_views = sum(safe_int(v.get('viewCount', 0)) for v in group)
            
            # Get representative video data (use one with most views)
            representative = max(group, key=lambda v: safe_int(v.get('viewCount', 0)))
            
            # Create identifier for the video
            caption = representative.get('caption', '') or '(no caption)'
            date_str = representative.get('publishedDate', '')[:10] if representative.get('publishedDate') else ''
            video_id = representative.get('platformVideoId', '')
            platform = representative.get('platform', '')
            
            # Create a readable identifier
            video_identifier = f"{creator_name} - {caption[:50]}"
            if date_str:
                video_identifier += f" ({date_str})"
            
            unique_video_rows.append({
                'creator_name': creator_name,
                'video_identifier': video_identifier,
                'caption': caption,
                'published_date': date_str,
                'platform_video_id': video_id,
                'platform': platform,
                'video_url': representative.get('videoUrl', ''),
                'total_views': total_views,
                'platforms': ', '.join(sorted(set(v.get('platform', '') for v in group))),
                'scripted': ''  # Empty column for user to fill in
            })
    
    print(f"Found {len(unique_video_rows)} unique videos\n")
    
    # Verify count matches original deduplication
    total_unique_original = 0
    for creator_name, videos in creator_videos.items():
        unique = deduplicate_videos(videos)
        total_unique_original += len(unique)
    
    print(f"Verification:")
    print(f"  - Original deduplicate_videos function: {total_unique_original} unique videos")
    print(f"  - This grouping function: {len(unique_video_rows)} unique videos")
    
    if len(unique_video_rows) != total_unique_original:
        print(f"\n⚠️  WARNING: Count mismatch! Difference: {abs(len(unique_video_rows) - total_unique_original)}")
        print(f"   This might indicate a difference in grouping logic.")
    
    # Sort by total views descending
    unique_video_rows.sort(key=lambda x: x['total_views'], reverse=True)
    
    # Write to CSV
    output_file = str(Path(__file__).parent.parent / "data" / "individual_videos.csv")
    
    fieldnames = [
        'creator_name',
        'video_identifier',
        'caption',
        'published_date',
        'platform_video_id',
        'platform',
        'video_url',
        'total_views',
        'platforms',
        'scripted'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_video_rows)
    
    print(f"\nExported {len(unique_video_rows)} unique videos to {output_file}")
    print(f"\nColumns:")
    print(f"  - creator_name: Creator name")
    print(f"  - video_identifier: Readable identifier for the video")
    print(f"  - caption: Video caption")
    print(f"  - published_date: Publication date")
    print(f"  - platform_video_id: Platform-specific video ID")
    print(f"  - platform: Primary platform (highest views)")
    print(f"  - video_url: URL to the video")
    print(f"  - total_views: Sum of views across all platforms")
    print(f"  - platforms: List of platforms this video appears on")
    print(f"  - scripted: Column for you to mark if video was scripted (Yes/No)")
    
    print(f"\nTop 10 videos by total views:")
    for i, row in enumerate(unique_video_rows[:10], 1):
        print(f"  {i}. {row['creator_name']}: {row['total_views']:,} views - {row['caption'][:60]}")

if __name__ == "__main__":
    main()
