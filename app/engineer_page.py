import streamlit as st
from database import (get_sites, add_progress, get_progress_by_site, get_site_by_id,
                      get_progress_timeline, get_category_breakdown, get_verification_breakdown,
                      get_monthly_progress, get_floor_wise_progress, get_work_type_breakdown)
import datetime
import os
import google.generativeai as genai
from io import BytesIO
from fpdf import FPDF
from dotenv import load_dotenv
import json
import base64
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def clean_markdown_for_pdf(text):
    """
    Remove markdown formatting for clean PDF output and structure it better.
    """
    import re
    
    # Remove markdown headers (##, ###, etc.) but keep structure
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # Bold+Italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)          # Italic
    text = re.sub(r'__(.+?)__', r'\1', text)          # Bold (underscore)
    text = re.sub(r'_(.+?)_', r'\1', text)            # Italic (underscore)
    
    # Remove inline code markers
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove links but keep text [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    # Convert list markers to bullets
    text = re.sub(r'^\s*[-*+]\s+', '  - ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '  ', text, flags=re.MULTILINE)
    
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Clean up emojis and special symbols
    emoji_map = {
        '✅': '[VERIFIED] ',
        '⚠️': '[PARTIALLY VERIFIED] ',
        '❌': '[NOT VERIFIED] ',
        'ℹ️': '[INFO] ',
        '🟢': '[OK] ',
        '🟡': '[WARNING] ',
        '🔴': '[ISSUE] ',
    }
    
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    
    # Remove any remaining emojis/unicode symbols that might not render
    text = re.sub(r'[^\x00-\x7F\u00A0-\u00FF]+', '', text)
    
    return text

def parse_ai_report_sections(ai_report):
    """
    Parse the AI report into structured sections for better PDF formatting.
    """
    import re
    
    sections = {}
    current_section = "Introduction"
    current_content = []
    
    lines = ai_report.split('\n')
    
    for line in lines:
        # Check if line is a section header (starts with number or **TITLE**)
        if re.match(r'^\*?\*?(\d+\.|\*\*[A-Z\s]+\*\*)', line.strip()):
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Extract section name
            section_name = re.sub(r'^\*?\*?(\d+\.\s*|\*\*)', '', line.strip())
            section_name = section_name.replace('**', '').strip()
            if section_name:
                current_section = section_name
            current_content = []
        else:
            if line.strip():
                current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def get_gemini_report(description, image_data_list, category):
    """
    Generates a comprehensive AI report from Gemini API based on the description and multiple images.
    """
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        
        # Convert all images
        import PIL.Image
        images = []
        for image_data in image_data_list:
            image = PIL.Image.open(BytesIO(image_data))
            images.append(image)
        
        # Enhanced prompt for more accurate analysis with multiple images
        prompt = f"""You are a certified construction site inspector with expertise in civil engineering, quality assurance, and project management. Your role is to conduct a thorough, objective, and professional analysis of construction work progress.

**PROJECT CONTEXT:**
- Work Category: {category}
- Number of Images Submitted: {len(images)}
- Engineer's Reported Work: {description}

**ANALYSIS INSTRUCTIONS:**
Examine all {len(images)} image(s) systematically. Cross-reference visual evidence with the engineer's description. Provide factual, evidence-based observations.

**REQUIRED REPORT STRUCTURE:**

**1. VERIFICATION STATUS**
State ONE of the following based on visual evidence:
- ✅ VERIFIED: Visual evidence fully confirms the described work
- ⚠️ PARTIALLY VERIFIED: Some aspects confirmed, discrepancies noted
- ❌ NOT VERIFIED: Visual evidence contradicts or does not support description
- ℹ️ INSUFFICIENT DATA: Images quality/angles inadequate for verification

**2. VISUAL EVIDENCE ANALYSIS**
- Document what is clearly visible in each image
- Specify materials, equipment, and work completed observed
- Note image quality, lighting, and coverage adequacy
- Identify what cannot be verified from provided images
- Compare visual findings with engineer's description point-by-point

**3. TECHNICAL QUALITY ASSESSMENT**
- **Workmanship Rating:** [Excellent/Good/Adequate/Poor/Cannot Assess]
- **Justification:** Specific observations supporting the rating
- **Materials & Specifications:** Visible materials and their apparent condition
- **Defects/Issues:** Any visible defects, damage, or non-conformance
- **Industry Standards:** Compliance with standard construction practices for {category}

**4. SAFETY & COMPLIANCE EVALUATION**
- **PPE (Personal Protective Equipment):** What safety gear is visible/absent
- **Site Safety Measures:** Barriers, signage, fall protection, scaffolding safety
- **Hazard Identification:** List any visible safety hazards or risks
- **Housekeeping:** Site cleanliness, material storage, waste management
- **Compliance Level:** [High/Medium/Low/Cannot Assess] with rationale

**5. REGULATORY & CODE COMPLIANCE**
- **Building Codes:** Apparent adherence to standard construction codes for {category}
- **Specification Compliance:** Does work appear to meet typical specifications
- **Documentation Concerns:** Any work requiring additional verification or documentation
- **Non-Compliance Issues:** List any observed code violations or concerns

**6. PROFESSIONAL RECOMMENDATIONS**
- **Immediate Actions Required:** Critical issues needing urgent attention
- **Quality Improvements:** Suggestions for better workmanship
- **Additional Documentation Needed:** Photos/tests/inspections recommended
- **Follow-up Inspections:** Areas requiring subsequent verification
- **Risk Mitigation:** Steps to address identified safety/quality concerns

**7. PROGRESS QUANTIFICATION**
- **Estimated Completion:** [0-100]% for this specific work phase
- **Basis for Estimate:** Explain how you arrived at this percentage
- **Work Remaining:** Describe what is left to complete this phase
- **Timeline Assessment:** Is work progressing as expected for {category}?

**REPORTING STANDARDS:**
- Be objective and evidence-based; avoid assumptions
- Use precise construction terminology
- Cite specific image evidence for all claims
- Clearly distinguish between observed facts and professional opinions
- Highlight both strengths and areas for improvement
- Prioritize safety-critical observations

Provide your analysis now, following this exact structure."""

        # Prepare content with all images
        content = [prompt] + images
        response = model.generate_content(content)
        
        # Extract verification status from response
        response_text = response.text
        if "✅ VERIFIED" in response_text or "VERIFIED: Work matches" in response_text:
            status = "Verified"
        elif "⚠️ PARTIALLY VERIFIED" in response_text or "PARTIALLY VERIFIED" in response_text:
            status = "Partially Verified"
        elif "❌ NOT VERIFIED" in response_text or "NOT VERIFIED" in response_text:
            status = "Not Verified"
        else:
            status = "Needs Review"
        
        return response_text, status
        
    except Exception as e:
        return f"Error generating AI report: {e}", "Error"

def get_ordinal_suffix(n):
    """Helper function to get ordinal suffix (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return suffix

def generate_floor_options(num_basements, num_floors, has_roof):
    """Generate dynamic floor options based on site configuration"""
    floor_options = []
    
    # Add basement levels
    for i in range(num_basements, 0, -1):
        floor_options.append(f"Basement {i}")
    
    # Add ground floor
    floor_options.append("Ground Floor")
    
    # Add upper floors
    for i in range(1, num_floors + 1):
        floor_options.append(f"{i}{get_ordinal_suffix(i)} Floor")
    
    # Add roof/terrace if applicable
    if has_roof:
        floor_options.append("Roof/Terrace")
    
    # Add "All Floors" option
    floor_options.append("All Floors")
    
    return floor_options

def show():
    st.title("👷 Site Engineer Dashboard")
    
    # Site selection
    sites = get_sites()
    if not sites:
        st.warning("⚠️ No construction sites available. Please contact your administrator to add sites.")
        return
    
    site_options = {f"{site[1]} - {site[2]}": site[0] for site in sites}
    selected_site_label = st.selectbox("🏗️ Select Construction Site", list(site_options.keys()))
    site_id = site_options[selected_site_label]
    
    # Get site details
    site_details = get_site_by_id(site_id)
    
    # Extract floor configuration with backward compatibility
    num_basements = site_details[6] if len(site_details) > 6 else 0
    num_floors = site_details[7] if len(site_details) > 7 else 10
    has_roof = site_details[8] if len(site_details) > 8 else 1
    
    # Generate dynamic floor list
    floor_options = generate_floor_options(num_basements, num_floors, has_roof)
    
    # Tabs for different functions
    tab1, tab2, tab3 = st.tabs(["📤 Upload Progress", "📊 View Progress History", "📈 Analytics & Visualizations"])
    
    with tab1:
        st.header("Upload Progress Update")
        
        with st.form("progress_form", clear_on_submit=True):
            # Main section
            st.subheader("📋 Basic Information")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                category = st.selectbox(
                    "Work Category *",
                    ["Foundation Work", "Structural Work", "Masonry", "Electrical Work", 
                     "Plumbing", "Finishing Work", "HVAC", "Landscaping", "Other"]
                )
                description = st.text_area(
                    "Detailed Description of Work Progress *",
                    placeholder="Describe the work completed, materials used, any challenges faced...",
                    height=100
                )
            
            with col2:
                progress_percentage = st.slider("Overall Progress Percentage", 0, 100, 0, 5)
                st.info(f"**Current Progress:** {progress_percentage}%")
            
            # Floor-wise Progress Section
            st.subheader("🏢 Floor-wise Progress Details")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                floor_number = st.selectbox(
                    "Floor/Level *",
                    floor_options,
                    help=f"Building has {num_basements} basement(s), ground floor, {num_floors} floor(s)" + 
                         (" and roof/terrace" if has_roof else "")
                )
            
            with col2:
                work_phase = st.selectbox(
                    "Work Phase",
                    ["Not Started", "In Progress", "Completed", "Under Review", "Rework Required"]
                )
            
            with col3:
                floor_progress = st.slider("Floor Progress %", 0, 100, 0, 5)
            
            # Detailed Work Checklist
            st.subheader("✅ Work Type Checklist")
            st.markdown("*Select all work types being carried out on this floor:*")
            
            col1, col2, col3 = st.columns(3)
            
            work_checklist = {}
            
            with col1:
                st.markdown("**🏗️ Core Construction**")
                work_checklist['Structural Work'] = st.checkbox("Structural Work", help="Columns, beams, slabs")
                work_checklist['Masonry Work'] = st.checkbox("Masonry Work", help="Block work, walls")
                work_checklist['Plastering'] = st.checkbox("Plastering", help="Wall and ceiling plastering")
            
            with col2:
                st.markdown("**🔧 MEP Works**")
                work_checklist['Plumbing Work'] = st.checkbox("Plumbing Work", help="Water supply, drainage")
                work_checklist['Electrical Work'] = st.checkbox("Electrical Work", help="Wiring, conduits, fixtures")
                work_checklist['HVAC Work'] = st.checkbox("HVAC Work", help="AC ducts, vents")
            
            with col3:
                st.markdown("**🎨 Finishing Works**")
                work_checklist['Waterproofing'] = st.checkbox("Waterproofing", help="Bathroom/terrace waterproofing")
                work_checklist['Toilet Finishes'] = st.checkbox("Toilet Finishes", help="Tiles, fixtures, fittings")
                work_checklist['Lift Lobby Finishes'] = st.checkbox("Lift Lobby Finishes", help="Flooring, walls, ceiling")
                work_checklist['Painting'] = st.checkbox("Painting", help="Wall painting, finishes")
            
            # Additional work details
            selected_works = [work for work, checked in work_checklist.items() if checked]
            
            if selected_works:
                st.markdown("---")
                st.subheader("� Work Status Details")
                
                work_status_details = {}
                for work in selected_works:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**{work}**")
                    with col2:
                        status = st.selectbox(
                            f"Status",
                            ["Started", "50% Complete", "75% Complete", "Completed", "Pending"],
                            key=f"status_{work}"
                        )
                        work_status_details[work] = status
            
            # Image Upload Section
            st.subheader("�📸 Progress Photos")
            uploaded_files = st.file_uploader(
                "Upload Progress Photos (Multiple allowed) *",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                help="Upload multiple clear photos showing different angles of the completed work"
            )
            
            if uploaded_files:
                st.write(f"**{len(uploaded_files)} image(s) selected**")
                # Show previews in a grid
                cols = st.columns(min(len(uploaded_files), 3))
                for idx, file in enumerate(uploaded_files):
                    with cols[idx % 3]:
                        st.image(file, caption=f"Image {idx+1}", use_container_width=True)
            
            submitted = st.form_submit_button("🚀 Submit Progress Update", use_container_width=True)
            
            if submitted:
                if not uploaded_files or not description or not category:
                    st.error("⚠️ Please fill in all required fields and upload at least one image.")
                else:
                    # Collect all image data
                    image_data_list = [file.getvalue() for file in uploaded_files]
                    # Store all images as a combined blob
                    import pickle
                    combined_image_data = pickle.dumps(image_data_list)
                    
                    # Build enhanced description with floor-wise details
                    enhanced_description = f"{description}\n\n"
                    enhanced_description += f"--- FLOOR-WISE DETAILS ---\n"
                    enhanced_description += f"Floor: {floor_number}\n"
                    enhanced_description += f"Work Phase: {work_phase}\n"
                    enhanced_description += f"Floor Progress: {floor_progress}%\n\n"
                    
                    if selected_works:
                        enhanced_description += f"Work Types Being Carried Out:\n"
                        for work in selected_works:
                            status = work_status_details.get(work, "N/A")
                            enhanced_description += f"  - {work}: {status}\n"
                    
                    with st.spinner(f"🤖 AI is analyzing {len(uploaded_files)} image(s)... This may take a moment."):
                        ai_report, verification_status = get_gemini_report(enhanced_description, image_data_list, category)
                    
                    # Display AI analysis
                    st.success("✅ AI Analysis Complete!")
                    
                    # Verification status badge
                    if verification_status == "Verified":
                        st.success(f"✅ **Status:** {verification_status}")
                    elif verification_status == "Partially Verified":
                        st.warning(f"⚠️ **Status:** {verification_status}")
                    elif verification_status == "Not Verified":
                        st.error(f"❌ **Status:** {verification_status}")
                    else:
                        st.info(f"ℹ️ **Status:** {verification_status}")
                    
                    with st.expander("📋 View Full AI Analysis Report", expanded=True):
                        st.markdown(ai_report)
                    
                    # Save to database
                    user_id = st.session_state.user_id
                    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    add_progress(site_id, user_id, date, category, description, combined_image_data, 
                               ai_report, verification_status, progress_percentage)
                    
                    st.success("✅ Progress update saved successfully!")
                    st.balloons()
    
    with tab2:
        st.header("Progress History")
        
        progress_entries = get_progress_by_site(site_id)
        
        if not progress_entries:
            st.info("📭 No progress updates found for this site yet. Be the first to add one!")
        else:
            st.success(f"📊 Total Updates: {len(progress_entries)}")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                filter_category = st.selectbox("Filter by Category", 
                    ["All"] + ["Foundation Work", "Structural Work", "Masonry", "Electrical Work", 
                               "Plumbing", "Finishing Work", "HVAC", "Landscaping", "Other"])
            with col2:
                filter_status = st.selectbox("Filter by Verification", 
                    ["All", "Verified", "Partially Verified", "Not Verified", "Needs Review"])
            
            for entry in progress_entries:
                entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
                
                # Apply filters
                if filter_category != "All" and category != filter_category:
                    continue
                if filter_status != "All" and verification_status != filter_status:
                    continue
                
                # Status color coding
                if verification_status == "Verified":
                    status_color = "🟢"
                elif verification_status == "Partially Verified":
                    status_color = "🟡"
                elif verification_status == "Not Verified":
                    status_color = "🔴"
                else:
                    status_color = "⚪"
                
                with st.expander(f"{status_color} **{date}** | {category} | by {username} | {progress_pct}% Complete"):
                    # Try to load multiple images
                    import pickle
                    try:
                        image_list = pickle.loads(image)
                        num_images = len(image_list)
                    except:
                        # Fallback for old single-image format
                        image_list = [image]
                        num_images = 1
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        if num_images == 1:
                            st.image(BytesIO(image_list[0]), caption="Progress Photo", use_container_width=True)
                        else:
                            st.write(f"**📸 {num_images} Images:**")
                            for idx, img_data in enumerate(image_list):
                                st.image(BytesIO(img_data), caption=f"Image {idx+1}", use_container_width=True)
                    
                    with col2:
                        st.markdown(f"**📅 Date:** {date}")
                        st.markdown(f"**👤 Engineer:** {username}")
                        st.markdown(f"**📂 Category:** {category}")
                        st.markdown(f"**📊 Progress:** {progress_pct}%")
                        st.markdown(f"**Status:** {verification_status}")
                        st.markdown(f"**📸 Images:** {num_images}")
                    
                    st.markdown("**📝 Description:**")
                    st.write(description)
                    
                    st.markdown("**🤖 AI Analysis Report:**")
                    st.markdown(ai_report)
                    
                    # Generate PDF report
                    st.markdown("---")
                    
                    # Create professional PDF with better formatting
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    
                    # Title
                    pdf.set_font("Arial", 'B', 18)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 12, "CONSTRUCTION PROGRESS REPORT", ln=True, align='C')
                    pdf.ln(3)
                    
                    # Add a line separator
                    pdf.set_draw_color(0, 102, 204)
                    pdf.set_line_width(0.5)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(8)
                    
                    # Project Information Section
                    pdf.set_font("Arial", 'B', 14)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.cell(0, 8, "PROJECT INFORMATION", ln=True, fill=True)
                    pdf.ln(2)
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(0, 0, 0)
                    
                    info_items = [
                        ("Site Name:", site_details[1]),
                        ("Location:", site_details[2]),
                        ("Report Date:", date),
                        ("Engineer:", username),
                        ("Work Category:", category),
                        ("Progress Percentage:", f"{progress_pct}%"),
                        ("Verification Status:", verification_status),
                        ("Images Submitted:", str(num_images))
                    ]
                    
                    for label, value in info_items:
                        pdf.set_font("Arial", 'B', 9)
                        pdf.cell(45, 6, label, 0, 0)
                        pdf.set_font("Arial", '', 9)
                        pdf.multi_cell(0, 6, value)
                    
                    pdf.ln(5)
                    
                    # Floor-wise Details Section (NEW)
                    if "--- FLOOR-WISE DETAILS ---" in description:
                        pdf.set_font("Arial", 'B', 14)
                        pdf.set_fill_color(240, 240, 240)
                        pdf.cell(0, 8, "FLOOR-WISE DETAILS", ln=True, fill=True)
                        pdf.ln(2)
                        
                        parts = description.split("--- FLOOR-WISE DETAILS ---")
                        if len(parts) > 1:
                            floor_section = parts[1]
                            
                            # Parse floor details
                            floor_info = {}
                            if "Floor: " in floor_section:
                                floor_line = [line for line in floor_section.split('\n') if "Floor: " in line]
                                if floor_line:
                                    floor_info['Floor'] = floor_line[0].replace("Floor: ", "").strip()
                            
                            if "Work Phase: " in floor_section:
                                phase_line = [line for line in floor_section.split('\n') if "Work Phase: " in line]
                                if phase_line:
                                    floor_info['Work Phase'] = phase_line[0].replace("Work Phase: ", "").strip()
                            
                            if "Floor Progress: " in floor_section:
                                prog_line = [line for line in floor_section.split('\n') if "Floor Progress: " in line]
                                if prog_line:
                                    floor_info['Floor Progress'] = prog_line[0].replace("Floor Progress: ", "").strip()
                            
                            # Display floor info
                            pdf.set_font("Arial", 'B', 9)
                            for label, value in floor_info.items():
                                pdf.cell(45, 6, f"{label}:", 0, 0)
                                pdf.set_font("Arial", '', 9)
                                pdf.cell(0, 6, value, 0, 1)
                                pdf.set_font("Arial", 'B', 9)
                            
                            # Work types carried out
                            if "Work Types Being Carried Out:" in floor_section:
                                pdf.ln(3)
                                pdf.set_font("Arial", 'B', 10)
                                pdf.cell(0, 6, "Work Types Being Carried Out:", ln=True)
                                pdf.set_font("Arial", '', 9)
                                
                                work_section = floor_section.split("Work Types Being Carried Out:")[1]
                                work_lines = [line.strip() for line in work_section.split('\n') if line.strip().startswith('-')]
                                
                                for line in work_lines:
                                    clean_line = line.encode('ascii', 'ignore').decode('ascii')
                                    pdf.cell(10, 5, "", 0, 0)  # Indent
                                    pdf.multi_cell(0, 5, clean_line)
                        
                        pdf.ln(5)
                    
                    # Work Description Section
                    pdf.set_font("Arial", 'B', 14)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.cell(0, 8, "WORK DESCRIPTION", ln=True, fill=True)
                    pdf.ln(2)
                    
                    pdf.set_font("Arial", '', 9)
                    # Extract only the main description (before floor details)
                    main_description = description.split("--- FLOOR-WISE DETAILS ---")[0].strip() if "--- FLOOR-WISE DETAILS ---" in description else description
                    clean_description = clean_markdown_for_pdf(main_description)
                    try:
                        clean_description_encoded = clean_description.encode('latin-1', 'replace').decode('latin-1')
                    except:
                        clean_description_encoded = clean_description.encode('ascii', 'ignore').decode('ascii')
                    pdf.multi_cell(0, 5, clean_description_encoded)
                    pdf.ln(5)
                    
                    # AI Analysis Report Section
                    pdf.set_font("Arial", 'B', 14)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.cell(0, 8, "AI VERIFICATION & ANALYSIS REPORT", ln=True, fill=True)
                    pdf.ln(2)
                    
                    # Parse the AI report into sections
                    sections = parse_ai_report_sections(ai_report)
                    
                    for section_name, section_content in sections.items():
                        # Section header
                        pdf.set_font("Arial", 'B', 11)
                        pdf.set_text_color(0, 102, 204)
                        section_title = clean_markdown_for_pdf(section_name)[:80]  # Limit length
                        try:
                            section_title_encoded = section_title.encode('latin-1', 'replace').decode('latin-1')
                        except:
                            section_title_encoded = section_title.encode('ascii', 'ignore').decode('ascii')
                        pdf.cell(0, 6, section_title_encoded, ln=True)
                        
                        # Section content
                        pdf.set_font("Arial", '', 9)
                        pdf.set_text_color(0, 0, 0)
                        clean_content = clean_markdown_for_pdf(section_content)
                        try:
                            clean_content_encoded = clean_content.encode('latin-1', 'replace').decode('latin-1')
                        except:
                            clean_content_encoded = clean_content.encode('ascii', 'ignore').decode('ascii')
                        
                        # Split long content for better readability
                        pdf.multi_cell(0, 5, clean_content_encoded)
                        pdf.ln(3)
                    
                    # Footer
                    pdf.ln(5)
                    pdf.set_draw_color(0, 102, 204)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(2)
                    pdf.set_font("Arial", 'I', 8)
                    pdf.set_text_color(128, 128, 128)
                    pdf.cell(0, 5, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | AI-Powered Construction Monitoring System", ln=True, align='C')
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_output,
                        file_name=f"progress_report_{category}_{date.replace(':', '-')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
    
    with tab3:
        st.header("📈 Analytics & Visualizations")
        
        progress_entries = get_progress_by_site(site_id)
        
        if not progress_entries or len(progress_entries) == 0:
            st.info("📭 No progress data available yet. Add progress updates to see visualizations!")
        else:
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Updates", len(progress_entries))
            
            with col2:
                latest_progress = progress_entries[0][8] if progress_entries else 0
                st.metric("Latest Progress", f"{latest_progress}%")
            
            with col3:
                verified_count = sum(1 for e in progress_entries if e[7] == "Verified")
                st.metric("Verified Updates", verified_count)
            
            with col4:
                categories_count = len(set(e[3] for e in progress_entries))
                st.metric("Work Categories", categories_count)
            
            st.markdown("---")
            
            # 1. Progress Timeline Chart
            st.subheader("📊 Progress Timeline")
            timeline_data = get_progress_timeline(site_id)
            
            if timeline_data:
                df_timeline = pd.DataFrame(timeline_data, columns=['Date', 'Progress %', 'Category'])
                
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=df_timeline['Date'],
                    y=df_timeline['Progress %'],
                    mode='lines+markers',
                    name='Progress',
                    line=dict(color='#0066cc', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Progress:</b> %{y}%<extra></extra>'
                ))
                
                fig_timeline.update_layout(
                    title="Project Progress Over Time",
                    xaxis_title="Date",
                    yaxis_title="Progress Percentage (%)",
                    hovermode='x unified',
                    height=400,
                    yaxis=dict(range=[0, 100])
                )
                
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Row with two charts
            col1, col2 = st.columns(2)
            
            with col1:
                # 2. Category Breakdown Pie Chart
                st.subheader("📂 Work by Category")
                category_data = get_category_breakdown(site_id)
                
                if category_data:
                    df_category = pd.DataFrame(category_data, columns=['Category', 'Count'])
                    
                    fig_category = px.pie(
                        df_category,
                        values='Count',
                        names='Category',
                        title='Distribution of Work Categories',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_category.update_traces(textposition='inside', textinfo='percent+label')
                    fig_category.update_layout(height=400)
                    
                    st.plotly_chart(fig_category, use_container_width=True)
            
            with col2:
                # 3. Verification Status Chart
                st.subheader("✅ Verification Status")
                verification_data = get_verification_breakdown(site_id)
                
                if verification_data:
                    df_verification = pd.DataFrame(verification_data, columns=['Status', 'Count'])
                    
                    # Color mapping for status
                    color_map = {
                        'Verified': '#28a745',
                        'Partially Verified': '#ffc107',
                        'Not Verified': '#dc3545',
                        'Needs Review': '#6c757d'
                    }
                    colors = [color_map.get(status, '#6c757d') for status in df_verification['Status']]
                    
                    fig_verification = go.Figure(data=[
                        go.Bar(
                            x=df_verification['Status'],
                            y=df_verification['Count'],
                            marker_color=colors,
                            text=df_verification['Count'],
                            textposition='auto',
                        )
                    ])
                    
                    fig_verification.update_layout(
                        title='AI Verification Status Distribution',
                        xaxis_title='Status',
                        yaxis_title='Number of Updates',
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_verification, use_container_width=True)
            
            # 4. Monthly Activity Chart
            st.subheader("📅 Monthly Activity & Progress")
            monthly_data = get_monthly_progress(site_id)
            
            if monthly_data:
                df_monthly = pd.DataFrame(monthly_data, columns=['Month', 'Updates', 'Avg Progress'])
                
                fig_monthly = go.Figure()
                
                # Bar chart for number of updates
                fig_monthly.add_trace(go.Bar(
                    x=df_monthly['Month'],
                    y=df_monthly['Updates'],
                    name='Number of Updates',
                    marker_color='#0066cc',
                    yaxis='y',
                    offsetgroup=1
                ))
                
                # Line chart for average progress
                fig_monthly.add_trace(go.Scatter(
                    x=df_monthly['Month'],
                    y=df_monthly['Avg Progress'],
                    name='Avg Progress %',
                    line=dict(color='#ff9800', width=3),
                    marker=dict(size=8),
                    yaxis='y2'
                ))
                
                fig_monthly.update_layout(
                    title='Monthly Updates and Average Progress',
                    xaxis_title='Month',
                    yaxis=dict(
                        title='Number of Updates',
                        side='left'
                    ),
                    yaxis2=dict(
                        title='Average Progress (%)',
                        overlaying='y',
                        side='right',
                        range=[0, 100]
                    ),
                    hovermode='x unified',
                    height=400,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            # 5. Category Progress Breakdown
            st.subheader("📊 Progress by Category")
            
            # Get progress data grouped by category
            category_progress = {}
            for entry in progress_entries:
                category = entry[3]
                progress_pct = entry[8]
                if category not in category_progress:
                    category_progress[category] = []
                category_progress[category].append(progress_pct)
            
            if category_progress:
                categories = list(category_progress.keys())
                avg_progress = [sum(progs) / len(progs) for progs in category_progress.values()]
                max_progress = [max(progs) for progs in category_progress.values()]
                
                fig_cat_progress = go.Figure()
                
                fig_cat_progress.add_trace(go.Bar(
                    name='Average Progress',
                    x=categories,
                    y=avg_progress,
                    marker_color='#0066cc'
                ))
                
                fig_cat_progress.add_trace(go.Bar(
                    name='Maximum Progress',
                    x=categories,
                    y=max_progress,
                    marker_color='#28a745'
                ))
                
                fig_cat_progress.update_layout(
                    title='Progress Percentage by Work Category',
                    xaxis_title='Category',
                    yaxis_title='Progress (%)',
                    barmode='group',
                    height=400,
                    yaxis=dict(range=[0, 100])
                )
                
                st.plotly_chart(fig_cat_progress, use_container_width=True)
            
            # 6. Floor-wise Progress Analysis
            st.markdown("---")
            st.subheader("🏢 Floor-wise Progress Analysis")
            
            floor_data = get_floor_wise_progress(site_id)
            
            if floor_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Floor progress bar chart
                    df_floors = pd.DataFrame(floor_data, columns=['Floor', 'Updates', 'Avg Progress %', 'Latest Phase', 'Work Types Count'])
                    
                    fig_floor_progress = go.Figure()
                    
                    fig_floor_progress.add_trace(go.Bar(
                        x=df_floors['Floor'],
                        y=df_floors['Avg Progress %'],
                        marker_color='#17a2b8',
                        text=df_floors['Avg Progress %'].round(1),
                        textposition='auto',
                        hovertemplate='<b>%{x}</b><br>Avg Progress: %{y:.1f}%<br>Updates: %{customdata[0]}<extra></extra>',
                        customdata=df_floors[['Updates']].values
                    ))
                    
                    fig_floor_progress.update_layout(
                        title='Average Progress by Floor',
                        xaxis_title='Floor',
                        yaxis_title='Progress (%)',
                        height=400,
                        yaxis=dict(range=[0, 100]),
                        xaxis={'categoryorder': 'total descending'}
                    )
                    
                    st.plotly_chart(fig_floor_progress, use_container_width=True)
                
                with col2:
                    # Updates count by floor
                    fig_floor_updates = go.Figure()
                    
                    fig_floor_updates.add_trace(go.Bar(
                        x=df_floors['Floor'],
                        y=df_floors['Updates'],
                        marker_color='#6f42c1',
                        text=df_floors['Updates'],
                        textposition='auto',
                        hovertemplate='<b>%{x}</b><br>Total Updates: %{y}<br>Work Types: %{customdata[0]}<extra></extra>',
                        customdata=df_floors[['Work Types Count']].values
                    ))
                    
                    fig_floor_updates.update_layout(
                        title='Number of Updates by Floor',
                        xaxis_title='Floor',
                        yaxis_title='Number of Updates',
                        height=400,
                        xaxis={'categoryorder': 'total descending'}
                    )
                    
                    st.plotly_chart(fig_floor_updates, use_container_width=True)
                
                # Floor status table
                st.markdown("**📋 Detailed Floor Status:**")
                display_df = df_floors.copy()
                display_df['Avg Progress %'] = display_df['Avg Progress %'].round(1).astype(str) + '%'
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Floor": st.column_config.TextColumn("Floor/Level", width="medium"),
                        "Updates": st.column_config.NumberColumn("Total Updates", width="small"),
                        "Avg Progress %": st.column_config.TextColumn("Avg Progress", width="small"),
                        "Latest Phase": st.column_config.TextColumn("Current Phase", width="medium"),
                        "Work Types Count": st.column_config.NumberColumn("Work Types", width="small")
                    }
                )
            else:
                st.info("No floor-wise data available yet. Upload progress updates with floor details to see analytics.")
            
            # 7. Work Type Analysis Across All Floors
            st.markdown("---")
            st.subheader("🔧 Work Type Analysis")
            
            work_type_data = get_work_type_breakdown(site_id)
            
            if work_type_data:
                df_work = pd.DataFrame(work_type_data, columns=['Work Type', 'Total Instances', 'Completed', 'In Progress'])
                
                # Stacked bar chart
                fig_work = go.Figure()
                
                fig_work.add_trace(go.Bar(
                    name='Completed',
                    x=df_work['Work Type'],
                    y=df_work['Completed'],
                    marker_color='#28a745'
                ))
                
                fig_work.add_trace(go.Bar(
                    name='In Progress',
                    x=df_work['Work Type'],
                    y=df_work['In Progress'],
                    marker_color='#ffc107'
                ))
                
                fig_work.add_trace(go.Bar(
                    name='Other',
                    x=df_work['Work Type'],
                    y=df_work['Total Instances'] - df_work['Completed'] - df_work['In Progress'],
                    marker_color='#6c757d'
                ))
                
                fig_work.update_layout(
                    title='Work Type Status Distribution',
                    xaxis_title='Work Type',
                    yaxis_title='Number of Instances',
                    barmode='stack',
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_work, use_container_width=True)
                
                # Work type summary table
                st.markdown("**📊 Work Type Summary:**")
                df_work['Completion Rate'] = ((df_work['Completed'] / df_work['Total Instances']) * 100).round(1).astype(str) + '%'
                st.dataframe(
                    df_work,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Work Type": st.column_config.TextColumn("Work Type", width="medium"),
                        "Total Instances": st.column_config.NumberColumn("Total", width="small"),
                        "Completed": st.column_config.NumberColumn("Completed", width="small"),
                        "In Progress": st.column_config.NumberColumn("In Progress", width="small"),
                        "Completion Rate": st.column_config.TextColumn("Completion Rate", width="small")
                    }
                )
            else:
                st.info("No work type data available yet. Upload progress updates with work type details to see analytics.")
            
            # 8. Download Monthly Progress Report
            st.markdown("---")
            st.subheader("📥 Download Monthly Progress Report")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("Generate a comprehensive monthly progress report with all updates in table format.")
                
                # Allow user to select month range
                if progress_entries:
                    all_dates = [entry[1] for entry in progress_entries]
                    min_date = min(all_dates).split()[0] if all_dates else datetime.date.today().strftime("%Y-%m-%d")
                    max_date = max(all_dates).split()[0] if all_dates else datetime.date.today().strftime("%Y-%m-%d")
                    
                    st.info(f"Reports available from {min_date} to {max_date}")
            
            with col2:
                report_format = st.selectbox("Report Format", ["PDF Table", "Excel (CSV)"])
            
            if st.button("📊 Generate Monthly Report", use_container_width=True):
                if not progress_entries:
                    st.error("No progress data available to generate report.")
                else:
                    with st.spinner("Generating monthly progress report..."):
                        if report_format == "PDF Table":
                            # Generate PDF with table
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_auto_page_break(auto=True, margin=15)
                            
                            # Title
                            pdf.set_font("Arial", 'B', 16)
                            pdf.cell(0, 10, "MONTHLY PROGRESS SUMMARY REPORT", ln=True, align='C')
                            pdf.ln(2)
                            
                            # Site info
                            pdf.set_font("Arial", 'B', 11)
                            pdf.cell(0, 8, f"Site: {site_details[1]}", ln=True)
                            pdf.set_font("Arial", '', 10)
                            pdf.cell(0, 6, f"Location: {site_details[2]}", ln=True)
                            pdf.cell(0, 6, f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
                            pdf.ln(5)
                            
                            # Group entries by month
                            from collections import defaultdict
                            monthly_groups = defaultdict(list)
                            
                            for entry in progress_entries:
                                entry_date = entry[1].split()[0]  # Get date part
                                month_key = entry_date[:7]  # YYYY-MM
                                monthly_groups[month_key].append(entry)
                            
                            # Process each month
                            for month in sorted(monthly_groups.keys(), reverse=True):
                                month_entries = monthly_groups[month]
                                
                                # Month header
                                pdf.set_font("Arial", 'B', 12)
                                pdf.set_fill_color(0, 102, 204)
                                pdf.set_text_color(255, 255, 255)
                                pdf.cell(0, 8, f"  {month} ({len(month_entries)} updates)", ln=True, fill=True)
                                pdf.set_text_color(0, 0, 0)
                                pdf.ln(2)
                                
                                # Table header
                                pdf.set_font("Arial", 'B', 7)
                                pdf.set_fill_color(240, 240, 240)
                                pdf.cell(22, 7, "Date", 1, 0, 'C', True)
                                pdf.cell(25, 7, "Category", 1, 0, 'C', True)
                                pdf.cell(20, 7, "Engineer", 1, 0, 'C', True)
                                pdf.cell(18, 7, "Floor", 1, 0, 'C', True)
                                pdf.cell(15, 7, "Floor %", 1, 0, 'C', True)
                                pdf.cell(12, 7, "Prog%", 1, 0, 'C', True)
                                pdf.cell(25, 7, "Status", 1, 0, 'C', True)
                                pdf.cell(53, 7, "Work Types", 1, 1, 'C', True)
                                
                                # Table rows
                                pdf.set_font("Arial", '', 6.5)
                                for entry in month_entries:
                                    entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
                                    
                                    # Parse floor-wise details from description
                                    floor_info = "N/A"
                                    floor_progress = "N/A"
                                    work_types = ""
                                    
                                    if "--- FLOOR-WISE DETAILS ---" in description:
                                        parts = description.split("--- FLOOR-WISE DETAILS ---")
                                        if len(parts) > 1:
                                            floor_section = parts[1]
                                            
                                            # Extract floor
                                            if "Floor: " in floor_section:
                                                floor_line = [line for line in floor_section.split('\n') if "Floor: " in line]
                                                if floor_line:
                                                    floor_info = floor_line[0].replace("Floor: ", "").strip()
                                            
                                            # Extract floor progress
                                            if "Floor Progress: " in floor_section:
                                                prog_line = [line for line in floor_section.split('\n') if "Floor Progress: " in line]
                                                if prog_line:
                                                    floor_progress = prog_line[0].replace("Floor Progress: ", "").strip()
                                            
                                            # Extract work types
                                            if "Work Types Being Carried Out:" in floor_section:
                                                work_section = floor_section.split("Work Types Being Carried Out:")[1]
                                                work_lines = [line.strip() for line in work_section.split('\n') if line.strip().startswith('-')]
                                                work_types_list = []
                                                for line in work_lines[:3]:  # Limit to 3 work types for space
                                                    # Extract work name (before colon)
                                                    work_name = line.split(':')[0].replace('-', '').strip()
                                                    work_types_list.append(work_name)
                                                work_types = ', '.join(work_types_list)
                                                if len(work_lines) > 3:
                                                    work_types += f" +{len(work_lines)-3} more"
                                    
                                    # Truncate long text
                                    category_short = (category[:15] + '..') if len(category) > 15 else category
                                    username_short = (username[:10] + '..') if len(username) > 10 else username
                                    status_short = (verification_status[:15] + '..') if len(verification_status) > 15 else verification_status
                                    floor_short = (floor_info[:10] + '..') if len(floor_info) > 10 else floor_info
                                    work_types_short = (work_types[:35] + '...') if len(work_types) > 35 else work_types
                                    
                                    # Clean text for PDF
                                    category_short = category_short.encode('ascii', 'ignore').decode('ascii')
                                    username_short = username_short.encode('ascii', 'ignore').decode('ascii')
                                    status_short = status_short.encode('ascii', 'ignore').decode('ascii')
                                    floor_short = floor_short.encode('ascii', 'ignore').decode('ascii')
                                    work_types_short = work_types_short.encode('ascii', 'ignore').decode('ascii')
                                    
                                    # Calculate row height based on work types length
                                    lines_needed = max(1, (len(work_types_short) // 35) + 1)
                                    row_height = max(7, lines_needed * 3.5)
                                    
                                    # Save current position
                                    x_before = pdf.get_x()
                                    y_before = pdf.get_y()
                                    
                                    # Draw cells
                                    pdf.cell(22, row_height, date.split()[0], 1, 0, 'C')
                                    pdf.cell(25, row_height, category_short, 1, 0, 'C')
                                    pdf.cell(20, row_height, username_short, 1, 0, 'C')
                                    pdf.cell(18, row_height, floor_short, 1, 0, 'C')
                                    pdf.cell(15, row_height, floor_progress, 1, 0, 'C')
                                    pdf.cell(12, row_height, f"{progress_pct}%", 1, 0, 'C')
                                    pdf.cell(25, row_height, status_short, 1, 0, 'C')
                                    
                                    # Work types cell with wrapping
                                    x_work = pdf.get_x()
                                    y_work = pdf.get_y()
                                    
                                    # Draw work types cell border
                                    pdf.rect(x_work, y_work, 53, row_height)
                                    
                                    # Add work types text with multi_cell
                                    pdf.set_xy(x_work + 0.5, y_work + 0.5)
                                    pdf.multi_cell(52, 3.5, work_types_short if work_types_short else "N/A", 0, 'L')
                                    
                                    # Move to next row
                                    pdf.set_xy(x_before, y_work + row_height)
                                
                                # Month summary
                                avg_progress = sum(e[8] for e in month_entries) / len(month_entries)
                                verified_count = sum(1 for e in month_entries if e[7] == "Verified")
                                
                                pdf.ln(2)
                                pdf.set_font("Arial", 'I', 8)
                                pdf.cell(0, 5, f"Month Summary: Avg Progress: {avg_progress:.1f}% | Verified: {verified_count}/{len(month_entries)}", ln=True)
                                pdf.ln(5)
                            
                            # Overall summary
                            pdf.ln(5)
                            pdf.set_font("Arial", 'B', 11)
                            pdf.cell(0, 8, "OVERALL SUMMARY", ln=True)
                            pdf.set_font("Arial", '', 9)
                            pdf.cell(0, 6, f"Total Updates: {len(progress_entries)}", ln=True)
                            pdf.cell(0, 6, f"Average Progress: {sum(e[8] for e in progress_entries) / len(progress_entries):.1f}%", ln=True)
                            pdf.cell(0, 6, f"Verified Updates: {sum(1 for e in progress_entries if e[7] == 'Verified')}", ln=True)
                            
                            # Floor-wise Summary
                            floor_summary_data = get_floor_wise_progress(site_id)
                            if floor_summary_data:
                                pdf.ln(8)
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 8, "FLOOR-WISE PROGRESS SUMMARY", ln=True)
                                pdf.ln(2)
                                
                                # Floor summary table header
                                pdf.set_font("Arial", 'B', 8)
                                pdf.set_fill_color(240, 240, 240)
                                pdf.cell(50, 7, "Floor", 1, 0, 'C', True)
                                pdf.cell(25, 7, "Updates", 1, 0, 'C', True)
                                pdf.cell(30, 7, "Avg Progress", 1, 0, 'C', True)
                                pdf.cell(40, 7, "Latest Phase", 1, 0, 'C', True)
                                pdf.cell(25, 7, "Work Types", 1, 1, 'C', True)
                                
                                # Floor summary table rows
                                pdf.set_font("Arial", '', 8)
                                for floor_row in floor_summary_data:
                                    floor, updates, avg_prog, phase, work_count = floor_row
                                    floor_short = (floor[:30] + '...') if len(floor) > 30 else floor
                                    phase_short = (phase[:25] + '...') if len(phase) > 25 else phase
                                    
                                    pdf.cell(50, 6, floor_short, 1, 0, 'L')
                                    pdf.cell(25, 6, str(updates), 1, 0, 'C')
                                    pdf.cell(30, 6, f"{avg_prog:.1f}%", 1, 0, 'C')
                                    pdf.cell(40, 6, phase_short, 1, 0, 'C')
                                    pdf.cell(25, 6, str(work_count), 1, 1, 'C')
                            
                            # Work Type Summary
                            work_type_summary = get_work_type_breakdown(site_id)
                            if work_type_summary:
                                pdf.ln(8)
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 8, "WORK TYPE SUMMARY", ln=True)
                                pdf.ln(2)
                                
                                # Work type table header
                                pdf.set_font("Arial", 'B', 8)
                                pdf.set_fill_color(240, 240, 240)
                                pdf.cell(70, 7, "Work Type", 1, 0, 'C', True)
                                pdf.cell(30, 7, "Total", 1, 0, 'C', True)
                                pdf.cell(30, 7, "Completed", 1, 0, 'C', True)
                                pdf.cell(30, 7, "In Progress", 1, 0, 'C', True)
                                pdf.cell(30, 7, "Completion %", 1, 1, 'C', True)
                                
                                # Work type table rows
                                pdf.set_font("Arial", '', 8)
                                for work_row in work_type_summary:
                                    work_name, total, completed, in_prog = work_row
                                    completion_rate = (completed / total * 100) if total > 0 else 0
                                    work_short = (work_name[:45] + '...') if len(work_name) > 45 else work_name
                                    
                                    pdf.cell(70, 6, work_short, 1, 0, 'L')
                                    pdf.cell(30, 6, str(total), 1, 0, 'C')
                                    pdf.cell(30, 6, str(completed), 1, 0, 'C')
                                    pdf.cell(30, 6, str(in_prog), 1, 0, 'C')
                                    pdf.cell(30, 6, f"{completion_rate:.1f}%", 1, 1, 'C')
                            
                            pdf_output = pdf.output(dest='S').encode('latin-1')
                            
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_output,
                                file_name=f"monthly_progress_report_{site_details[1].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            
                        else:  # CSV format
                            # Generate CSV
                            import csv
                            from io import StringIO
                            
                            output = StringIO()
                            writer = csv.writer(output)
                            
                            # Header
                            writer.writerow(['Date', 'Category', 'Engineer', 'Floor', 'Floor Progress %', 'Overall Progress %', 
                                           'Verification Status', 'Work Phase', 'Work Types', 'Description Summary', 'AI Report Summary'])
                            
                            # Data rows
                            for entry in progress_entries:
                                entry_id, date, username, category, description, image, ai_report, verification_status, progress_pct = entry
                                
                                # Parse floor-wise details from description
                                floor_info = "N/A"
                                floor_progress = "N/A"
                                work_phase = "N/A"
                                work_types = ""
                                base_description = description
                                
                                if "--- FLOOR-WISE DETAILS ---" in description:
                                    parts = description.split("--- FLOOR-WISE DETAILS ---")
                                    base_description = parts[0].strip()
                                    
                                    if len(parts) > 1:
                                        floor_section = parts[1]
                                        
                                        # Extract floor
                                        if "Floor: " in floor_section:
                                            floor_line = [line for line in floor_section.split('\n') if "Floor: " in line]
                                            if floor_line:
                                                floor_info = floor_line[0].replace("Floor: ", "").strip()
                                        
                                        # Extract work phase
                                        if "Work Phase: " in floor_section:
                                            phase_line = [line for line in floor_section.split('\n') if "Work Phase: " in line]
                                            if phase_line:
                                                work_phase = phase_line[0].replace("Work Phase: ", "").strip()
                                        
                                        # Extract floor progress
                                        if "Floor Progress: " in floor_section:
                                            prog_line = [line for line in floor_section.split('\n') if "Floor Progress: " in line]
                                            if prog_line:
                                                floor_progress = prog_line[0].replace("Floor Progress: ", "").strip()
                                        
                                        # Extract work types
                                        if "Work Types Being Carried Out:" in floor_section:
                                            work_section = floor_section.split("Work Types Being Carried Out:")[1]
                                            work_lines = [line.strip() for line in work_section.split('\n') if line.strip().startswith('-')]
                                            work_types = "; ".join([line.replace('-', '').strip() for line in work_lines])
                                
                                # Get first line of AI report as summary
                                ai_summary = ai_report.split('\n')[0][:150] if ai_report else "N/A"
                                
                                # Truncate description
                                desc_summary = (base_description[:200] + '...') if len(base_description) > 200 else base_description
                                
                                writer.writerow([
                                    date,
                                    category,
                                    username,
                                    floor_info,
                                    floor_progress,
                                    progress_pct,
                                    verification_status,
                                    work_phase,
                                    work_types if work_types else "N/A",
                                    desc_summary,
                                    ai_summary
                                ])
                            
                            csv_data = output.getvalue()
                            
                            st.download_button(
                                label="📥 Download CSV Report",
                                data=csv_data,
                                file_name=f"monthly_progress_report_{site_details[1].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        st.success("✅ Report generated successfully!")
