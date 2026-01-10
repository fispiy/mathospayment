# Model Calculation Process - Detailed Explanation

## Overview

This document explains how the payment models are calculated, including how videos are deduplicated across platforms, how creators are matched, and how bonuses are computed.

## Payment Model Structure

All models (A-F) follow the same structure:

### Base Payment
- **$30 per video** with **3,000+ views** (14-day sum)
- All videos meeting the 3k threshold receive the base payment
- Videos with less than 3,000 views receive $0 base

### Bonus Payment
- Based on **14-day sum of views** for each video
- Same bonus tiers for all models:
  - 10,000 – 49,999 views: $45
  - 50,000 – 99,999 views: $170
  - 100,000 – 499,999 views: $470
  - 500,000 – 1,999,999 views: $1,270
  - 2,000,000 – 4,999,999 views: $2,270
  - 5,000,000+ views: $2,970 (capped)

### Model Differences

The **only difference** between models is how bonuses are calculated:

- **Individual Models (A, C, E)**: Each video gets a bonus based on its own view count. Bonuses are calculated per video and then summed.
- **Summed Models (B, D, F)**: Total bonus is calculated based on the sum of all video views for each creator. A single bonus tier is applied to the total.

---

## Step-by-Step Process

### Step 1: Data Loading

#### December 2025 Data
- **Source**: `data/December Data - Sheet1.csv` (or `model1_data.json` as fallback)
- **Format**: CSV with columns: Date, Creator, Notes, Link, Platform, Date2, Views, Amount, Paid
- **Key**: Videos marked as "Paid" are the primary entries

#### January 2026 Data
- **Source**: `januaryinfo/videos_*.csv` (viral.app export format)
- **Format**: CSV with columns: platform, accountUsername, accountDisplayName, videoUrl, caption, publishedDate, viewCount, etc.
- **Key**: All videos from viral.app export

### Step 2: Creator Matching

Videos are matched to creators using the **Creator Registry** (`src/creator_registry.py`):

1. **Registry Structure**: Contains all creators with their social media accounts:
   - Contact account (Instagram/TikTok/YouTube)
   - Mathos Ins (Instagram handle)
   - Mathos TT (TikTok handle)
   - Mathos YT (YouTube handle)

2. **Matching Logic** (`match_video_to_creator`):
   - **By URL**: Extracts handles from video URLs and matches to registry
   - **By Handle**: Matches accountUsername to registry handles
   - **By Author Name**: Matches accountDisplayName to creator names
   - **Normalization**: Removes query parameters, normalizes handles (lowercase, removes @)

3. **New Creators**: Added from `januaryinfo/newcreators.txt`:
   - Braedon, Sasha, Eason, Nickolai, Sean, Brady, Rishab, Ethan, Zander
   - Each with their Instagram, TikTok, and YouTube accounts

### Step 3: Video Deduplication Across Platforms

**Critical Process**: The same video posted on multiple platforms (Instagram, TikTok, YouTube) is treated as **one unique video**.

#### Deduplication Logic

1. **Grouping Criteria**: Videos are grouped by:
   - **Same creator**
   - **Similar caption** (normalized: lowercase, whitespace collapsed)
   - **Same date** (within 1 day tolerance)
   - **Similar duration** (within 5 seconds tolerance)

2. **View Summing**: For each group of duplicate videos:
   - **Sum views** across all platforms
   - **Keep metadata** from the top-performing platform (highest views)
   - **Result**: One unique video entry with summed views

3. **Example**:
   ```
   Video posted on 3 platforms:
   - Instagram: 5,000 views
   - TikTok: 8,000 views  
   - YouTube: 2,000 views
   
   Result: 1 unique video with 15,000 total views
   ```

#### Implementation Details

**December Data** (`process_december_data.py`):
- Looks for "Paid" entries
- Checks following rows for same date/creator (non-paid entries = same video on different platform)
- Groups them together and sums views

**January Data** (`process_january_data.py`):
- Uses caption + date + duration as grouping key
- Groups videos with same signature
- Sums views and keeps top platform's metadata

### Step 4: Base Payment Calculation

For each creator's unique videos:

```python
BASE_RATE = 30.0
MIN_VIEWS_FOR_BASE = 3000

for each video:
    if video.views >= MIN_VIEWS_FOR_BASE:
        base_cost += BASE_RATE
        qualified_videos += 1
```

**Example**:
- Creator has 10 videos
- 7 videos have 3,000+ views
- Base cost = 7 × $30 = $210

### Step 5: Bonus Calculation

#### Model A, C, E: Individual Video Bonus

For each video individually:

```python
def calculate_bonus_for_views(views):
    if views < 10000:
        return 0.0
    elif views >= 5000000:
        return 2970.0
    elif views >= 2000000:
        return 2270.0
    elif views >= 500000:
        return 1270.0
    elif views >= 100000:
        return 470.0
    elif views >= 50000:
        return 170.0
    elif views >= 10000:
        return 45.0
```

**Example**:
- Video 1: 50,000 views → $170 bonus
- Video 2: 120,000 views → $470 bonus
- Video 3: 8,000 views → $0 bonus
- **Total bonus** = $170 + $470 + $0 = $640

#### Model B, D, F: Summed Video Bonus

For each creator, sum all video views first:

```python
creator_total_views = sum(video.views for all videos)
creator_bonus = calculate_bonus_for_views(creator_total_views)
```

**Example**:
- Video 1: 50,000 views
- Video 2: 120,000 views
- Video 3: 8,000 views
- **Total views** = 178,000
- **Total bonus** = $470 (single bonus for 100k-499k tier)

### Step 6: Total Cost Calculation

```python
total_cost = base_cost + bonus
```

**Example (Individual Model)**:
- Base: $210 (7 videos × $30)
- Bonus: $640 (individual video bonuses)
- **Total** = $850

**Example (Summed Model)**:
- Base: $210 (7 videos × $30)
- Bonus: $470 (summed view bonus)
- **Total** = $680

---

## Data Flow Diagram

```
Raw Data (CSV)
    ↓
[Step 1: Load & Parse]
    ↓
Video Entries (with platform, views, creator info)
    ↓
[Step 2: Match to Creators]
    ↓
Videos Grouped by Creator
    ↓
[Step 3: Deduplicate Across Platforms]
    ↓
Unique Videos (views summed across platforms)
    ↓
[Step 4: Calculate Base Payment]
    ↓
Base Cost ($30 per video with 3k+ views)
    ↓
[Step 5: Calculate Bonuses]
    ↓
Individual Model: Sum of per-video bonuses
OR
Summed Model: Single bonus based on total views
    ↓
[Step 6: Combine Base + Bonus]
    ↓
Final Cost per Creator
```

---

## Key Assumptions and Rules

### View Calculation
- **14-day sum**: Views are summed across all platforms after 14 days
- **Deduplication**: Same video on multiple platforms = one unique video
- **Highest performing platform**: Used for metadata (link, caption, date)

### Base Payment
- **Threshold**: 3,000 views minimum
- **Rate**: $30 per qualifying video
- **All-or-nothing**: Video either qualifies (3k+) or doesn't (<3k)

### Bonus Payment
- **Threshold**: 10,000 views minimum
- **Tier-based**: Highest applicable tier is used (not cumulative)
- **Capped**: Maximum $2,970 at 5M+ views

### Creator Matching
- **Priority**: URL matching > Handle matching > Name matching
- **Normalization**: Handles are lowercased, @ symbols removed
- **URL cleaning**: Query parameters removed for matching

---

## Example Calculation

### Creator: Sasha (January 2026)

**Step 1: Raw Data Loading**
- 24 video entries from viral.app export CSV
- Videos appear on Instagram, TikTok, and YouTube

**Step 2: Creator Matching**
- Videos matched to "Sasha" using:
  - Instagram handle: `mathwithsasha`
  - TikTok handle: `mathwithsasha`
  - YouTube handle: `mathwithsasha`
- All 24 videos successfully matched

**Step 3: Video Deduplication**
- Example: One video posted on 3 platforms:
  - Instagram: 45,000 views
  - TikTok: 120,000 views
  - YouTube: 35,000 views
  - **Result**: 1 unique video with 200,000 total views (summed)
- After deduplication: 24 unique videos
- Total views: 591,743 (summed across all platforms)

**Step 4: Base Calculation**
- Videos with 3,000+ views: 7 videos
- Base cost = 7 × $30 = **$210**

**Step 5a: Bonus Calculation (Model E - Individual)**
- Each video gets bonus based on its own views:
  - Video 1: 150,000 views → $470 (100k-499k tier)
  - Video 2: 80,000 views → $170 (50k-99k tier)
  - Video 3: 45,000 views → $45 (10k-49k tier)
  - Video 4: 200,000 views → $470 (100k-499k tier)
  - Video 5: 25,000 views → $45 (10k-49k tier)
  - Video 6: 60,000 views → $170 (50k-99k tier)
  - Video 7: 31,743 views → $45 (10k-49k tier)
  - Videos 8-24: < 10,000 views → $0 each
- **Total bonus** = $470 + $170 + $45 + $470 + $45 + $170 + $45 = **$1,415**

**Step 5b: Bonus Calculation (Model F - Summed)**
- Sum all video views: 591,743 total views
- Apply single bonus tier: 500k-1.99M → **$1,270**

**Step 6: Total Cost**

**Model E (Individual)**:
- Base: $210
- Bonus: $1,415
- **Total** = **$1,625**

**Model F (Summed)**:
- Base: $210
- Bonus: $1,270
- **Total** = **$1,480**

**Key Difference**: Model E rewards individual high-performing videos, while Model F rewards creators with high total view counts.

---

## Files and Functions

### Core Processing
- **`src/process_december_data.py`**: Processes December CSV, deduplicates videos
- **`src/process_january_data.py`**: Processes January viral.app CSV, deduplicates videos
- **`src/creator_registry.py`**: Creator matching and registry management

### Model Calculation
- **`src/simulate_new_bonus_models.py`**: Simulates models A-D (December + January projection)
- **`src/export_dashboard_data.py`**: Generates all model data files (A-F)

### Key Functions
- `calculate_bonus_for_views(views)`: Returns bonus amount for view count
- `deduplicate_videos(videos_list)`: Groups videos across platforms
- `match_video_to_creator()`: Matches video to creator in registry
- `process_january_data()`: Loads and processes January CSV
- `process_december_data()`: Loads and processes December CSV

---

## Model Data Files

All model data is saved as JSON files in `data/`:

- `new_model_a_data.json`: $30 Base + Individual Bonus (Dec 2025)
- `new_model_b_data.json`: $30 Base + Summed Bonus (Dec 2025)
- `new_model_c_data.json`: $30 Base + Individual Bonus (Jan 2026 Projection)
- `new_model_d_data.json`: $30 Base + Summed Bonus (Jan 2026 Projection)
- `new_model_e_data.json`: $30 Base + Individual Bonus (Jan 2026 Actual)
- `new_model_f_data.json`: $30 Base + Summed Bonus (Jan 2026 Actual)

Each file contains:
- Model name and totals (cost, base, bonus, videos, views)
- Per-creator breakdown with base, bonus, and total costs

---

## Verification

To verify calculations:

1. **Check base costs**: Should be (number of videos with 3k+ views) × $30
2. **Check bonuses**: Individual model should have higher total than summed model
3. **Check totals**: Base + Bonus = Total Cost
4. **Check views**: Should match sum of all unique video views (after deduplication)

---

## Detailed Deduplication Example

### How 3 Links Become 1 Video

**Scenario**: Creator posts the same video on Instagram, TikTok, and YouTube.

**Raw Data**:
```
Row 1: Instagram, "Learn calculus tips", 2026-01-10, 5,000 views
Row 2: TikTok, "Learn calculus tips", 2026-01-10, 8,000 views  
Row 3: YouTube, "Learn calculus tips", 2026-01-10, 2,000 views
```

**Deduplication Process**:

1. **Grouping**: All 3 rows have:
   - Same caption (normalized: "learn calculus tips")
   - Same date (2026-01-10)
   - Same duration (if available)
   - Same creator

2. **View Summing**: 
   - Total views = 5,000 + 8,000 + 2,000 = **15,000 views**

3. **Metadata Selection**:
   - Top platform: TikTok (8,000 views - highest)
   - Keep TikTok's link, caption, date

4. **Result**: 
   - **1 unique video** with 15,000 views
   - Platform: TikTok (representative)
   - Used for all calculations

**Why This Matters**:
- Without deduplication: 3 videos × $30 = $90 base
- With deduplication: 1 video × $30 = $30 base
- **Saves $60** and accurately reflects actual content created

---

## Notes

- **Unmatched videos**: Some videos may not match to creators (shown as warnings)
- **New creators**: Must be added to `creator_registry.py` to be included
- **Data freshness**: Models are regenerated when dashboard starts
- **Reproducibility**: Simulation uses random seed (42) for consistent projections
- **View accuracy**: Views are 14-day sums, already aggregated when loaded from CSV

