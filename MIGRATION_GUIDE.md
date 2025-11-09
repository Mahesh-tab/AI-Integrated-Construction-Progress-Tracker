# Database Migration Guide - Floor Configuration Update

## What Changed?

The `sites` table in the database has been updated to include floor configuration:

### Old Schema (6 columns):
```
id, name, location, description, start_date, status
```

### New Schema (9 columns):
```
id, name, location, description, start_date, status, num_basements, num_floors, has_roof
```

## New Columns:
- **num_basements** (INTEGER, default: 0) - Number of basement levels (0-5)
- **num_floors** (INTEGER, default: 10) - Number of floors above ground (1-100)
- **has_roof** (INTEGER, default: 1) - Whether building has roof/terrace (0 or 1)

## Migration Steps:

### Option 1: Fresh Database (Recommended if no important data)
```powershell
# Delete existing database
Remove-Item construction.db

# Reinitialize with new schema
python app/database.py
```

### Option 2: Migrate Existing Database (If you have data to preserve)
```powershell
# Run the migration script
python migrate_database.py
```

This will:
- Add the three new columns to existing sites table
- Set default values for existing sites (0 basements, 10 floors, has roof)
- Display current configuration of all sites

### Option 3: Manual SQL Migration
```sql
ALTER TABLE sites ADD COLUMN num_basements INTEGER DEFAULT 0;
ALTER TABLE sites ADD COLUMN num_floors INTEGER DEFAULT 10;
ALTER TABLE sites ADD COLUMN has_roof INTEGER DEFAULT 1;

UPDATE sites 
SET num_basements = 0, num_floors = 10, has_roof = 1 
WHERE num_basements IS NULL OR num_floors IS NULL OR has_roof IS NULL;
```

## Code Changes Made:

### 1. database.py
- Updated `CREATE TABLE sites` statement with new columns
- Updated `add_site()` function to accept floor parameters
- Backward compatible with existing queries

### 2. admin_page.py
- Fixed unpacking errors by using index-based access: `site[0]`, `site[1]`, etc.
- Added floor configuration inputs in "Add New Site" form
- Added floor structure display in site management view
- All site iterations now handle variable column counts safely

### 3. engineer_page.py
- Added `get_ordinal_suffix()` helper function
- Added `generate_floor_options()` to dynamically create floor lists
- Floor dropdown now shows only floors that exist for selected site
- Backward compatible with sites that don't have floor configuration

### 4. migrate_database.py (NEW)
- Automated migration script
- Safely adds columns if they don't exist
- Sets default values for existing records
- Displays migration results

## Testing the Changes:

1. **Start the application:**
   ```powershell
   streamlit run app/main.py
   ```

2. **As Admin:**
   - Go to "Add New Site" tab
   - Fill in site details
   - Set floor configuration (e.g., 2 basements, 15 floors, has roof)
   - Submit

3. **As Engineer:**
   - Select the newly created site
   - Check the floor dropdown in "Upload Progress"
   - Verify it shows the correct floors for that building

## Troubleshooting:

### Error: "too many values to unpack"
- **Cause:** Old code trying to unpack 9 columns into 6 variables
- **Solution:** All code has been fixed to use index-based access
- **Action:** Ensure you're running the latest version of all files

### Error: "no such column: num_basements"
- **Cause:** Database hasn't been migrated yet
- **Solution:** Run `python migrate_database.py`

### Default floor list shows wrong floors
- **Cause:** Site was created before migration or with defaults
- **Solution:** Admin can update the site (feature to be added) or recreate it with correct floor count

## Backward Compatibility:

All code includes backward compatibility checks:
```python
num_basements = site[6] if len(site) > 6 else 0
num_floors = site[7] if len(site) > 7 else 10
has_roof = site[8] if len(site) > 8 else 1
```

This ensures the app works with both old and new database schemas.

## Future Enhancements:

- [ ] Add ability to edit site floor configuration after creation
- [ ] Add validation to prevent floor selection beyond building height
- [ ] Add floor-wise progress visualization
- [ ] Export floor-wise progress reports

## Questions?

If you encounter any issues, check:
1. Is the database migrated? Run `python migrate_database.py`
2. Are all files updated to the latest version?
3. Check the terminal for detailed error messages
