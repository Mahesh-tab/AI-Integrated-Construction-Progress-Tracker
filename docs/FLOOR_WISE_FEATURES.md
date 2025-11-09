# Floor-wise Progress Tracking - Feature Documentation

## 🎯 Overview

The application now includes comprehensive floor-wise progress tracking with enhanced visualizations, reports, and analytics across all modules.

---

## ✨ New Features Added

### 1. **Database Enhancements** (`database.py`)

#### New Database Functions:
- **`get_floor_wise_progress(site_id)`**
  - Returns: Floor name, update count, average progress %, latest phase, work types count
  - Parses floor-wise details from progress descriptions
  - Aggregates statistics per floor
  
- **`get_work_type_breakdown(site_id)`**
  - Returns: Work type name, total instances, completed count, in-progress count
  - Tracks all work types: Structural, Plumbing, Electrical, Waterproofing, Toilet Finishes, Lift Lobby Finishes, etc.
  - Provides completion statistics

#### Enhanced Sites Table:
```sql
num_basements INTEGER DEFAULT 0
num_floors INTEGER DEFAULT 10
has_roof INTEGER DEFAULT 1
```

---

### 2. **Engineer Dashboard Enhancements** (`engineer_page.py`)

#### Upload Progress Form:
- **Floor/Level Selection**: Dynamically generated based on site configuration
  - Shows only floors that exist for the selected building
  - Example: "Basement 2, Basement 1, Ground Floor, 1st Floor...10th Floor, Roof/Terrace, All Floors"
  
- **Floor-wise Progress Details Section**:
  - Floor/Level dropdown (dynamic)
  - Work Phase selector (Not Started, In Progress, Completed, Under Review, Rework Required)
  - Floor-specific progress slider (0-100%)
  
- **Work Type Checklist** (3 categories):
  - **Core Construction**: Structural Work, Masonry Work, Plastering
  - **MEP Works**: Plumbing Work, Electrical Work, HVAC Work
  - **Finishing Works**: Waterproofing, Toilet Finishes, Lift Lobby Finishes, Painting
  
- **Individual Work Status**: For each selected work type, track status (Started, 50%, 75%, Completed, Pending)

#### New Visualizations in Analytics Tab:

**6. Floor-wise Progress Analysis** (NEW)
- **Average Progress by Floor** (Bar Chart)
  - Shows average progress percentage per floor
  - Hover shows: Floor name, avg progress, number of updates
  - Color: #17a2b8 (teal/cyan)
  
- **Number of Updates by Floor** (Bar Chart)
  - Shows total updates submitted for each floor
  - Hover shows: Floor name, total updates, work types count
  - Color: #6f42c1 (purple)
  
- **Detailed Floor Status Table**:
  - Floor/Level
  - Total Updates
  - Average Progress %
  - Current Phase
  - Work Types Count

**7. Work Type Analysis** (NEW)
- **Work Type Status Distribution** (Stacked Bar Chart)
  - Green: Completed
  - Yellow: In Progress
  - Gray: Other/Pending
  - Shows status breakdown for each work type
  
- **Work Type Summary Table**:
  - Work Type name
  - Total Instances
  - Completed count
  - In Progress count
  - Completion Rate %

#### Enhanced Individual PDF Reports:
- **New Section: "FLOOR-WISE DETAILS"**
  - Floor/Level
  - Work Phase
  - Floor Progress %
  - Work Types Being Carried Out (with status)
- Positioned before "WORK DESCRIPTION" section
- Formatted with clear labels and bullet points

#### Enhanced Monthly Progress Reports:

**PDF Table Format**:
- Added columns:
  - **Floor**: Which floor the work is on
  - **Floor %**: Floor-specific progress
  - **Work Types**: List of work types being carried out (shows top 3 + count)
- Table shows: Date, Category, Engineer, Floor, Floor %, Prog%, Status, Work Types

**PDF Summary Sections** (Added at end):
1. **Floor-wise Progress Summary Table**:
   - Floor | Updates | Avg Progress | Latest Phase | Work Types
   
2. **Work Type Summary Table**:
   - Work Type | Total | Completed | In Progress | Completion %

**CSV Format**:
- Additional columns:
  - Floor
  - Floor Progress %
  - Work Phase
  - Work Types (complete list with status)
  - Description Summary
  - AI Report Summary

---

### 3. **Admin Dashboard Enhancements** (`admin_page.py`)

#### Add New Site Form:
- **Building Structure Details Section**:
  - Number of Basements (0-5)
  - Number of Floors (1-100)
  - Has Roof/Terrace (checkbox)
  - Floor Structure Preview before submission

#### Site Management View:
- **Building Structure Display**: Shows "2 Basement(s) + Ground Floor + 15 Floor(s) + Roof/Terrace"
- **Floor-wise Progress Overview Table** (NEW):
  - Appears in each site's expanded view
  - Shows: Floor | Avg Progress % | Latest Phase
  - Limited height for compact display

---

## 📊 Complete Visualization List

### Engineer Analytics Tab (8 Total):
1. ✅ Progress Timeline (Line Chart)
2. ✅ Work by Category (Pie Chart)
3. ✅ Verification Status (Bar Chart)
4. ✅ Monthly Activity & Progress (Dual-axis Chart)
5. ✅ Progress by Category (Grouped Bar Chart)
6. ✨ **Floor-wise Progress Analysis** (2 charts + table) - NEW
7. ✨ **Work Type Analysis** (Stacked Bar + table) - NEW
8. ✅ Download Monthly Reports (PDF/CSV)

### Admin Dashboard (2 Total):
1. ✅ Progress by Site (Bar Chart)
2. ✅ Sites by Status (Pie Chart)

---

## 🗂️ Data Storage Format

Floor-wise details are stored in the `description` field with special markers:

```
[Main description text]

--- FLOOR-WISE DETAILS ---
Floor: 3rd Floor
Work Phase: In Progress
Floor Progress: 65%

Work Types Being Carried Out:
  - Structural Work: Completed
  - Plumbing Work: 75% Complete
  - Electrical Work: Started
  - Toilet Finishes: Pending
```

---

## 🔄 Dynamic Floor Generation

Helper functions in `engineer_page.py`:
- **`get_ordinal_suffix(n)`**: Returns 'st', 'nd', 'rd', 'th'
- **`generate_floor_options(num_basements, num_floors, has_roof)`**:
  - Creates floor list: ["Basement 2", "Basement 1", "Ground Floor", "1st Floor", "2nd Floor", ..., "10th Floor", "Roof/Terrace", "All Floors"]
  - Automatically adjusts based on building configuration

---

## 📈 Data Flow

1. **Admin creates site** → Sets number of basements, floors, roof
2. **Engineer selects site** → Floor options dynamically generated
3. **Engineer uploads progress** → Selects floor, phase, progress %, work types
4. **Data stored** → Description includes floor-wise details section
5. **Analytics generated** → Database functions parse floor data
6. **Visualizations displayed** → Charts and tables show floor-wise breakdown
7. **Reports exported** → PDF/CSV include floor and work type details

---

## 🎨 Color Scheme

- **Floor Progress Chart**: #17a2b8 (Teal)
- **Floor Updates Chart**: #6f42c1 (Purple)
- **Work Type - Completed**: #28a745 (Green)
- **Work Type - In Progress**: #ffc107 (Yellow)
- **Work Type - Other**: #6c757d (Gray)

---

## 📋 Work Types Tracked

1. **Structural Work** - Columns, beams, slabs
2. **Masonry Work** - Block work, walls
3. **Plastering** - Wall and ceiling plastering
4. **Plumbing Work** - Water supply, drainage
5. **Electrical Work** - Wiring, conduits, fixtures
6. **HVAC Work** - AC ducts, vents
7. **Waterproofing** - Bathroom/terrace waterproofing
8. **Toilet Finishes** - Tiles, fixtures, fittings
9. **Lift Lobby Finishes** - Flooring, walls, ceiling
10. **Painting** - Wall painting, finishes

---

## 🚀 Usage Examples

### For Engineers:

1. **Upload Progress with Floor Details**:
   ```
   1. Select site
   2. Choose floor (e.g., "3rd Floor")
   3. Set work phase (e.g., "In Progress")
   4. Set floor progress (e.g., 65%)
   5. Check work types (Structural, Plumbing, Electrical)
   6. Set status for each work type
   7. Upload photos
   8. Submit
   ```

2. **View Analytics**:
   - Go to "Analytics & Visualizations" tab
   - Scroll to "Floor-wise Progress Analysis" section
   - View progress by floor, updates count, and status table
   - Check "Work Type Analysis" for completion rates

3. **Download Reports**:
   - Monthly reports now include floor-wise breakdown
   - Individual reports show floor details in dedicated section

### For Admins:

1. **Create Site with Floor Config**:
   ```
   1. Fill in site name, location
   2. Set basements: 2
   3. Set floors: 15
   4. Check "Has Roof/Terrace"
   5. Submit
   ```

2. **Monitor Progress**:
   - Site Management → Expand site
   - View floor-wise progress table
   - See which floors are active and their progress

---

## 🔍 Backward Compatibility

All code includes backward compatibility:
- Sites without floor config get defaults (0 basements, 10 floors, has roof)
- Progress entries without floor data show "N/A" in reports
- Visualizations gracefully handle missing data
- No data loss for existing entries

---

## 📊 Sample Report Output

### Monthly Report PDF - Floor Summary Table:
```
Floor           | Updates | Avg Progress | Latest Phase  | Work Types
----------------|---------|--------------|---------------|------------
Basement 1      | 3       | 85.0%        | Completed     | 4
Ground Floor    | 5       | 70.0%        | In Progress   | 6
1st Floor       | 4       | 65.0%        | In Progress   | 5
2nd Floor       | 2       | 45.0%        | Started       | 3
```

### Work Type Summary Table:
```
Work Type           | Total | Completed | In Progress | Completion %
--------------------|-------|-----------|-------------|-------------
Structural Work     | 12    | 8         | 3           | 66.7%
Plumbing Work       | 10    | 5         | 4           | 50.0%
Electrical Work     | 9     | 3         | 5           | 33.3%
Toilet Finishes     | 6     | 2         | 3           | 33.3%
```

---

## 🎯 Benefits

1. **Detailed Tracking**: Monitor progress at floor level, not just site level
2. **Work Type Visibility**: See which activities are in progress vs completed
3. **Better Planning**: Identify floors that need attention
4. **Resource Allocation**: Understand where teams are deployed
5. **Comprehensive Reports**: Floor-wise data in all exports
6. **Dynamic Configuration**: Each building has its own floor structure
7. **Visual Analytics**: 2 new chart types + 2 data tables
8. **Phase Tracking**: Know the current state of each floor

---

## 🛠️ Technical Notes

- Floor data parsed from description field (non-invasive approach)
- No database schema changes for progress table
- Parser handles missing/incomplete data gracefully
- CSV exports include all floor details for spreadsheet analysis
- PDF tables use dynamic row heights for text wrapping
- All visualizations use Plotly for interactivity

---

## 📝 Future Enhancements

- [ ] Floor-wise photo gallery
- [ ] Compare progress across floors side-by-side
- [ ] Floor-specific AI analysis
- [ ] Timeline view showing floor progression over time
- [ ] Critical path analysis for floor dependencies
- [ ] Mobile-responsive floor selection
- [ ] Edit site floor configuration after creation

---

## 🎉 Summary

The floor-wise progress tracking system adds **7 major features**:
1. Dynamic floor selection based on building structure
2. Floor-wise progress percentage tracking
3. Work type checklist with status
4. 2 new visualization types (4 charts total)
5. 2 new data tables
6. Enhanced PDF reports with floor sections
7. Comprehensive monthly reports with floor/work summaries

All features are backward compatible and production-ready! 🚀
