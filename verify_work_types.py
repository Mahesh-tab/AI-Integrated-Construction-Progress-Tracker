"""
Verification script to check work_types table and data
"""

import sqlite3
from datetime import datetime

def verify_work_types_table():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    
    print("=" * 60)
    print("WORK TYPES TABLE VERIFICATION")
    print("=" * 60)
    print()
    
    # Check if table exists
    c.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='work_types'""")
    if not c.fetchone():
        print("❌ ERROR: work_types table does not exist!")
        print("   Please run: python add_work_types_table.py")
        conn.close()
        return
    
    print("✓ work_types table exists")
    print()
    
    # Get table schema
    print("TABLE SCHEMA:")
    print("-" * 60)
    c.execute("PRAGMA table_info(work_types)")
    columns = c.fetchall()
    for col in columns:
        print(f"  {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else ''}")
    print()
    
    # Check indexes
    print("INDEXES:")
    print("-" * 60)
    c.execute("""SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='work_types'""")
    indexes = c.fetchall()
    if indexes:
        for idx in indexes:
            print(f"  ✓ {idx[0]}")
    else:
        print("  (no indexes found)")
    print()
    
    # Count records
    c.execute("SELECT COUNT(*) FROM work_types")
    count = c.fetchone()[0]
    print(f"TOTAL RECORDS: {count}")
    print()
    
    if count > 0:
        # Show sample data
        print("SAMPLE DATA (Last 5 entries):")
        print("-" * 60)
        c.execute("""
            SELECT id, site_id, floor_name, work_name, status, progress_percentage, date
            FROM work_types
            ORDER BY id DESC
            LIMIT 5
        """)
        rows = c.fetchall()
        
        print(f"{'ID':<5} {'Site':<6} {'Floor':<15} {'Work Type':<20} {'Status':<15} {'Progress':<8} {'Date':<20}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<6} {row[2]:<15} {row[3]:<20} {row[4]:<15} {row[5]:<8}% {row[6]:<20}")
        print()
        
        # Statistics by work type
        print("STATISTICS BY WORK TYPE:")
        print("-" * 60)
        c.execute("""
            SELECT work_name, 
                   COUNT(*) as count,
                   AVG(progress_percentage) as avg_progress,
                   MIN(progress_percentage) as min_progress,
                   MAX(progress_percentage) as max_progress
            FROM work_types
            GROUP BY work_name
            ORDER BY count DESC
        """)
        stats = c.fetchall()
        
        print(f"{'Work Type':<25} {'Count':<8} {'Avg %':<8} {'Min %':<8} {'Max %':<8}")
        print("-" * 60)
        for row in stats:
            print(f"{row[0]:<25} {row[1]:<8} {row[2]:<8.1f} {row[3]:<8} {row[4]:<8}")
        print()
        
        # Statistics by floor
        print("STATISTICS BY FLOOR:")
        print("-" * 60)
        c.execute("""
            SELECT floor_name,
                   COUNT(DISTINCT work_name) as work_types,
                   AVG(progress_percentage) as avg_progress
            FROM work_types
            GROUP BY floor_name
            ORDER BY floor_name
        """)
        floor_stats = c.fetchall()
        
        print(f"{'Floor':<25} {'Work Types':<15} {'Avg Progress':<15}")
        print("-" * 60)
        for row in floor_stats:
            print(f"{row[0]:<25} {row[1]:<15} {row[2]:<15.1f}%")
        print()
    else:
        print("ℹ️  No data in work_types table yet.")
        print("   Submit a new progress update to populate this table.")
        print()
    
    # Check progress table for comparison
    c.execute("SELECT COUNT(*) FROM progress")
    progress_count = c.fetchone()[0]
    print(f"COMPARISON:")
    print("-" * 60)
    print(f"  Total progress entries: {progress_count}")
    print(f"  Work type records:      {count}")
    
    if count == 0 and progress_count > 0:
        print()
        print("  ⚠️  NOTE: Old progress entries exist but no work_types data.")
        print("     These will use fallback parsing from descriptions.")
        print("     New entries will populate work_types table.")
    
    conn.close()
    print()
    print("=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    verify_work_types_table()
