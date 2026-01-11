#!/usr/bin/env python3
"""
Process January data CSV to identify multi-platform videos and calculate proper view counts.
This script:
1. Parses the January data CSV (viral.app format)
2. Identifies videos posted on multiple platforms
3. Groups same videos across platforms and sums views
4. Returns data in format compatible with new bonus model calculations
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

def normalize_caption(caption):
    """Normalize caption for matching."""
    if not caption:
        return ""
    return " ".join(caption.lower().split())

def parse_date(date_str):
    """Parse date string."""
    if not date_str:
        return None
    try:
        # Handle format like "2026-01-10" or "2026-01-10 10:31:57+00"
        date_part = date_str.split()[0] if ' ' in date_str else date_str
        return datetime.strptime(date_part, '%Y-%m-%d')
    except:
        return None

def load_january_csv(csv_file):
    """Load January data CSV (viral.app format)."""
    videos = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                videos.append({
                    'platform': row.get('platform', '').lower(),
                    'accountUsername': row.get('accountUsername', ''),
                    'accountDisplayName': row.get('accountDisplayName', ''),
                    'videoUrl': row.get('videoUrl', ''),
                    'caption': row.get('caption', ''),
                    'publishedDate': row.get('publishedDate', ''),
                    'viewCount': parse_views(row.get('viewCount', 0)),
                    'durationSeconds': parse_views(row.get('durationSeconds', 0)),
                    'platformVideoId': row.get('platformVideoId', ''),
                })
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
        return []
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
    
    return videos

def deduplicate_videos(videos_list):
    """
    Deduplicate videos that appear on multiple platforms.
    Groups videos by same creator, similar caption, same date, and similar duration.
    Returns a list of unique videos with summed views across platforms.
    """
    if not videos_list:
        return []
    
    # Group videos by signature (caption + date + duration)
    video_groups = {}
    
    for video in videos_list:
        caption = normalize_caption(video.get('caption', ''))
        date_str = video.get('publishedDate', '')
        date_obj = parse_date(date_str)
        date_key = date_obj.strftime('%Y-%m-%d') if date_obj else date_str[:10] if date_str else ''
        duration = video.get('durationSeconds', 0)
        
        # Create a signature for grouping similar videos
        # Use caption + date + duration as the key
        group_key = (caption, date_key, duration)
        
        if group_key not in video_groups:
            video_groups[group_key] = []
        
        video_groups[group_key].append(video)
    
    # For each group, sum views and keep the top-performing platform's metadata
    unique_videos = []
    for group_key, group_videos in video_groups.items():
        # Sum views across all platforms
        total_views = sum(v.get('viewCount', 0) for v in group_videos)
        
        # Get the top-performing platform's video as representative
        top_video = max(group_videos, key=lambda v: v.get('viewCount', 0))
        
        unique_videos.append({
            'platform': top_video['platform'],
            'views': total_views,  # Summed across all platforms
            'caption': top_video['caption'],
            'publishedDate': top_video['publishedDate'],
            'durationSeconds': top_video['durationSeconds'],
            'videoUrl': top_video['videoUrl'],
            'platforms': list(set(v['platform'] for v in group_videos))
        })
    
    return unique_videos

def process_january_data(csv_file):
    """
    Process January data and return creator videos dictionary.
    Returns: Dict[str, List[Dict]] - {creator_name: [video1, video2, ...]}
    """
    registry = create_registry()
    videos = load_january_csv(csv_file)
    
    if not videos:
        return {}
    
    # Group videos by creator
    creator_videos = defaultdict(list)
    unmatched_count = 0
    
    for video in videos:
        # Match to creator using registry
        creator = match_video_to_creator(
            registry,
            video_url=video.get('videoUrl', ''),
            video_handle=video.get('accountUsername', ''),
            video_author=video.get('accountDisplayName', '')
        )
        
        if creator:
            creator_videos[creator.name].append(video)
        else:
            unmatched_count += 1
    
    if unmatched_count > 0:
        print(f"Warning: {unmatched_count} videos could not be matched to creators")
    
    # Deduplicate videos for each creator
    creator_unique_videos = {}
    for creator_name, videos_list in creator_videos.items():
        unique_videos = deduplicate_videos(videos_list)
        creator_unique_videos[creator_name] = unique_videos
    
    return creator_unique_videos

if __name__ == '__main__':
    # Find January CSV file
    january_dir = Path(__file__).parent.parent / 'januaryinfo'
    csv_files = list(january_dir.glob('videos_*.csv'))
    
    if not csv_files:
        print("Error: No January CSV file found in januaryinfo/")
        sys.exit(1)
    
    # Use the most recent CSV file
    csv_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"Processing January data from: {csv_file}")
    
    creator_videos = process_january_data(csv_file)
    
    print(f"\nProcessed {len(creator_videos)} creators")
    total_videos = sum(len(videos) for videos in creator_videos.values())
    print(f"Total unique videos: {total_videos}")
    
    # Print summary
    print("\n" + "="*80)
    print("JANUARY 2026 SUMMARY")
    print("="*80)
    for creator_name in sorted(creator_videos.keys()):
        videos = creator_videos[creator_name]
        total_views = sum(v['views'] for v in videos)
        print(f"{creator_name}: {len(videos)} videos, {total_views:,} total views")


