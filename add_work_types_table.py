"""
Migration script to add work_types table to existing database
This table stores structured work type data from form submissions
"""

import sqlite3

def migrate_add_work_types_table():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    
    # Check if work_types table already exists
    c.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='work_types'""")
    if c.fetchone():
        print("✓ work_types table already exists")
        conn.close()
        return
    
    # Create work_types table
    print("Creating work_types table...")
    c.execute('''
        CREATE TABLE work_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            progress_id INTEGER NOT NULL,
            site_id INTEGER NOT NULL,
            floor_name TEXT NOT NULL,
            work_name TEXT NOT NULL,
            status TEXT NOT NULL,
            progress_percentage INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (progress_id) REFERENCES progress (id),
            FOREIGN KEY (site_id) REFERENCES sites (id)
        )
    ''')
    
    conn.commit()
    print("✓ work_types table created successfully!")
    
    # Create indexes for better query performance
    print("Creating indexes...")
    c.execute("""CREATE INDEX IF NOT EXISTS idx_work_types_site_id ON work_types(site_id)""")
    c.execute("""CREATE INDEX IF NOT EXISTS idx_work_types_progress_id ON work_types(progress_id)""")
    c.execute("""CREATE INDEX IF NOT EXISTS idx_work_types_floor ON work_types(floor_name)""")
    
    conn.commit()
    print("✓ Indexes created successfully!")
    
    conn.close()
    print("\n✅ Migration completed successfully!")
    print("\nNote: Old progress entries will use fallback parsing from descriptions.")
    print("New progress entries will store data directly in work_types table for better performance.")

if __name__ == '__main__':
    print("=" * 60)
    print("WORK TYPES TABLE MIGRATION")
    print("=" * 60)
    print("\nThis script will add a new 'work_types' table to store")
    print("structured work type data from form submissions.")
    print()
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate_add_work_types_table()
    else:
        print("Migration cancelled.")
