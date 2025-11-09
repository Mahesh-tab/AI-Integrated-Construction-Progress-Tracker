"""
Engineer Dashboard - Professional Status Update Page
Supports multi-floor data entry, work type tracking, and AI-powered verification
"""

import streamlit as st
import datetime
import pickle
import re
import csv
from io import BytesIO, StringIO
from fpdf import FPDF
import PIL.Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from database import (
    get_sites, 
    get_site_by_id, 
    add_progress, 
    get_progress_by_site,
    get_progress_timeline, 
    get_category_breakdown, 
    get_verification_breakdown,
    get_monthly_progress, 
    get_floor_wise_progress, 
    get_work_type_breakdown,
    get_floor_wise_work_type_breakdown,
    get_work_type_floor_matrix,
    get_floor_completion_stats
)

load_dotenv()
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))

# ===========================
# CONFIGURATION & CONSTANTS
# ===========================

WORK_CATEGORIES = [
    "Foundation Work",
    "Structural Work",
    "Masonry",
    "Electrical Work",
    "Plumbing",
    "Finishing Work",
    "HVAC",
    "Landscaping",
    "Other"
]

WORK_TYPES = {
    "Core Construction": [
        "Structural Work",
        "Masonry Work",
        "Plastering"
    ],
    "MEP Works": [
        "Plumbing Work",
        "Electrical Work",
        "HVAC Work"
    ],
    "Finishing Works": [
        "Waterproofing",
        "Toilet Finishes",
        "Lift Lobby Finishes",
        "Painting",
        "Flooring",
        "False Ceiling"
    ]
}

WORK_STATUS_OPTIONS = [
    "Not Started",
    "Started",
    "25% Complete",
    "50% Complete",
    "75% Complete",
    "Completed"
]

# ===========================
# UTILITY FUNCTIONS
# ===========================

def get_ordinal_suffix(n):
    """Get ordinal suffix for numbers (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')

def generate_floor_options(num_basements, num_floors, has_roof):
    """Generate dynamic floor options based on site configuration"""
    floors = []
    
    # Basements
    for i in range(num_basements, 0, -1):
        floors.append(f"Basement {i}")
    
    # Ground floor
    floors.append("Ground Floor")
    
    # Upper floors
    for i in range(1, num_floors + 1):
        floors.append(f"{i}{get_ordinal_suffix(i)} Floor")
    
    # Roof/Terrace
    if has_roof:
        floors.append("Roof/Terrace")
    
    return floors

def initialize_session_state():
    """Initialize session state variables"""
    if 'floor_entries' not in st.session_state:
        st.session_state.floor_entries = []
    if 'pending_analysis' not in st.session_state:
        st.session_state.pending_analysis = None
    if 'current_floor_data' not in st.session_state:
        st.session_state.current_floor_data = {}

# ===========================
# AI ANALYSIS FUNCTIONS
# ===========================

def get_gemini_analysis(description, image_data_list, category, floor_data):
    """
    Send all collected data to Gemini AI for comprehensive analysis
    """
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        
        # Convert images
        images = []
        for img_data in image_data_list:
            image = PIL.Image.open(BytesIO(img_data))
            images.append(image)
        
        # Build comprehensive prompt with all floor data
        floor_summary = "\n\n**FLOOR-WISE PROGRESS DETAILS:**\n"
        for floor_info in floor_data:
            floor_summary += f"\n**{floor_info['floor_name']}:**\n"
            floor_summary += f"- Work Phase: {floor_info['work_phase']}\n"
            floor_summary += f"- Overall Floor Progress: {floor_info['floor_progress']}%\n"
            floor_summary += "- Work Types:\n"
            for work_type, details in floor_info['work_types'].items():
                floor_summary += f"  • {work_type}: {details['status']} ({details['progress']}%)\n"
        
        prompt = f"""You are a certified construction site inspector conducting a professional analysis.

**PROJECT CONTEXT:**
- Work Category: {category}
- Number of Images: {len(images)}
- Engineer's Description: {description}

{floor_summary}

**ANALYSIS INSTRUCTIONS:**
Examine all {len(images)} image(s) and cross-reference with the provided floor-wise progress data.

**REQUIRED REPORT STRUCTURE:**

**1. VERIFICATION STATUS**
Select ONE based on visual evidence:
- ✅ VERIFIED: Visual evidence fully confirms reported work
- ⚠️ PARTIALLY VERIFIED: Some aspects confirmed, discrepancies noted
- ❌ NOT VERIFIED: Visual evidence contradicts description
- ℹ️ INSUFFICIENT DATA: Image quality/coverage inadequate

**2. VISUAL EVIDENCE ANALYSIS**
- Document what is clearly visible in each image
- Identify materials, equipment, and completed work
- Note image quality and coverage adequacy
- Compare visual findings with engineer's floor-wise description

**3. TECHNICAL QUALITY ASSESSMENT**
- **Workmanship Rating:** [Excellent/Good/Adequate/Poor/Cannot Assess]
- **Justification:** Specific observations
- **Materials & Specifications:** Visible materials and condition
- **Defects/Issues:** Any visible problems
- **Industry Standards Compliance:** For {category}

**4. SAFETY & COMPLIANCE**
- **PPE Status:** Visible safety gear
- **Site Safety Measures:** Barriers, signage, fall protection
- **Hazard Identification:** List visible hazards
- **Housekeeping:** Site cleanliness and organization

**5. FLOOR-WISE VERIFICATION**
For each floor mentioned, verify:
- Does visual evidence support the claimed progress percentage?
- Are the listed work types actually visible in the images?
- Any discrepancies between claimed and observed progress?

**6. RECOMMENDATIONS**
- **Immediate Actions Required**
- **Quality Improvements**
- **Additional Documentation Needed**
- **Follow-up Inspections**

**7. PROGRESS ASSESSMENT**
- **Overall Estimated Completion:** [0-100]%
- **Basis for Estimate:** Explain reasoning
- **Work Remaining:** What needs to be completed
- **Timeline Assessment:** Is progress on track?

Provide objective, evidence-based analysis using precise construction terminology."""

        # Generate content
        content = [prompt] + images
        response = model.generate_content(content)
        
        # Extract verification status
        response_text = response.text
        if "✅ VERIFIED" in response_text or "VERIFIED: Work matches" in response_text:
            status = "Verified"
        elif "⚠️ PARTIALLY VERIFIED" in response_text:
            status = "Partially Verified"
        elif "❌ NOT VERIFIED" in response_text:
            status = "Not Verified"
        else:
            status = "Needs Review"
        
        return response_text, status
        
    except Exception as e:
        return f"Error generating AI analysis: {str(e)}", "Error"

# ===========================
# FLOOR DATA COLLECTION UI
# ===========================

def render_floor_data_form(floor_options, site_id):
    """Render form for collecting data for a single floor"""
    
    st.subheader("🏢 Add Floor Progress Data")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        floor_name = st.selectbox(
            "Select Floor/Level",
            floor_options,
            key="current_floor_select"
        )
    
    with col2:
        work_phase = st.selectbox(
            "Work Phase",
            ["Not Started", "In Progress", "Completed", "Under Review", "Rework Required"],
            key="current_work_phase"
        )
    
    floor_progress = st.slider(
        "Overall Floor Progress (%)",
        0, 100, 0, 5,
        key="current_floor_progress"
    )
    
    st.markdown("---")
    st.markdown("**✅ Select Work Types and Set Progress**")
    
    work_types_selected = {}
    
    # Render work types by category
    for category_name, work_list in WORK_TYPES.items():
        st.markdown(f"**{category_name}**")
        
        for work_name in work_list:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                is_selected = st.checkbox(
                    work_name,
                    key=f"check_{work_name}_{floor_name}"
                )
            
            if is_selected:
                with col2:
                    status = st.selectbox(
                        "Status",
                        WORK_STATUS_OPTIONS,
                        key=f"status_{work_name}_{floor_name}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    progress = st.number_input(
                        "Progress %",
                        0, 100, 0, 5,
                        key=f"progress_{work_name}_{floor_name}",
                        label_visibility="collapsed"
                    )
                
                work_types_selected[work_name] = {
                    'status': status,
                    'progress': progress
                }
        
        st.markdown("")  # Spacing
    
    st.markdown("---")
    
    # Summary
    if work_types_selected:
        st.info(f"✅ **{len(work_types_selected)} work type(s) selected for {floor_name}**")
        for work_name, details in work_types_selected.items():
            st.write(f"  • {work_name}: {details['status']} ({details['progress']}%)")
    
    # Add to list button
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("➕ Add This Floor to Submission", type="primary", use_container_width=True):
            if not work_types_selected:
                st.error("⚠️ Please select at least one work type for this floor")
            else:
                # Add to session state
                floor_entry = {
                    'floor_name': floor_name,
                    'work_phase': work_phase,
                    'floor_progress': floor_progress,
                    'work_types': work_types_selected
                }
                
                # Check if floor already exists and replace it
                existing_index = None
                for idx, entry in enumerate(st.session_state.floor_entries):
                    if entry['floor_name'] == floor_name:
                        existing_index = idx
                        break
                
                if existing_index is not None:
                    st.session_state.floor_entries[existing_index] = floor_entry
                    st.success(f"✅ Updated data for {floor_name}")
                else:
                    st.session_state.floor_entries.append(floor_entry)
                    st.success(f"✅ Added {floor_name} to submission")
                
                st.rerun()
    
    with col2:
        if st.button("🔄 Clear Form", use_container_width=True):
            # Clear form (rerun will reset)
            st.rerun()

def render_floor_entries_summary():
    """Display summary of all added floor entries"""
    
    if not st.session_state.floor_entries:
        st.info("📭 No floor data added yet. Add floor progress data above.")
        return
    
    st.subheader(f"📋 Added Floor Data ({len(st.session_state.floor_entries)} floor(s))")
    
    for idx, entry in enumerate(st.session_state.floor_entries):
        with st.expander(f"**{entry['floor_name']}** - {entry['work_phase']} ({entry['floor_progress']}%)", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Work Phase:** {entry['work_phase']}")
                st.markdown(f"**Floor Progress:** {entry['floor_progress']}%")
                st.markdown(f"**Work Types ({len(entry['work_types'])}):**")
                
                for work_name, details in entry['work_types'].items():
                    st.write(f"  • {work_name}: {details['status']} ({details['progress']}%)")
            
            with col2:
                if st.button("🗑️ Remove", key=f"remove_{idx}", use_container_width=True):
                    st.session_state.floor_entries.pop(idx)
                    st.rerun()

# ===========================
# UPLOAD FORM
# ===========================

def render_upload_form(site_id, site_details):
    """Main upload form for progress updates"""
    
    st.header("📤 Upload Progress Update")
    
    # Basic Information Section
    st.subheader("📋 Basic Information")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        category = st.selectbox(
            "Work Category *",
            WORK_CATEGORIES
        )
        
        description = st.text_area(
            "Overall Work Description *",
            placeholder="Provide a comprehensive description of all work completed across floors...",
            height=120
        )
    
    with col2:
        overall_progress = st.slider(
            "Overall Site Progress (%)",
            0, 100, 0, 5
        )
        st.info(f"**Current:** {overall_progress}%")
    
    st.markdown("---")
    
    # Floor Data Collection
    num_basements = site_details[6] if len(site_details) > 6 else 0
    num_floors = site_details[7] if len(site_details) > 7 else 10
    has_roof = site_details[8] if len(site_details) > 8 else 1
    floor_options = generate_floor_options(num_basements, num_floors, has_roof)
    
    render_floor_data_form(floor_options, site_id)
    
    st.markdown("---")
    
    # Display summary of added floors
    render_floor_entries_summary()
    
    st.markdown("---")
    
    # Image Upload Section
    st.subheader("📸 Progress Photos")
    st.info("💡 **Tip:** Upload multiple photos showing different angles and floors for comprehensive AI analysis")
    
    uploaded_files = st.file_uploader(
        "Upload Progress Photos (Multiple allowed) *",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Upload clear photos from all floors showing the work completed"
    )
    
    if uploaded_files:
        st.success(f"✅ **{len(uploaded_files)} image(s) uploaded**")
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                st.image(file, caption=f"Image {idx+1}", use_container_width=True)
    
    st.markdown("---")
    
    # Submit Button
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        submit_button = st.button(
            "🤖 Analyze with AI",
            type="primary",
            use_container_width=True
        )
    
    # Handle submission
    if submit_button:
        # Validation
        if not description:
            st.error("⚠️ Please provide an overall work description")
            return
        
        if not st.session_state.floor_entries:
            st.error("⚠️ Please add at least one floor's progress data")
            return
        
        if not uploaded_files:
            st.error("⚠️ Please upload at least one progress photo")
            return
        
        # Collect image data
        image_data_list = [file.getvalue() for file in uploaded_files]
        combined_image_data = pickle.dumps(image_data_list)
        
        # Generate enhanced description with floor data
        enhanced_description = f"{description}\n\n"
        enhanced_description += "=== DETAILED FLOOR-WISE BREAKDOWN ===\n\n"
        
        for entry in st.session_state.floor_entries:
            enhanced_description += f"**{entry['floor_name']}:**\n"
            enhanced_description += f"  Work Phase: {entry['work_phase']}\n"
            enhanced_description += f"  Floor Progress: {entry['floor_progress']}%\n"
            enhanced_description += "  Work Types:\n"
            for work_name, details in entry['work_types'].items():
                enhanced_description += f"    - {work_name}: {details['status']} | {details['progress']}%\n"
            enhanced_description += "\n"
        
        # AI Analysis
        with st.spinner(f"🤖 Analyzing {len(uploaded_files)} image(s) and {len(st.session_state.floor_entries)} floor(s)..."):
            ai_report, verification_status = get_gemini_analysis(
                description,
                image_data_list,
                category,
                st.session_state.floor_entries
            )
        
        # Store in session for review
        st.session_state.pending_analysis = {
            'site_id': site_id,
            'category': category,
            'description': description,
            'enhanced_description': enhanced_description,
            'combined_image_data': combined_image_data,
            'ai_report': ai_report,
            'verification_status': verification_status,
            'overall_progress': overall_progress,
            'floor_entries': st.session_state.floor_entries.copy(),
            'num_images': len(uploaded_files)
        }
        
        st.rerun()

# ===========================
# AI ANALYSIS REVIEW
# ===========================

def render_analysis_review():
    """Display AI analysis results and allow confirmation"""
    
    if not st.session_state.pending_analysis:
        return
    
    pending = st.session_state.pending_analysis
    
    st.markdown("---")
    st.header("🤖 AI Analysis Results")
    
    # Verification status badge
    status = pending['verification_status']
    if status == "Verified":
        st.success(f"✅ **Verification Status:** {status}")
    elif status == "Partially Verified":
        st.warning(f"⚠️ **Verification Status:** {status}")
    elif status == "Not Verified":
        st.error(f"❌ **Verification Status:** {status}")
    else:
        st.info(f"ℹ️ **Verification Status:** {status}")
    
    # Display AI Report
    with st.expander("📋 View Complete AI Analysis Report", expanded=True):
        st.markdown(pending['ai_report'])
    
    # Review submission details
    with st.expander("📝 Review Submission Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Category:** {pending['category']}")
            st.markdown(f"**Overall Progress:** {pending['overall_progress']}%")
            st.markdown(f"**Images Submitted:** {pending['num_images']}")
        
        with col2:
            st.markdown(f"**Floors Covered:** {len(pending['floor_entries'])}")
            total_work_types = sum(len(entry['work_types']) for entry in pending['floor_entries'])
            st.markdown(f"**Total Work Types:** {total_work_types}")
        
        st.markdown("---")
        st.markdown("**Floor-wise Summary:**")
        for entry in pending['floor_entries']:
            st.write(f"**{entry['floor_name']}** - {entry['work_phase']} ({entry['floor_progress']}%) - {len(entry['work_types'])} work types")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Confirm & Save to Database", type="primary", use_container_width=True):
            save_to_database(pending)
    
    with col2:
        if st.button("🔄 Modify & Re-analyze", use_container_width=True):
            st.session_state.pending_analysis = None
            st.rerun()
    
    with col3:
        if st.button("❌ Cancel Submission", use_container_width=True):
            st.session_state.pending_analysis = None
            st.session_state.floor_entries = []
            st.rerun()

def save_to_database(pending):
    """Save the analyzed progress to database"""
    
    user_id = st.session_state.user_id
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare work types data for all floors
    all_work_types = {}
    for floor_entry in pending['floor_entries']:
        floor_name = floor_entry['floor_name']
        for work_name, details in floor_entry['work_types'].items():
            # Create unique key with floor and work type
            key = f"{floor_name}|{work_name}"
            all_work_types[key] = {
                'floor_name': floor_name,
                'work_name': work_name,
                'status': details['status'],
                'progress': details['progress']
            }
    
    # Add to database - we'll modify add_progress to handle multi-floor data
    try:
        add_progress_multi_floor(
            site_id=pending['site_id'],
            user_id=user_id,
            date=date,
            category=pending['category'],
            description=pending['description'],
            image=pending['combined_image_data'],
            ai_report=pending['ai_report'],
            ai_verification_status=pending['verification_status'],
            progress_percentage=pending['overall_progress'],
            floor_entries=pending['floor_entries']
        )
        
        st.success("✅ Progress update saved successfully!")
        st.balloons()
        
        # Clear session state
        st.session_state.pending_analysis = None
        st.session_state.floor_entries = []
        
        # Small delay before rerun
        import time
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error saving to database: {str(e)}")

def add_progress_multi_floor(site_id, user_id, date, category, description, image, ai_report, 
                              ai_verification_status, progress_percentage, floor_entries):
    """
    Enhanced version of add_progress that handles multiple floors
    """
    import sqlite3
    
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    
    try:
        # Insert main progress record
        c.execute("""INSERT INTO progress (site_id, user_id, date, category, description, image, 
                     ai_report, ai_verification_status, progress_percentage) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (site_id, user_id, date, category, description, image, ai_report, 
                   ai_verification_status, progress_percentage))
        
        progress_id = c.lastrowid
        
        # Insert work types for each floor
        for floor_entry in floor_entries:
            floor_name = floor_entry['floor_name']
            for work_name, details in floor_entry['work_types'].items():
                c.execute("""INSERT INTO work_types (progress_id, site_id, floor_name, work_name, 
                             status, progress_percentage, date)
                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (progress_id, site_id, floor_name, work_name, 
                           details['status'], details['progress'], date))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ===========================
# PROGRESS HISTORY TAB
# ===========================

def render_progress_history(site_id, site_details):
    """Display progress history with filtering"""
    
    st.header("📊 Progress History")
    
    progress_entries = get_progress_by_site(site_id)
    
    if not progress_entries:
        st.info("📭 No progress updates found. Add your first update to get started!")
        return
    
    st.success(f"📊 **Total Updates:** {len(progress_entries)}")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + WORK_CATEGORIES
        )
    
    with col2:
        filter_status = st.selectbox(
            "Filter by Verification",
            ["All", "Verified", "Partially Verified", "Not Verified", "Needs Review"]
        )
    
    with col3:
        sort_order = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First", "Progress %"]
        )
    
    # Apply filters and sorting
    filtered_entries = []
    for entry in progress_entries:
        entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
        
        if filter_category != "All" and category != filter_category:
            continue
        if filter_status != "All" and verification_status != filter_status:
            continue
        
        filtered_entries.append(entry)
    
    # Sort
    if sort_order == "Oldest First":
        filtered_entries.reverse()
    elif sort_order == "Progress %":
        filtered_entries.sort(key=lambda x: x[8], reverse=True)
    
    st.markdown("---")
    
    # Display entries
    for entry in filtered_entries:
        entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
        
        # Status indicator
        status_emoji = {
            "Verified": "🟢",
            "Partially Verified": "🟡",
            "Not Verified": "🔴",
            "Needs Review": "⚪"
        }.get(verification_status, "⚪")
        
        with st.expander(f"{status_emoji} **{date}** | {category} | {username} | {progress_pct}%"):
            render_progress_entry_details(entry, site_details)

def render_progress_entry_details(entry, site_details):
    """Render detailed view of a progress entry"""
    
    entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
    
    # Try to load images
    try:
        image_list = pickle.loads(image)
        num_images = len(image_list)
    except:
        image_list = [image]
        num_images = 1
    
    # Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Display images
        st.markdown(f"**📸 Progress Photos ({num_images}):**")
        for idx, img_data in enumerate(image_list):
            st.image(BytesIO(img_data), caption=f"Image {idx+1}", use_container_width=True)
    
    with col2:
        # Metadata
        st.markdown(f"**📅 Date:** {date}")
        st.markdown(f"**👤 Engineer:** {username}")
        st.markdown(f"**📂 Category:** {category}")
        st.markdown(f"**📊 Overall Progress:** {progress_pct}%")
        st.markdown(f"**✅ Status:** {verification_status}")
    
    st.markdown("---")
    
    # Description
    st.markdown("**📝 Work Description:**")
    # Parse and display floor-wise data if present
    if "=== DETAILED FLOOR-WISE BREAKDOWN ===" in description:
        parts = description.split("=== DETAILED FLOOR-WISE BREAKDOWN ===")
        st.write(parts[0].strip())
        
        st.markdown("**🏢 Floor-wise Details:**")
        st.code(parts[1].strip())
    else:
        st.write(description)
    
    st.markdown("---")
    
    # AI Report
    st.markdown("**🤖 AI Analysis Report:**")
    st.markdown(ai_report)
    
    st.markdown("---")
    
    # Download PDF
    if st.button(f"📥 Download PDF Report", key=f"pdf_{entry_id}", use_container_width=True):
        generate_pdf_report(entry, site_details, num_images)

def generate_pdf_report(entry, site_details, num_images):
    """Generate and download PDF report"""
    
    entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 12, "CONSTRUCTION PROGRESS REPORT", ln=True, align='C')
    pdf.ln(5)
    
    # Project Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "PROJECT INFORMATION", ln=True)
    pdf.set_font("Arial", '', 10)
    
    info = [
        ("Site:", site_details[1]),
        ("Location:", site_details[2]),
        ("Date:", date),
        ("Engineer:", username),
        ("Category:", category),
        ("Progress:", f"{progress_pct}%"),
        ("Verification:", verification_status),
        ("Images:", str(num_images))
    ]
    
    for label, value in info:
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(40, 6, label, 0, 0)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(0, 6, str(value))
    
    pdf.ln(5)
    
    # Description
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "WORK DESCRIPTION", ln=True)
    pdf.set_font("Arial", '', 9)
    
    # Clean description for PDF
    clean_desc = description.replace('=== DETAILED FLOOR-WISE BREAKDOWN ===', '\n\nFLOOR-WISE BREAKDOWN:\n')
    clean_desc = clean_desc.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_desc)
    
    pdf.ln(5)
    
    # AI Report
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "AI ANALYSIS REPORT", ln=True)
    pdf.set_font("Arial", '', 9)
    
    clean_report = ai_report.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_report)
    
    # Footer
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    
    # Output
    pdf_output = pdf.output(dest='S').encode('latin-1')
    
    st.download_button(
        label="📥 Download PDF",
        data=pdf_output,
        file_name=f"progress_report_{date.replace(':', '-')}.pdf",
        mime="application/pdf"
    )

# ===========================
# ANALYTICS TAB
# ===========================

def render_analytics(site_id):
    """Display analytics and visualizations"""
    
    st.header("📈 Analytics & Visualizations")
    
    progress_entries = get_progress_by_site(site_id)
    
    if not progress_entries:
        st.info("📭 No progress data available. Add updates to see analytics!")
        return
    
    # Floor Filter Section (Global for all analytics)
    st.markdown("### 🔍 Filter Options")
    
    # Get all available floors from the database
    floor_work_data = get_floor_wise_work_type_breakdown(site_id)
    
    if floor_work_data:
        all_floors = sorted(floor_work_data.keys())
        
        col_filter1, col_filter2 = st.columns([3, 1])
        
        with col_filter1:
            selected_floors = st.multiselect(
                "Select Floors to Display",
                all_floors,
                default=all_floors,
                key="analytics_floor_filter",
                help="Choose specific floors to analyze. This filter applies to all floor-related visualizations below."
            )
        
        with col_filter2:
            st.markdown("")  # Spacing
            st.markdown("")  # Spacing
            if st.button("🔄 Reset Filter", use_container_width=True):
                selected_floors = all_floors
                st.rerun()
        
        if not selected_floors:
            st.warning("⚠️ Please select at least one floor to display analytics.")
            selected_floors = all_floors
        
        # Filter floor_work_data based on selection
        filtered_floor_data = {floor: data for floor, data in floor_work_data.items() if floor in selected_floors}
        
        st.info(f"📊 Showing analytics for **{len(selected_floors)}** floor(s): {', '.join(selected_floors)}")
    else:
        selected_floors = []
        filtered_floor_data = {}
    
    st.markdown("---")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Updates", len(progress_entries))
    
    with col2:
        latest_progress = progress_entries[0][8]
        st.metric("Latest Progress", f"{latest_progress}%")
    
    with col3:
        verified = sum(1 for e in progress_entries if e[7] == "Verified")
        st.metric("Verified", verified)
    
    with col4:
        categories = len(set(e[3] for e in progress_entries))
        st.metric("Categories", categories)
    
    st.markdown("---")
    
    # Progress Timeline
    st.subheader("📊 Progress Timeline")
    timeline_data = get_progress_timeline(site_id)
    
    if timeline_data:
        df = pd.DataFrame(timeline_data, columns=['Date', 'Progress %', 'Category'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Progress %'],
            mode='lines+markers',
            name='Progress',
            line=dict(color='#0066cc', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Progress %",
            height=400,
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📂 Category Breakdown")
        category_data = get_category_breakdown(site_id)
        
        if category_data:
            df = pd.DataFrame(category_data, columns=['Category', 'Count'])
            fig = px.pie(df, values='Count', names='Category', title='Work Categories')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("✅ Verification Status")
        verification_data = get_verification_breakdown(site_id)
        
        if verification_data:
            df = pd.DataFrame(verification_data, columns=['Status', 'Count'])
            
            colors = {
                'Verified': '#28a745',
                'Partially Verified': '#ffc107',
                'Not Verified': '#dc3545',
                'Needs Review': '#6c757d'
            }
            color_list = [colors.get(s, '#6c757d') for s in df['Status']]
            
            fig = go.Figure(data=[go.Bar(
                x=df['Status'],
                y=df['Count'],
                marker_color=color_list
            )])
            
            fig.update_layout(title='Verification Status', height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Floor-wise analysis
    st.markdown("---")
    st.subheader("🏢 Floor-wise Progress Analysis")
    
    floor_data = get_floor_wise_progress(site_id)
    
    # Apply floor filter if available
    if floor_data and selected_floors:
        floor_data = [f for f in floor_data if f[0] in selected_floors]
    
    if floor_data:
        df = pd.DataFrame(floor_data, columns=['Floor', 'Updates', 'Avg Progress', 'Work Types'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure(data=[go.Bar(
                x=df['Floor'],
                y=df['Avg Progress'],
                marker_color='#17a2b8',
                text=df['Avg Progress'].round(1),
                textposition='auto'
            )])
            fig.update_layout(
                title='Average Progress by Floor',
                yaxis=dict(range=[0, 100]),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[go.Bar(
                x=df['Floor'],
                y=df['Updates'],
                marker_color='#6f42c1',
                text=df['Updates'],
                textposition='auto'
            )])
            fig.update_layout(
                title='Updates by Floor',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.markdown("**📋 Floor Status Summary:**")
        display_df = df.copy()
        display_df['Avg Progress'] = display_df['Avg Progress'].round(1).astype(str) + '%'
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Work type analysis
    st.markdown("---")
    st.subheader("🔧 Work Type Analysis")
    
    work_type_data = get_work_type_breakdown(site_id)
    
    if work_type_data:
        df = pd.DataFrame(work_type_data, columns=['Work Type', 'Total', 'Completed', 'In Progress', 'Avg Progress'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(name='Completed', x=df['Work Type'], y=df['Completed'], marker_color='#28a745'))
        fig.add_trace(go.Bar(name='In Progress', x=df['Work Type'], y=df['In Progress'], marker_color='#ffc107'))
        
        not_started = df['Total'] - df['Completed'] - df['In Progress']
        fig.add_trace(go.Bar(name='Not Started', x=df['Work Type'], y=not_started, marker_color='#6c757d'))
        
        fig.update_layout(
            title='Work Type Status Distribution',
            barmode='stack',
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.markdown("**📊 Work Type Summary:**")
        display_df = df.copy()
        display_df['Completion Rate'] = ((df['Completed'] / df['Total']) * 100).round(1).astype(str) + '%'
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Floor-wise Work Type Analysis
    st.markdown("---")
    st.subheader("🏗️ Floor-wise Work Type Analysis")
    
    if filtered_floor_data:
        # Create tabs for different views
        view_tab1, view_tab2, view_tab3 = st.tabs(["📊 Progress Heatmap", "📈 Floor Comparison", "📋 Detailed Table"])
        
        with view_tab1:
            st.markdown("**Work Type Progress Across All Floors**")
            
            # Create heatmap data - use filtered floors
            matrix_data = get_work_type_floor_matrix(site_id)
            
            if matrix_data:
                # Filter matrix data based on selected floors
                filtered_matrix = [item for item in matrix_data if item['Floor'] in selected_floors]
                
                if filtered_matrix:
                    # Convert to pivot table format
                    df_matrix = pd.DataFrame(filtered_matrix)
                    pivot_table = df_matrix.pivot(index='Work Type', columns='Floor', values='Progress')
                    
                    # Reorder columns based on selected_floors order
                    available_cols = [col for col in selected_floors if col in pivot_table.columns]
                    pivot_table = pivot_table[available_cols]
                    
                    # Create heatmap
                    fig = go.Figure(data=go.Heatmap(
                        z=pivot_table.values,
                        x=pivot_table.columns,
                        y=pivot_table.index,
                        colorscale=[
                            [0, '#dc3545'],      # Red for 0%
                            [0.25, '#ffc107'],   # Yellow for 25%
                            [0.5, '#17a2b8'],    # Cyan for 50%
                            [0.75, '#20c997'],   # Teal for 75%
                            [1, '#28a745']       # Green for 100%
                        ],
                        text=pivot_table.values,
                        texttemplate='%{text:.0f}%',
                        textfont={"size": 10},
                        colorbar=dict(title="Progress %"),
                        hoverongaps=False,
                        hovertemplate='<b>%{y}</b><br>Floor: %{x}<br>Progress: %{z:.1f}%<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=f'Work Type Progress Heatmap ({len(selected_floors)} Floor(s))',
                        xaxis_title='Floor',
                        yaxis_title='Work Type',
                        height=max(400, len(pivot_table.index) * 30),
                        xaxis={'side': 'top'},
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Legend
                    st.info("🎨 **Color Legend:** 🔴 0% → 🟡 25% → 🔵 50% → 🟢 75% → ✅ 100%")
                else:
                    st.warning("No data available for the selected floors.")
            else:
                st.info("No heatmap data available yet.")
        
        with view_tab2:
            st.markdown("**Compare Work Type Progress Across Floors**")
            
            # Allow user to select work types to compare - use filtered data
            all_work_types = set()
            for floor, work_types in filtered_floor_data.items():
                all_work_types.update(work_types.keys())
            
            selected_work_types = st.multiselect(
                "Select Work Types to Compare",
                sorted(all_work_types),
                default=sorted(all_work_types)[:5] if len(all_work_types) >= 5 else sorted(all_work_types)
            )
            
            if selected_work_types:
                # Create grouped bar chart - use filtered floors
                floors = [f for f in selected_floors if f in filtered_floor_data]
                
                fig = go.Figure()
                
                for work_type in selected_work_types:
                    progress_values = []
                    for floor in floors:
                        if work_type in filtered_floor_data[floor]:
                            avg_progress = filtered_floor_data[floor][work_type]['total_progress'] / filtered_floor_data[floor][work_type]['count']
                            progress_values.append(avg_progress)
                        else:
                            progress_values.append(0)
                    
                    fig.add_trace(go.Bar(
                        name=work_type,
                        x=floors,
                        y=progress_values,
                        text=[f"{v:.0f}%" for v in progress_values],
                        textposition='auto',
                        hovertemplate='<b>%{fullData.name}</b><br>Floor: %{x}<br>Progress: %{y:.1f}%<extra></extra>'
                    ))
                
                fig.update_layout(
                    title=f'Work Type Progress Comparison ({len(selected_floors)} Floor(s))',
                    xaxis_title='Floor',
                    yaxis_title='Average Progress %',
                    barmode='group',
                    height=500,
                    yaxis=dict(range=[0, 100]),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Floor completion statistics - filtered
                st.markdown("---")
                st.markdown("**🏢 Floor Completion Statistics**")
                
                floor_stats = get_floor_completion_stats(site_id)
                
                if floor_stats:
                    # Filter stats based on selected floors
                    filtered_stats = [stat for stat in floor_stats if stat[0] in selected_floors]
                    
                    if filtered_stats:
                        df_stats = pd.DataFrame(filtered_stats, columns=[
                            'Floor', 'Total Work Types', 'Completed', 'In Progress', 'Not Started', 'Avg Progress %'
                        ])
                        
                        # Create stacked bar chart for completion status
                        fig_completion = go.Figure()
                        
                        fig_completion.add_trace(go.Bar(
                            name='Completed',
                            x=df_stats['Floor'],
                            y=df_stats['Completed'],
                            marker_color='#28a745',
                            text=df_stats['Completed'],
                            textposition='auto'
                        ))
                        
                        fig_completion.add_trace(go.Bar(
                            name='In Progress',
                            x=df_stats['Floor'],
                            y=df_stats['In Progress'],
                            marker_color='#ffc107',
                            text=df_stats['In Progress'],
                            textposition='auto'
                        ))
                        
                        fig_completion.add_trace(go.Bar(
                            name='Not Started',
                            x=df_stats['Floor'],
                            y=df_stats['Not Started'],
                            marker_color='#dc3545',
                            text=df_stats['Not Started'],
                            textposition='auto'
                        ))
                        
                        fig_completion.update_layout(
                            title=f'Work Type Completion Status ({len(selected_floors)} Floor(s))',
                            xaxis_title='Floor',
                            yaxis_title='Number of Work Types',
                            barmode='stack',
                            height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig_completion, use_container_width=True)
                    else:
                        st.info("No completion statistics available for selected floors.")
            else:
                st.warning("Please select at least one work type to compare")
        
        with view_tab3:
            st.markdown("**Detailed Floor-wise Work Type Data**")
            
            # Create expandable sections for each floor - use filtered data
            for floor in sorted(filtered_floor_data.keys()):
                with st.expander(f"**{floor}** - {len(filtered_floor_data[floor])} work type(s)", expanded=False):
                    
                    # Calculate floor statistics
                    floor_work_types = filtered_floor_data[floor]
                    total_work_types = len(floor_work_types)
                    avg_floor_progress = sum(wt['total_progress'] / wt['count'] for wt in floor_work_types.values()) / total_work_types if total_work_types > 0 else 0
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Work Types", total_work_types)
                    with col2:
                        st.metric("Avg Progress", f"{avg_floor_progress:.1f}%")
                    with col3:
                        completed = sum(1 for wt in floor_work_types.values() if wt['latest_progress'] >= 100)
                        st.metric("Completed", f"{completed}/{total_work_types}")
                    
                    st.markdown("---")
                    
                    # Create detailed table
                    work_type_rows = []
                    for work_name, data in sorted(floor_work_types.items()):
                        avg_progress = data['total_progress'] / data['count']
                        work_type_rows.append({
                            'Work Type': work_name,
                            'Latest Status': data['latest_status'],
                            'Latest Progress': f"{data['latest_progress']}%",
                            'Avg Progress': f"{avg_progress:.1f}%",
                            'Updates': data['count'],
                            'Last Updated': data['latest_date'][:10] if data['latest_date'] else 'N/A'
                        })
                    
                    df_floor = pd.DataFrame(work_type_rows)
                    
                    # Color coding for progress
                    def highlight_progress(row):
                        latest_prog = int(row['Latest Progress'].replace('%', ''))
                        if latest_prog >= 100:
                            return ['background-color: #d4edda'] * len(row)
                        elif latest_prog >= 75:
                            return ['background-color: #d1ecf1'] * len(row)
                        elif latest_prog >= 50:
                            return ['background-color: #fff3cd'] * len(row)
                        elif latest_prog > 0:
                            return ['background-color: #f8d7da'] * len(row)
                        else:
                            return ['background-color: #e2e3e5'] * len(row)
                    
                    st.dataframe(
                        df_floor.style.apply(highlight_progress, axis=1),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.caption("🟢 Completed | 🔵 75%+ | 🟡 50-74% | 🔴 25-49% | ⚪ Not Started")
            
            if not filtered_floor_data:
                st.info("No data available for the selected floors.")
    else:
        st.info("No floor-wise work type data available yet. Add progress updates with work type details to see this analysis.")

# ===========================
# MAIN FUNCTION
# ===========================

def show():
    """Main entry point for engineer dashboard"""
    
    initialize_session_state()
    
    st.title("👷 Site Engineer Dashboard")
    
    # Site selection
    sites = get_sites()
    
    if not sites:
        st.warning("⚠️ No construction sites available. Contact admin to add sites.")
        return
    
    site_options = {f"{site[1]} - {site[2]}": site[0] for site in sites}
    selected_site_label = st.selectbox("🏗️ Select Construction Site", list(site_options.keys()))
    site_id = site_options[selected_site_label]
    
    # Get site details
    site_details = get_site_by_id(site_id)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload Progress", "📊 Progress History", "📈 Analytics"])
    
    with tab1:
        # Check if we have pending analysis
        if st.session_state.pending_analysis:
            render_analysis_review()
        else:
            render_upload_form(site_id, site_details)
    
    with tab2:
        render_progress_history(site_id, site_details)
    
    with tab3:
        render_analytics(site_id)

if __name__ == "__main__":
    show()
