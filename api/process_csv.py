import json
import sys
import csv
from pathlib import Path
from io import StringIO

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from calculate_costs import (
    create_default_model, create_performance_model, create_optimized_cpm_model,
    create_minimum_base_model,
    calculate_all_creators, calculate_all_creators_performance
)
from creator_registry import create_registry, match_video_to_creator
from collections import defaultdict

def safe_int(value, default=0):
    """Safely convert value to int."""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def deduplicate_videos(videos_list):
    """Deduplicate videos based on caption, date, and duration."""
    import re
    from collections import defaultdict
    
    if not videos_list:
        return []
    
    def normalize_caption(caption):
        return re.sub(r'[^a-z0-9]', '', caption.lower())
    
    video_groups = defaultdict(list)
    for video in videos_list:
        caption = normalize_caption(video.get('caption', ''))
        published_date_str = video.get('publishedDate', '')
        date_key = published_date_str.split(' ')[0] if published_date_str else ''
        duration = safe_int(video.get('durationSeconds', 0))
        
        signature = (caption, date_key, duration)
        video_groups[signature].append(video)
    
    unique_videos = []
    seen_groups = set()
    for signature, group in video_groups.items():
        if signature not in seen_groups:
            seen_groups.add(signature)
            unique_videos.append(group[0])
    
    return unique_videos

def process_csv_to_statistics(csv_content):
    """Process CSV content and return creator statistics."""
    registry = create_registry()
    
    creator_stats = defaultdict(lambda: {
        'videos': [],
        'total_views': 0,
        'total_likes': 0,
        'total_comments': 0,
        'total_shares': 0,
        'platforms': set(),
    })
    
    # Parse CSV
    reader = csv.DictReader(StringIO(csv_content))
    
    for row in reader:
        video_url = row.get('videoUrl', '')
        account_username = row.get('accountUsername', '')
        account_display_name = row.get('accountDisplayName', '')
        
        creator = match_video_to_creator(
            registry,
            video_url=video_url,
            video_handle=account_username,
            video_author=account_display_name
        )
        
        if creator:
            creator_name = creator.name
            stats = creator_stats[creator_name]
            row_with_creator = row.copy()
            row_with_creator['creator_name'] = creator_name
            stats['videos'].append(row_with_creator)
            stats['total_views'] += safe_int(row.get('viewCount', 0))
            stats['total_likes'] += safe_int(row.get('likeCount', 0))
            stats['total_comments'] += safe_int(row.get('commentCount', 0))
            stats['total_shares'] += safe_int(row.get('shareCount', 0))
            stats['platforms'].add(row.get('platform', ''))
    
    # Convert to list format with deduplication
    creators_data = []
    creator_videos_dict = {}
    
    for creator_name, stats in creator_stats.items():
        videos = stats['videos']
        
        # Deduplicate videos
        unique_videos = deduplicate_videos(videos)
        instagram_videos = [v for v in unique_videos if v.get('platform', '').lower() == 'instagram']
        
        creators_data.append({
            'creator_name': creator_name,
            'instagram_videos': len(instagram_videos),
            'total_videos': len(unique_videos),
            'total_views': stats['total_views'],
            'avg_views': stats['total_views'] / len(unique_videos) if unique_videos else 0,
        })
        
        creator_videos_dict[creator_name] = unique_videos
    
    return creators_data, creator_videos_dict

def handler(request):
    """Vercel serverless function handler."""
    # Handle CORS preflight
    if request.get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    if request.get('method') != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Get CSV data from request body
        body = request.get('body', '')
        if isinstance(body, dict):
            csv_content = body.get('csv', '')
        elif isinstance(body, str):
            try:
                parsed = json.loads(body)
                csv_content = parsed.get('csv', body)
            except:
                csv_content = body
        else:
            csv_content = body.decode('utf-8') if isinstance(body, bytes) else str(body)
        
        if not csv_content:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No CSV data provided'})
            }
        
        # Process CSV
        creators_data, creator_videos_dict = process_csv_to_statistics(csv_content)
        
        if not creators_data:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No creators found in CSV'})
            }
        
        # Generate all model data
        model1 = create_default_model()
        financials1 = calculate_all_creators(model1, creators_data, follower_counts=None, period_type="signed")
        
        model3 = create_optimized_cpm_model()
        financials3 = calculate_all_creators(model3, creators_data, follower_counts=None, period_type="signed")
        
        model2 = create_performance_model()
        financials2 = calculate_all_creators_performance(model2, creator_videos_dict)
        
        model4 = create_minimum_base_model()
        financials4 = calculate_all_creators_performance(model4, creator_videos_dict)
        
        # Format results
        def format_model1_data(financials):
            total_base_cost = sum(f.total_base_cost for f in financials)
            total_bonus = sum(f.bonus for f in financials)
            total_cost = sum(f.total_cost for f in financials)
            total_instagram_videos = sum(f.instagram_videos for f in financials)
            total_views = sum(f.total_views for f in financials)
            
            return {
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
        
        def format_performance_data(financials, model_name):
            total_cost = sum(f.total_compensation for f in financials)
            total_videos = sum(f.total_videos for f in financials)
            total_qualified = sum(f.qualified_videos for f in financials)
            total_views = sum(f.total_views for f in financials)
            
            return {
                'model_name': model_name,
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
        
        result = {
            'model1': format_model1_data(financials1),
            'model2': format_performance_data(financials2, 'Model 2: Performance-Based Per Video'),
            'model3': format_model1_data(financials3),
            'model4': format_performance_data(financials4, 'Model 4: Lower Threshold Performance Model')
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': error_msg})
        }
