#!/usr/bin/env python3
"""
Script to analyze viral.app video data and generate statistics per creator.
Uses built-in csv module instead of pandas.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from creator_registry import create_registry, match_video_to_creator

def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int."""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def normalize_caption(caption):
    """Normalize caption for comparison (remove extra spaces, lowercase)."""
    if not caption:
        return ""
    # Remove extra whitespace and convert to lowercase
    return " ".join(caption.lower().split())

def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        from datetime import datetime
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S%z']:
            try:
                return datetime.strptime(date_str.split('+')[0].strip(), fmt)
            except ValueError:
                continue
        return None
    except:
        return None

def deduplicate_videos(videos_list):
    """
    Deduplicate videos that appear on multiple platforms.
    Groups videos by same creator, similar caption, same date, and similar duration.
    Returns a list of unique videos (one per content piece).
    """
    if not videos_list:
        return []
    
    # Group videos by creator first
    unique_videos = []
    seen_groups = set()
    
    for video in videos_list:
        creator_name = video.get('creator_name', '')
        caption = normalize_caption(video.get('caption', ''))
        published_date = parse_date(video.get('publishedDate', ''))
        duration = safe_int(video.get('durationSeconds', 0))
        platform = video.get('platform', '')
        
        # Create a signature for grouping similar videos
        # Use caption + date + duration as the key
        if published_date:
            date_key = published_date.strftime('%Y-%m-%d')
        else:
            date_key = video.get('publishedDate', '')[:10] if video.get('publishedDate') else ''
        
        # Group by caption and date (within 1 day tolerance)
        # Also consider duration (within 5 seconds tolerance)
        group_key = (creator_name, caption, date_key, duration)
        
        # Check if we've seen a similar video
        found_match = False
        for seen_key in seen_groups:
            seen_creator, seen_caption, seen_date, seen_duration = seen_key
            
            # Same creator
            if seen_creator != creator_name:
                continue
            
            # Same or very similar caption
            if caption and seen_caption:
                # Exact match or one contains the other (for slight variations)
                if caption == seen_caption or (len(caption) > 10 and len(seen_caption) > 10 and 
                                               (caption in seen_caption or seen_caption in caption)):
                    # Same date or within 1 day
                    if seen_date == date_key:
                        # Similar duration (within 5 seconds)
                        if abs(seen_duration - duration) <= 5:
                            found_match = True
                            break
                    # Also check if dates are within 1 day
                    elif date_key and seen_date:
                        try:
                            from datetime import datetime, timedelta
                            date1 = datetime.strptime(date_key, '%Y-%m-%d')
                            date2 = datetime.strptime(seen_date, '%Y-%m-%d')
                            if abs((date1 - date2).days) <= 1:
                                if abs(seen_duration - duration) <= 5:
                                    found_match = True
                                    break
                        except:
                            pass
        
        if not found_match:
            # This is a unique video
            unique_videos.append(video)
            seen_groups.add(group_key)
    
    return unique_videos

def main():
    # Load creator registry
    print("Loading creator registry...")
    registry = create_registry()
    print(f"Loaded {len(registry.get_all_creators())} creators\n")
    
    # Load and process video data
    print("Loading video data...")
    csv_file = str(Path(__file__).parent.parent / "data" / "videos_20251226233919.csv")
    
    creator_stats = defaultdict(lambda: {
        'videos': [],
        'total_views': 0,
        'total_likes': 0,
        'total_comments': 0,
        'total_shares': 0,
        'platforms': set(),
    })
    
    unmatched_usernames = defaultdict(int)
    total_videos = 0
    matched_videos = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_videos += 1
                
                # Get video data
                video_url = row.get('videoUrl', '')
                account_username = row.get('accountUsername', '')
                account_display_name = row.get('accountDisplayName', '')
                
                # Match to creator
                creator = match_video_to_creator(
                    registry,
                    video_url=video_url,
                    video_handle=account_username,
                    video_author=account_display_name
                )
                
                if creator:
                    matched_videos += 1
                    creator_name = creator.name
                    
                    # Add creator name to row for deduplication
                    row_with_creator = row.copy()
                    row_with_creator['creator_name'] = creator_name
                    
                    # Collect stats
                    # Sum views across ALL platforms (Instagram + TikTok + YouTube) for bonus calculation
                    stats = creator_stats[creator_name]
                    stats['videos'].append(row_with_creator)
                    stats['total_views'] += safe_int(row.get('viewCount', 0))  # Summed across all platforms
                    stats['total_likes'] += safe_int(row.get('likeCount', 0))
                    stats['total_comments'] += safe_int(row.get('commentCount', 0))
                    stats['total_shares'] += safe_int(row.get('shareCount', 0))
                    stats['platforms'].add(row.get('platform', ''))
                else:
                    unmatched_usernames[account_username] += 1
    
    except FileNotFoundError:
        print(f"ERROR: File {csv_file} not found!")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"Loaded {total_videos} videos")
    print(f"Matched {matched_videos} videos to creators")
    print(f"Unmatched {total_videos - matched_videos} videos\n")
    
    # Deduplicate videos across platforms for each creator
    print("Deduplicating videos across platforms...")
    total_before_dedup = sum(len(stats['videos']) for stats in creator_stats.values())
    
    for creator_name, stats in creator_stats.items():
        if stats['videos']:
            # Get all videos
            all_videos = stats['videos']
            
            # Deduplicate all videos (across all platforms)
            unique_videos = deduplicate_videos(all_videos)
            stats['unique_videos'] = unique_videos
            stats['unique_video_count'] = len(unique_videos)
            
            # Filter Instagram videos only
            instagram_videos = [v for v in all_videos if v.get('platform', '').lower() == 'instagram']
            
            # Deduplicate Instagram videos only (for base rate calculation)
            unique_instagram_videos = deduplicate_videos(instagram_videos)
            stats['unique_instagram_videos'] = unique_instagram_videos
            stats['unique_instagram_video_count'] = len(unique_instagram_videos)
        else:
            stats['unique_videos'] = []
            stats['unique_video_count'] = 0
            stats['unique_instagram_videos'] = []
            stats['unique_instagram_video_count'] = 0
    
    total_after_dedup = sum(stats['unique_video_count'] for stats in creator_stats.values())
    total_instagram_videos = sum(stats['unique_instagram_video_count'] for stats in creator_stats.values())
    print(f"Before deduplication: {total_before_dedup} video entries")
    print(f"After deduplication: {total_after_dedup} unique videos (across all platforms)")
    print(f"Instagram videos (for base rate): {total_instagram_videos} unique videos")
    print(f"Deduplicated: {total_before_dedup - total_after_dedup} duplicate entries\n")
    
    # Calculate statistics for each creator
    print("="*100)
    print("CREATOR STATISTICS (Based on Unique Videos)")
    print("="*100)
    
    results = []
    
    for creator_name, stats in creator_stats.items():
        # Use Instagram videos for base rate counting (deduplicated)
        num_instagram_videos = stats['unique_instagram_video_count']
        # Use all unique videos for total count display
        num_videos = stats['unique_video_count']
        if num_videos == 0:
            continue
        
        # Calculate averages based on unique videos
        avg_views = stats['total_views'] / num_videos if num_videos > 0 else 0
        avg_likes = stats['total_likes'] / num_videos if num_videos > 0 else 0
        avg_comments = stats['total_comments'] / num_videos if num_videos > 0 else 0
        
        # Find max values (across all platforms)
        max_views = 0
        max_likes = 0
        total_engagement_rate = 0
        total_virality = 0
        
        for video in stats['videos']:  # Use all videos for max calculations
            views = safe_int(video.get('viewCount', 0))
            likes = safe_int(video.get('likeCount', 0))
            max_views = max(max_views, views)
            max_likes = max(max_likes, likes)
            total_engagement_rate += safe_float(video.get('engagementRate', 0))
            total_virality += safe_float(video.get('viralityFactor', 0))
        
        avg_engagement_rate = total_engagement_rate / num_videos if num_videos > 0 else 0
        avg_virality = total_virality / num_videos if num_videos > 0 else 0
        
        # Calculate overall engagement rate
        overall_engagement_rate = 0
        if stats['total_views'] > 0:
            overall_engagement_rate = (stats['total_likes'] + stats['total_comments'] + stats['total_shares']) / stats['total_views']
        
        result = {
            'creator_name': creator_name,
            'total_videos': num_videos,  # Total unique videos across all platforms
            'instagram_videos': num_instagram_videos,  # Instagram videos only (for base rate)
            'platforms': ', '.join(sorted(stats['platforms'])),
            'total_views': stats['total_views'],  # Views across all platforms
            'total_likes': stats['total_likes'],
            'total_comments': stats['total_comments'],
            'total_shares': stats['total_shares'],
            'avg_views': round(avg_views, 2),
            'avg_likes': round(avg_likes, 2),
            'avg_comments': round(avg_comments, 2),
            'max_views': max_views,
            'max_likes': max_likes,
            'avg_engagement_rate': round(avg_engagement_rate, 4),
            'avg_virality_factor': round(avg_virality, 4),
            'overall_engagement_rate': round(overall_engagement_rate, 4),
        }
        
        results.append(result)
    
    # Sort by total views
    results.sort(key=lambda x: x['total_views'], reverse=True)
    
    # Print results
    if results:
        # Print header
        header = f"{'Creator Name':<25} {'Videos':<8} {'Total Views':<15} {'Avg Views':<12} {'Total Likes':<15} {'Eng Rate':<10} {'Platforms':<20}"
        print(header)
        print("-" * 100)
        
        for r in results:
            print(f"{r['creator_name']:<25} {r['total_videos']:<8} {r['total_views']:<15,} {r['avg_views']:<12,.0f} {r['total_likes']:<15,} {r['overall_engagement_rate']:<10.4f} {r['platforms']:<20}")
        
    # Save to CSV
    output_file = str(Path(__file__).parent.parent / "data" / "creator_statistics.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            # Add total_video_entries field to show original count
            for result in results:
                creator_name = result['creator_name']
                if creator_name in creator_stats:
                    result['total_video_entries'] = len(creator_stats[creator_name]['videos'])
                    result['unique_videos'] = creator_stats[creator_name]['unique_video_count']
                else:
                    result['total_video_entries'] = result['total_videos']
                    result['unique_videos'] = result['total_videos']
            
            fieldnames = list(results[0].keys())
            # Reorder to put unique_videos and total_video_entries near total_videos
            fieldnames.remove('unique_videos')
            fieldnames.remove('total_video_entries')
            fieldnames.insert(fieldnames.index('total_videos') + 1, 'unique_videos')
            fieldnames.insert(fieldnames.index('unique_videos') + 1, 'total_video_entries')
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nStatistics saved to {output_file}")
        print("Note: 'total_videos' = unique videos across all platforms (deduplicated)")
        print("      'instagram_videos' = Instagram videos only (used for base rate calculation)")
        print("      'total_video_entries' = total video entries (including duplicates)")
        print("      'total_views' = SUM of views from ALL platforms (Instagram + TikTok + YouTube)")
        print("      Views from each platform are ADDED together for bonus calculation")
        
        # Additional insights
        print("\n" + "="*100)
        print("ADDITIONAL INSIGHTS")
        print("="*100)
        print(f"\nTotal creators with videos: {len(results)}")
        print(f"Total videos analyzed: {matched_videos}")
        print(f"Average videos per creator: {matched_videos / len(results):.1f}")
        
        print(f"\nTop 5 creators by total views:")
        for i, r in enumerate(results[:5], 1):
            print(f"  {i}. {r['creator_name']}: {r['total_views']:,} views ({r['total_videos']} videos)")
        
        print(f"\nTop 5 creators by average views:")
        top_avg = sorted(results, key=lambda x: x['avg_views'], reverse=True)[:5]
        for i, r in enumerate(top_avg, 1):
            print(f"  {i}. {r['creator_name']}: {r['avg_views']:,.0f} avg views ({r['total_videos']} videos)")
        
        print(f"\nTop 5 creators by engagement rate:")
        top_eng = sorted(results, key=lambda x: x['overall_engagement_rate'], reverse=True)[:5]
        for i, r in enumerate(top_eng, 1):
            print(f"  {i}. {r['creator_name']}: {r['overall_engagement_rate']:.4f} ({r['total_videos']} videos)")
    
    # Show unmatched summary
    if unmatched_usernames:
        print("\n" + "="*100)
        print("UNMATCHED VIDEOS SUMMARY")
        print("="*100)
        print(f"\nTop unmatched usernames:")
        sorted_unmatched = sorted(unmatched_usernames.items(), key=lambda x: x[1], reverse=True)
        for username, count in sorted_unmatched[:20]:
            print(f"  {username}: {count} videos")

if __name__ == "__main__":
    main()

