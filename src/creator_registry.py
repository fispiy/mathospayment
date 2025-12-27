"""
Creator data structure for grouping creators by their social media links and handles.
This will be used to match videos from viral.app spreadsheet to creators.
"""

import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class CreatorAccount:
    """Represents a single social media account for a creator."""
    account_type: str  # e.g., "Contact account", "Mathos Ins", "Mathos TT", "Mathos YT"
    handle: str
    url: str


@dataclass
class Creator:
    """Represents a creator with all their social media accounts."""
    name: str
    accounts: List[CreatorAccount] = field(default_factory=list)
    
    def get_all_urls(self) -> Set[str]:
        """Get all URLs associated with this creator."""
        return {acc.url for acc in self.accounts if acc.url and acc.url.strip()}
    
    def get_all_handles(self) -> Set[str]:
        """Get all handles associated with this creator."""
        return {acc.handle for acc in self.accounts if acc.handle and acc.handle.strip()}
    
    def get_urls_by_platform(self) -> Dict[str, List[str]]:
        """Get URLs grouped by platform (instagram, tiktok, youtube)."""
        platform_urls = {
            'instagram': [],
            'tiktok': [],
            'youtube': []
        }
        for acc in self.accounts:
            if not acc.url or not acc.url.strip():
                continue
            url_lower = acc.url.lower()
            if 'instagram.com' in url_lower:
                platform_urls['instagram'].append(acc.url)
            elif 'tiktok.com' in url_lower:
                platform_urls['tiktok'].append(acc.url)
            elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                platform_urls['youtube'].append(acc.url)
        return platform_urls


class CreatorRegistry:
    """Registry that maps URLs and handles to creators for easy lookup."""
    
    def __init__(self):
        self.creators: List[Creator] = []
        self.url_to_creator: Dict[str, Creator] = {}
        self.handle_to_creator: Dict[str, Creator] = {}
        self.name_to_creator: Dict[str, Creator] = {}
    
    def add_creator(self, creator: Creator):
        """Add a creator to the registry and build lookup maps."""
        import re
        
        self.creators.append(creator)
        self.name_to_creator[creator.name.lower()] = creator
        
        # Map all URLs to creator
        for url in creator.get_all_urls():
            if url and url.strip():
                # Normalize URL for matching
                normalized = self._normalize_url(url)
                self.url_to_creator[normalized] = creator
                # Also store original URL
                self.url_to_creator[url] = creator
                
                # Extract handles from URLs and add to handle mapping
                # TikTok: tiktok.com/@username
                tiktok_match = re.search(r'tiktok\.com/@([^/?]+)', url, re.IGNORECASE)
                if tiktok_match:
                    handle = tiktok_match.group(1)
                    normalized_handle = handle.lower().strip().lstrip('@')
                    self.handle_to_creator[normalized_handle] = creator
                
                # Instagram: instagram.com/username or instagram.com/reel/...
                instagram_match = re.search(r'instagram\.com/(?:reel/|)([^/?]+)', url, re.IGNORECASE)
                if instagram_match:
                    handle = instagram_match.group(1)
                    # Skip if it's a video ID (usually short alphanumeric)
                    if len(handle) > 5 and not handle.startswith('p/'):
                        normalized_handle = handle.lower().strip().lstrip('@')
                        self.handle_to_creator[normalized_handle] = creator
                
                # YouTube: youtube.com/@username
                youtube_match = re.search(r'youtube\.com/@([^/?]+)', url, re.IGNORECASE)
                if youtube_match:
                    handle = youtube_match.group(1)
                    normalized_handle = handle.lower().strip().lstrip('@')
                    self.handle_to_creator[normalized_handle] = creator
        
        # Map all handles to creator
        for handle in creator.get_all_handles():
            if handle and handle.strip():
                normalized_handle = handle.lower().strip().lstrip('@')
                self.handle_to_creator[normalized_handle] = creator
    
    def find_creator_by_url(self, url: str) -> Optional[Creator]:
        """Find creator by URL (tries normalized and original)."""
        if not url or not url.strip():
            return None
        
        # Try original URL first
        if url in self.url_to_creator:
            return self.url_to_creator[url]
        
        # Try normalized URL
        normalized = self._normalize_url(url)
        return self.url_to_creator.get(normalized)
    
    def find_creator_by_handle(self, handle: str) -> Optional[Creator]:
        """Find creator by handle."""
        if not handle or not handle.strip():
            return None
        
        normalized = handle.lower().strip().lstrip('@')
        return self.handle_to_creator.get(normalized)
    
    def find_creator_by_name(self, name: str) -> Optional[Creator]:
        """Find creator by name."""
        if not name or not name.strip():
            return None
        
        return self.name_to_creator.get(name.lower().strip())
    
    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL for better matching (remove query params, trailing slashes, etc.)."""
        url = url.strip()
        # Remove common query parameters that don't affect identity
        url = re.sub(r'[?&](igsh|utm_source|_r|_t|is_from_webapp|sender_device)=[^&]*', '', url)
        url = re.sub(r'[?&]$', '', url)  # Remove trailing ? or &
        url = url.rstrip('/')
        return url.lower()
    
    def get_all_creators(self) -> List[Creator]:
        """Get all creators in the registry."""
        return self.creators


def parse_creator_data(data_text: str) -> CreatorRegistry:
    """
    Parse the creator data from the provided text format.
    Expected format: Creator name on first line, then account entries with tabs.
    Account entries: tab, account_type, handle, URL
    """
    registry = CreatorRegistry()
    lines = data_text.strip().split('\n')
    
    current_creator = None
    account_types = ['Contact account', 'Mathos Ins', 'Mathos TT', 'Mathos YT']
    
    for line in lines:
        # Check if line starts with tab (account entry) or not (creator name)
        if line.startswith('\t'):
            # This is an account entry
            parts = line.split('\t')
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) >= 1:
                account_type = parts[0]
                handle = parts[1] if len(parts) > 1 else ''
                url = parts[2] if len(parts) > 2 else ''
                
                # Handle cases where URL might be in handle position if handle is missing
                if not url and handle.startswith('http'):
                    url = handle
                    handle = ''
                
                if current_creator and account_type in account_types:
                    account = CreatorAccount(
                        account_type=account_type,
                        handle=handle,
                        url=url
                    )
                    current_creator.accounts.append(account)
        else:
            # This might be a creator name line
            parts = line.split('\t')
            parts = [p.strip() for p in parts if p.strip()]
            
            if parts:
                creator_name = parts[0]
                # Check if it's actually a creator name (not an account type or URL)
                if creator_name and creator_name not in account_types and not creator_name.startswith('http'):
                    # Save previous creator if exists
                    if current_creator:
                        registry.add_creator(current_creator)
                    
                    # Start new creator
                    current_creator = Creator(name=creator_name, accounts=[])
                    
                    # Check if there are account details on the same line
                    if len(parts) >= 2:
                        account_type = parts[1] if parts[1] in account_types else None
                        if account_type:
                            handle = parts[2] if len(parts) > 2 else ''
                            url = parts[3] if len(parts) > 3 else ''
                            
                            if not url and handle.startswith('http'):
                                url = handle
                                handle = ''
                            
                            account = CreatorAccount(
                                account_type=account_type,
                                handle=handle,
                                url=url
                            )
                            current_creator.accounts.append(account)
    
    # Don't forget the last creator
    if current_creator:
        registry.add_creator(current_creator)
    
    return registry


# Creator data as provided
CREATOR_DATA = """John Sellers	Contact account	johnstudiesnothing	https://www.instagram.com/johnstudiesnothing?igsh=MWxyZnF0dzdkdGR3cQ==
	Mathos Ins	integratingjohn	https://www.instagram.com/integratingjohn?igsh=MTFsNTIxOHI2aWFoaQ==
	Mathos TT	integratingjohn	https://www.tiktok.com/@integratingjohn?_r=1&_t=ZT-91flCcXwrHS
	Mathos YT	JNS426	https://www.youtube.com/@JNS426/shorts
			
Ivan	Contact account	i_vvlas	https://www.instagram.com/i_vvlas/
	Mathos Ins	study.motivat10n	https://www.instagram.com/study.motivat10n/
	Mathos TT	study.motivat10n	https://www.tiktok.com/@study.motivat10n
			
Thanush	Contact account	mathwiththanush	https://www.tiktok.com/@mathwiththanush?_r=1&_t=ZS-91atRokp6Zs
	Mathos Ins	mathwiththanush	https://www.instagram.com/mathwiththanush?igsh=MXR0cTQ5eWFzOXAxNA%3D%3D&utm_source=qr
	Mathos TT	mathwiththanush	https://www.tiktok.com/@mathwiththanush?_r=1&_t=ZS-91atRokp6Zs
			
Kevin Rhee	Contact account	flowstatekevin	https://www.instagram.com/flowstatekevin/
	Mathos Ins	kevdoesmath	https://www.instagram.com/kevdoesmath?igsh=ZDg3NnB1ZTIxbnM5&utm_source=qr
	Mathos TT	kevdoesmath	https://www.tiktok.com/@kevindoesmath?_r=1&_t=ZP-91g5PeUsehb
			
Nevin+	Contact account	@nbmath	https://www.tiktok.com/@nbincorporated?_r=1&_t=ZN-91UtxDqwTVG
	Mathos Ins	Needs to confirm	https://www.tiktok.com/@nbmath?_r=1&_t=ZN-91x5GftZWzO
	Mathos TT	@nbmath	https://www.tiktok.com/@nbmath?_r=1&_t=ZN-91x5GftZWzO
			
Huzaifa 	Contact account	lifebyuzi	https://www.tiktok.com/@lifebyuzi
	Mathos Ins	lifebyuzi	https://www.instagram.com/life.byuzi
	Mathos TT	lifebyuzi	https://www.tiktok.com/@lifebyuzi
			
Jasper	Contact account	studywithjamen	https://www.instagram.com/studywithjamen/
	Mathos Ins	studywithjamen	https://www.instagram.com/studywithjamen/
	Mathos TT	studywithjamen	https://www.tiktok.com/@studywithjamen
	Mathos YT		https://www.youtube.com/@studiosjamen
			
Arnab*	Contact account	exponential_arnab	https://www.instagram.com/exponential_arnab?igsh=MXExZTV2a25uczVyYg%3D%3D
	Mathos Ins	exponential_arnab	https://www.instagram.com/exponential_arnab?igsh=MXExZTV2a25uczVyYg%3D%3D
	Mathos TT	exponential_arnab	https://www.tiktok.com/@exponential_arnab
			
Yunski	Contact account	yunskistudy	https://www.instagram.com/yunskistudy
	Mathos Ins	math.maxxer	https://www.instagram.com/math.maxxer/
	Mathos TT	math.maxxer	https://www.tiktok.com/@math.maxxer
			
Adam	Contact account	mathwadam	https://www.tiktok.com/@mathwadam?_r=1&_t=ZP-91ihWswsBLi
	Mathos Ins	mathwadam	https://www.instagram.com/mathwadam?igsh=enZkNWg5YnhmaWNt&utm_source=qr
	Mathos TT	mathwadam	https://www.tiktok.com/@mathwadam?_r=1&_t=ZP-91ihWswsBLi
			
Yaz+	Contact account	amin_yaz_	https://www.tiktok.com/@studyhacksyaz_?is_from_webapp=1&sender_device=pc
	Mathos Ins	mathos.yazzz	https://www.instagram.com/mathos_.yazz__?igsh=MjdmdnhvcHBiN2dy&utm_source=qr
	Mathos TT	mathos.yazzz	https://www.tiktok.com/@mathos.yazzz?_r=1&_t=ZS-91i8mgoEd4H
			
Matt*	Contact account	Discord	
	Mathos Ins	kongsolvesmath	https://www.instagram.com/kongsolvesmath?igsh=bnB6dDl3cWJ2Z2Yy&utm_source=qr
	Mathos TT	kongsolvesmath	https://www.tiktok.com/@kongsolvesmath?_r=1&_t=ZT-91o0D18jmwA
	Mathos YT	kongsolvesmath	https://youtube.com/@kongsolvesmath?si=CcB4yA42oTmc-Oze
			
Jill	Contact account	jillhackslife	https://www.instagram.com/jillhackslife?igsh=NzcxNDliMmNpZ3Ft
	Mathos Ins	calwithjill	https://www.instagram.com/calwithjill?igsh=cTBtcHVvcHE4b3Ni&utm_source=qr
	Mathos TT	calwithjill	https://www.tiktok.com/@calwithjill
			
Ann	Contact account	essayswithann	https://www.tiktok.com/@essayswithann
	Mathos Ins	annsolves	
	Mathos TT	annsolves	https://www.tiktok.com/@annsolves
			
Kiru*	Contact account	cheatingwithkiru	https://www.instagram.com/cheatingwithkiru?
	Mathos Ins	waiting	https://www.instagram.com/kirudoesmath?igsh=MTlhYm53M3hjMnowaQ%3D%3D&utm_source=qr
	Mathos TT	waiting	https://www.tiktok.com/@learnwithkiru?_r=1&_t=ZN-91rmZNGYzLy
			
Daniel+	Contact account	LinkedIn	https://www.linkedin.com/in/danielyun27/
	Mathos Ins	danielmathmaxxing	https://www.instagram.com/danielmathmaxxing?igsh=d2k3bTN1cms3OG96
	Mathos TT	danielmathmaxxing	https://www.instagram.com/danielmathmaxxing?igsh=NTc4MTIwNjQ2YQ%3D%3D&utm_source=qr
	Mathos YT	danielmathmaxxing	https://www.youtube.com/@danielmathmaxxing
			
Dre	Contact account	UGC Page	UGC Page
	Mathos Ins	@nadraknows	https://www.instagram.com/nadraknows?igsh=MTJhZnhibW1iZnd6Yw==
	Mathos TT	@nadraknows	https://www.tiktok.com/@nadraknows?_r=1&_t=ZT-91vnsHC0K4c
	Mathos YT	@nadraknows	https://m.youtube.com/@nadraknows
			
Allen	Contact account	UGC Page	https://www.instagram.com/heysoliate/
	Mathos Ins	studymathosap	https://www.instagram.com/studymathosap/
	Mathos TT	studymathosap	https://www.tiktok.com/@studymathosap
			
Peter	Contact account	LinkTree	https://linktr.ee/peter.drykin 
	Mathos Ins		https://www.instagram.com/peter.counts?igsh=MWVmbDc3bGRnYmE5ZQ%3D%3D&utm_source=qr
	Mathos TT		https://www.tiktok.com/@peter.counts?_r=1&_t=ZG-92FjIlIMCQL
	Mathos YT		https://youtube.com/@peter.counts?si=6c-AEpDKz9eK78H_
			
JP	Contact account	Google Form	
	Mathos Ins	@productivitywithjp	https://www.instagram.com/productivitywithjp?igsh=eHJremY5bnMwMWpp&utm_source=qr
	Mathos TT	@productivitywithjp	https://www.tiktok.com/@productivitywithj?_r=1&_t=ZS-922Hs7BG6lz
	Mathos YT		
			
Riley	Contact account	Google Form	
	Mathos Ins	@rileyhatesmaths	https://www.instagram.com/rileyhatesmaths/
	Mathos TT	@rileyhatesmaths	https://www.tiktok.com/@rileyhatesmaths2
	Mathos YT	@rileyhatesmaths	https://youtube.com/@rileyhatesmaths?si=gts-0WmNZF2KtStt 
			
Andrew	Contact account	Google Form	https://www.instagram.com/ugc_andrewowusu/
	Mathos Ins		https://www.instagram.com/andrewstudies30?igsh=cTdsbXIwdnF3ZTBr&utm_source=qr
	Mathos TT		https://www.tiktok.com/@andrew.owusus_studies?_r=1&_t=ZT-92N8Czg57Cn
			
Gustavo	Contact account	Instagram	
	Mathos Ins		https://www.instagram.com/gustavosstudycorner?igsh=MXRsNWtvaHBzZHlyaQ%3D%3D&utm_source=qr
	Mathos TT		https://www.tiktok.com/@gustavo88138?_r=1&_t=ZS-92GQDD02rNI
	Mathos YT		
			
Liza	Contact account	Instagram	https://www.instagram.com/lizzflows?igsh=MjZ4ZnhvM2VyM24=
	Mathos Ins		
	Mathos TT		
	Mathos YT		
			
Salvador	Contact account	Instagram	https://www.instagram.com/joshuajsalvador?igsh=NTc4MTIwNjQ2YQ=="""


def create_registry() -> CreatorRegistry:
    """Create and populate the creator registry with the provided data."""
    registry = parse_creator_data(CREATOR_DATA)
    return registry


def match_video_to_creator(registry: CreatorRegistry, video_url: str = None, 
                           video_handle: str = None, video_author: str = None) -> Optional[Creator]:
    """
    Match a video from viral.app to a creator.
    Can match by URL, handle, or author name.
    
    Args:
        registry: The creator registry
        video_url: URL from the video (e.g., profile URL, video URL)
        video_handle: Handle/username from the video
        video_author: Author name from the video
    
    Returns:
        Creator if matched, None otherwise
    """
    import re
    
    # Try URL first (most reliable)
    if video_url:
        creator = registry.find_creator_by_url(video_url)
        if creator:
            return creator
        
        # Extract handle from video URL (e.g., tiktok.com/@username or instagram.com/username)
        # Try to extract @username from TikTok URLs
        tiktok_match = re.search(r'tiktok\.com/@([^/?]+)', video_url)
        if tiktok_match:
            handle = tiktok_match.group(1)
            creator = registry.find_creator_by_handle(handle)
            if creator:
                return creator
        
        # Try to extract username from Instagram URLs (reel/ or /)
        instagram_match = re.search(r'instagram\.com/(?:reel/|)([^/?]+)', video_url)
        if instagram_match:
            handle = instagram_match.group(1)
            creator = registry.find_creator_by_handle(handle)
            if creator:
                return creator
        
        # Try YouTube URLs
        youtube_match = re.search(r'youtube\.com/@([^/?]+)', video_url)
        if youtube_match:
            handle = youtube_match.group(1)
            creator = registry.find_creator_by_handle(handle)
            if creator:
                return creator
    
    # Try handle with variations
    if video_handle:
        # Try exact match first
        creator = registry.find_creator_by_handle(video_handle)
        if creator:
            return creator
        
        # Try variations (remove/add common suffixes/prefixes)
        handle_variations = [
            video_handle,
            video_handle.rstrip('1234567890'),  # Remove trailing numbers
            video_handle.replace('_', '').replace('.', ''),  # Remove separators
        ]
        
        # Also try adding/removing common prefixes
        if not video_handle.startswith('@'):
            handle_variations.append('@' + video_handle)
        else:
            handle_variations.append(video_handle.lstrip('@'))
        
        for variant in handle_variations:
            creator = registry.find_creator_by_handle(variant)
            if creator:
                return creator
        
        # Try partial matching - check if handle is contained in any creator's handles
        normalized_handle = video_handle.lower().strip().lstrip('@')
        for creator in registry.get_all_creators():
            for acc in creator.accounts:
                if acc.handle:
                    normalized_acc_handle = acc.handle.lower().strip().lstrip('@')
                    # Check if one contains the other (for variations like productivitywithj vs productivitywithjp)
                    if normalized_handle in normalized_acc_handle or normalized_acc_handle in normalized_handle:
                        if len(normalized_handle) >= 5 and len(normalized_acc_handle) >= 5:  # Only if both are substantial
                            return creator
    
    # Try author name
    if video_author:
        creator = registry.find_creator_by_name(video_author)
        if creator:
            return creator
    
    return None


def analyze_videos_dataframe(registry: CreatorRegistry, df, 
                            url_column: str = None, handle_column: str = None, 
                            author_column: str = None):
    """
    Analyze a pandas DataFrame of videos and match them to creators.
    
    Args:
        registry: The creator registry
        df: pandas DataFrame with video data
        url_column: Column name containing video/profile URLs
        handle_column: Column name containing handles/usernames
        author_column: Column name containing author names
    
    Returns:
        DataFrame with added 'creator_name' column
    """
    import pandas as pd
    
    # Try to auto-detect columns if not specified
    if not url_column:
        possible_url_cols = ['url', 'profile_url', 'author_url', 'link', 'video_url', 'creator_url']
        url_column = next((col for col in possible_url_cols if col in df.columns), None)
    
    if not handle_column:
        possible_handle_cols = ['handle', 'username', 'author_handle', 'creator_handle', '@handle']
        handle_column = next((col for col in possible_handle_cols if col in df.columns), None)
    
    if not author_column:
        possible_author_cols = ['author', 'creator', 'author_name', 'creator_name', 'name']
        author_column = next((col for col in possible_author_cols if col in df.columns), None)
    
    # Match each video to a creator
    creator_names = []
    for idx, row in df.iterrows():
        video_url = row[url_column] if url_column and url_column in df.columns else None
        video_handle = row[handle_column] if handle_column and handle_column in df.columns else None
        video_author = row[author_column] if author_column and author_column in df.columns else None
        
        creator = match_video_to_creator(registry, video_url, video_handle, video_author)
        creator_names.append(creator.name if creator else None)
    
    df_result = df.copy()
    df_result['creator_name'] = creator_names
    
    return df_result


def load_viral_app_data(file_path: str) -> 'pd.DataFrame':
    """
    Load viral.app spreadsheet data.
    Supports CSV and Excel files.
    
    Args:
        file_path: Path to the spreadsheet file
    
    Returns:
        pandas DataFrame
    """
    import pandas as pd
    import os
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.csv':
        return pd.read_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Use CSV or Excel files.")


def generate_creator_statistics(df_with_creators: 'pd.DataFrame') -> 'pd.DataFrame':
    """
    Generate statistics for each creator from the matched video data.
    
    Args:
        df_with_creators: DataFrame with 'creator_name' column added
    
    Returns:
        DataFrame with statistics per creator
    """
    import pandas as pd
    import numpy as np
    
    # Filter out rows without a matched creator
    df_matched = df_with_creators[df_with_creators['creator_name'].notna()].copy()
    
    if len(df_matched) == 0:
        return pd.DataFrame()
    
    # Group by creator and calculate statistics
    stats = []
    
    for creator_name in df_matched['creator_name'].unique():
        creator_df = df_matched[df_matched['creator_name'] == creator_name]
        
        # Convert numeric columns, handling any non-numeric values
        numeric_cols = ['viewCount', 'likeCount', 'commentCount', 'shareCount', 
                       'bookmarkCount', 'engagementRate', 'viralityFactor', 'durationSeconds']
        
        for col in numeric_cols:
            if col in creator_df.columns:
                creator_df[col] = pd.to_numeric(creator_df[col], errors='coerce')
        
        stat = {
            'creator_name': creator_name,
            'total_videos': len(creator_df),
            'platforms': ', '.join(creator_df['platform'].unique()) if 'platform' in creator_df.columns else '',
            'total_views': creator_df['viewCount'].sum() if 'viewCount' in creator_df.columns else 0,
            'total_likes': creator_df['likeCount'].sum() if 'likeCount' in creator_df.columns else 0,
            'total_comments': creator_df['commentCount'].sum() if 'commentCount' in creator_df.columns else 0,
            'total_shares': creator_df['shareCount'].sum() if 'shareCount' in creator_df.columns else 0,
            'avg_views': creator_df['viewCount'].mean() if 'viewCount' in creator_df.columns else 0,
            'avg_likes': creator_df['likeCount'].mean() if 'likeCount' in creator_df.columns else 0,
            'avg_comments': creator_df['commentCount'].mean() if 'commentCount' in creator_df.columns else 0,
            'max_views': creator_df['viewCount'].max() if 'viewCount' in creator_df.columns else 0,
            'max_likes': creator_df['likeCount'].max() if 'likeCount' in creator_df.columns else 0,
            'avg_engagement_rate': creator_df['engagementRate'].mean() if 'engagementRate' in creator_df.columns else 0,
            'avg_virality_factor': creator_df['viralityFactor'].mean() if 'viralityFactor' in creator_df.columns else 0,
            'avg_duration_seconds': creator_df['durationSeconds'].mean() if 'durationSeconds' in creator_df.columns else 0,
        }
        
        # Calculate engagement metrics
        if stat['total_views'] > 0:
            stat['overall_engagement_rate'] = (stat['total_likes'] + stat['total_comments'] + stat['total_shares']) / stat['total_views']
        else:
            stat['overall_engagement_rate'] = 0
        
        stats.append(stat)
    
    stats_df = pd.DataFrame(stats)
    
    # Sort by total views descending
    if 'total_views' in stats_df.columns:
        stats_df = stats_df.sort_values('total_views', ascending=False)
    
    return stats_df


if __name__ == "__main__":
    # Example usage
    registry = create_registry()
    
    print(f"Loaded {len(registry.get_all_creators())} creators")
    print("\n" + "="*80)
    
    # Show all creators and their links
    for creator in registry.get_all_creators():
        print(f"\n{creator.name}:")
        for acc in creator.accounts:
            if acc.url:
                print(f"  {acc.account_type}: {acc.handle} -> {acc.url}")
    
    print("\n" + "="*80)
    print("\nTesting URL lookup:")
    test_url = "https://www.instagram.com/integratingjohn?igsh=MTFsNTIxOHI2aWFoaQ=="
    creator = registry.find_creator_by_url(test_url)
    if creator:
        print(f"Found creator: {creator.name} for URL: {test_url}")
    
    print("\nTesting handle lookup:")
    test_handle = "integratingjohn"
    creator = registry.find_creator_by_handle(test_handle)
    if creator:
        print(f"Found creator: {creator.name} for handle: {test_handle}")

