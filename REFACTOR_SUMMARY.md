# Refactor Summary: Code Cleanup and Improvements

**Branch:** `refactor/cleanup`
**Date:** January 31, 2026
**Purpose:** Reduce code duplication, improve performance, and add test coverage

---

## Overview

This refactor addresses several code quality issues identified in the codebase:
- Significant code duplication between files
- No caching for API calls
- Zero test coverage
- Monolithic file structure

**Net Result:** ~1,750 lines of duplicate code removed

---

## Changes Made

### 1. Created `shared.py` - Shared Utilities Module

Extracted common functions used by both `streamlit_app.py` and `coach_view.py`:

| Function | Description |
|----------|-------------|
| `connect_to_google_sheets()` | Authenticate with Google Sheets API |
| `load_data_from_google_sheets()` | Load training data (now cached) |
| `save_data_to_google_sheets()` | Save data to cloud |
| `append_row_to_google_sheets()` | Add single row |
| `clear_gsheets_cache()` | Invalidate cache after saves |
| `calculate_personal_records()` | Calculate PRs from data |
| `generate_executive_summary()` | AI insights summary |
| `generate_30day_change_summary()` | 30-day trend analysis |
| `analyze_training_data()` | Comprehensive analysis report |

**Also includes:**
- `COLUMN_MAPPING` - Column name mappings
- `GSHEETS_COLUMN_MAPPING` - Google Sheets specific mappings
- `NUMERIC_COLUMNS` - List of numeric column names
- `get_central_time()` - Timezone helper

---

### 2. Added Caching for Google Sheets

**Before:** Every page interaction made a fresh API call to Google Sheets.

**After:** Data is cached for 5 minutes using `@st.cache_data(ttl=300)`.

```python
@st.cache_data(ttl=300, show_spinner=False)
def _fetch_gsheets_data(sheet_url: str, readonly: bool = False):
    # Cached API call
    ...
```

**Benefits:**
- Faster page loads
- Fewer API calls (reduces rate limiting risk)
- Cache auto-clears after saving data

---

### 3. Removed Duplicate Code from `streamlit_app.py`

**Before:** 2,614 lines
**After:** 1,712 lines
**Removed:** 902 lines (35% reduction)

Deleted local copies of functions now imported from `shared.py`:
- `connect_to_google_sheets()` (lines 86-113)
- `load_data_from_google_sheets()` (lines 115-193)
- `save_data_to_google_sheets()` (lines 195-237)
- `append_row_to_google_sheets()` (lines 239-258)
- `generate_executive_summary()` (lines 599-713)
- `generate_30day_change_summary()` (lines 715-853)
- `analyze_training_data()` (lines 855-1030)
- Duplicate `COLUMN_MAPPING` dictionary
- Duplicate `GSHEETS_AVAILABLE` check

---

### 4. Refactored `coach_view.py`

**Before:** 963 lines with duplicated functions
**After:** ~114 lines importing from `shared.py`

The coach view now properly imports shared utilities instead of maintaining its own copies.

---

### 5. Added Unit Tests

Created `tests/` directory with comprehensive test coverage:

#### `tests/test_ocr_parsing.py`
- 25+ tests for OCR text extraction
- Tests for duration, speed, distance, turns, touches
- Edge cases: empty text, case insensitivity, missing data

#### `tests/test_calculations.py`
- 20+ tests for `calculate_personal_records()`
- Tests for PR detection, date tracking, foot determination
- Edge cases: null values, empty DataFrames, missing columns

#### `tests/conftest.py`
- Pytest fixtures for sample data
- Reusable test DataFrames

#### `tests/requirements-test.txt`
- pytest>=7.0.0
- pytest-cov>=4.0.0

---

### 6. Created Reusable UI Components

Created `tabs/components.py` with reusable patterns:

| Component | Description |
|-----------|-------------|
| `coach_filter()` | Dropdown to filter by coach |
| `time_filter()` | Radio buttons for time period |
| `create_line_chart()` | Standardized chart creation |
| `display_metric_with_best()` | Metric with average and best |
| `display_time_range_info()` | Date range caption |

---

### 7. Split Tabs into Individual Modules

Extracted each tab's code into its own module in `tabs/`:

| Module | Description |
|--------|-------------|
| `tabs/dashboard.py` | Training Dashboard with KPIs and trends |
| `tabs/upload.py` | Upload & Extract with OCR and data entry |
| `tabs/ai_insights.py` | AI-powered analysis reports |
| `tabs/analytics.py` | Charts and analytics |
| `tabs/speed.py` | Speed metrics analysis |
| `tabs/agility.py` | Agility metrics analysis |
| `tabs/ball_work.py` | Ball work and foot balance |
| `tabs/match_play.py` | Match performance tracking |
| `tabs/personal_records.py` | Personal records display |

**Line count reductions:**
- `streamlit_app.py`: 1,713 → 557 lines (67% reduction)
- `coach_view.py`: 963 → 161 lines (83% reduction)

Both apps now share the same tab modules, eliminating code duplication.

---

### 8. Fixed df.iterrows() Performance

Replaced two slow `df.iterrows()` loops in `shared.py` with vectorized pandas operations:

**Before (lines 327, 770):**
```python
for idx, row in df.iterrows():
    left = pd.to_numeric(row.get('left_touches'), errors='coerce')
    right = pd.to_numeric(row.get('right_touches'), errors='coerce')
    if pd.notna(left) and pd.notna(right) and left > 0 and right > 0:
        ratio = left / right
        ...
```

**After:**
```python
left = pd.to_numeric(df['left_touches'], errors='coerce')
right = pd.to_numeric(df['right_touches'], errors='coerce')
valid_mask = (left > 0) & (right > 0) & pd.notna(left) & pd.notna(right)
if valid_mask.any():
    ratios = left[valid_mask] / right[valid_mask]
    distances = (ratios - 0.5).abs()
    best_idx = distances.idxmin()
    ...
```

---

## File Structure After Refactor

```
cityplaysensorapp/
├── streamlit_app.py      # Main app (557 lines, was 2,614)
├── coach_view.py         # Coach view (161 lines, was 963)
├── shared.py             # Shared utilities (984 lines)
├── tabs/
│   ├── __init__.py       # Package init with exports
│   ├── components.py     # Reusable UI components
│   ├── dashboard.py      # Dashboard tab
│   ├── upload.py         # Upload & Extract tab
│   ├── ai_insights.py    # AI Insights tab
│   ├── analytics.py      # Analytics tab
│   ├── speed.py          # Speed tab
│   ├── agility.py        # Agility tab
│   ├── ball_work.py      # Ball Work tab
│   ├── match_play.py     # Match Play tab
│   └── personal_records.py # Personal Records tab
├── tests/
│   ├── __init__.py       # Package init
│   ├── conftest.py       # Test fixtures
│   ├── test_ocr_parsing.py    # OCR tests (51 total tests)
│   ├── test_calculations.py   # Calculation tests
│   └── requirements-test.txt  # Test dependencies
├── .github/
│   └── workflows/
│       └── test.yml      # GitHub Actions CI
├── requirements.txt      # Unchanged
├── packages.txt          # Unchanged
└── README.md             # Unchanged
```

---

## Testing Checklist

Before merging to `main`, verify:

- [ ] App loads without errors
- [ ] Dashboard displays correctly
- [ ] Google Sheets data loads (check caching works)
- [ ] Upload & Extract tab functions
- [ ] OCR extracts data from screenshots
- [ ] Manual data entry works
- [ ] Data saves to Google Sheets
- [ ] All analytics tabs render charts
- [ ] Personal Records tab shows PRs
- [ ] AI Insights generates report
- [ ] Coach view loads and displays data

---

## How to Deploy for Testing

1. Go to https://share.streamlit.io
2. Create new app
3. Select repository: `weljim73-spec/cityplaysensorapp`
4. Select branch: `refactor/cleanup`
5. Main file: `streamlit_app.py`
6. Add secrets (same as main app)
7. Deploy and test

---

## How to Merge to Main

Once testing is complete:

```bash
git checkout main
git merge refactor/cleanup
git push origin main
```

Or create a Pull Request on GitHub for review.

---

## Rollback

If issues are found after merging:

```bash
git checkout main
git revert HEAD
git push origin main
```

Or reset to previous commit:

```bash
git log --oneline  # Find previous commit hash
git reset --hard <commit-hash>
git push --force origin main
```
