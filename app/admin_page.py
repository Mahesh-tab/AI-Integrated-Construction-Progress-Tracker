import streamlit as st
from database import (add_site, get_sites, get_all_statistics, get_site_statistics, 
                      update_site_status, get_all_users, get_progress_by_site,
                      get_floor_wise_progress, get_work_type_breakdown)
import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def show():
    st.title("🏢 Admin Dashboard")
    
    # Get overall statistics
    stats = get_all_statistics()
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e0e0e0;">
                <h3 style="color: #0066cc; margin-top: 0; font-size: 0.9rem;">🏗️ Total Sites</h3>
                <h1 style="color: #1f1f1f; margin: 0.5rem 0 0 0; font-size: 2.5rem; border: none; padding: 0;">{stats['total_sites']}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e0e0e0;">
                <h3 style="color: #28a745; margin-top: 0; font-size: 0.9rem;">✅ Active Sites</h3>
                <h1 style="color: #1f1f1f; margin: 0.5rem 0 0 0; font-size: 2.5rem; border: none; padding: 0;">{stats['active_sites']}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e0e0e0;">
                <h3 style="color: #ff9800; margin-top: 0; font-size: 0.9rem;">📊 Total Updates</h3>
                <h1 style="color: #1f1f1f; margin: 0.5rem 0 0 0; font-size: 2.5rem; border: none; padding: 0;">{stats['total_updates']}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Add a quick visualization section
    if stats['total_updates'] > 0:
        st.subheader("📊 Quick Overview")
        
        # Get all sites progress data
        sites = get_sites()
        site_progress_data = []
        
        for site in sites:
            site_id = site[0]
            name = site[1]
            location = site[2]
            description = site[3] if len(site) > 3 else ""
            start_date = site[4] if len(site) > 4 else ""
            status = site[5] if len(site) > 5 else "Active"
            
            site_stats = get_site_statistics(site_id)
            site_progress_data.append({
                'Site': name,
                'Progress': site_stats['latest_progress'],
                'Updates': site_stats['total_updates'],
                'Status': status
            })
        
        if site_progress_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Sites progress comparison
                df_sites = pd.DataFrame(site_progress_data)
                fig_sites = px.bar(
                    df_sites,
                    x='Site',
                    y='Progress',
                    color='Status',
                    title='Progress by Site',
                    color_discrete_map={
                        'Active': '#28a745',
                        'Completed': '#0066cc',
                        'On Hold': '#ffc107',
                        'Cancelled': '#dc3545'
                    }
                )
                fig_sites.update_layout(height=300, yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_sites, use_container_width=True)
            
            with col2:
                # Sites by status
                status_counts = df_sites['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig_status = px.pie(
                    status_counts,
                    values='Count',
                    names='Status',
                    title='Sites by Status',
                    color='Status',
                    color_discrete_map={
                        'Active': '#28a745',
                        'Completed': '#0066cc',
                        'On Hold': '#ffc107',
                        'Cancelled': '#dc3545'
                    }
                )
                fig_status.update_layout(height=300)
                st.plotly_chart(fig_status, use_container_width=True)
    
    st.markdown("---")
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["📍 Site Management", "➕ Add New Site", "👥 User Management"])
    
    with tab1:
        st.header("Construction Sites")
        
        sites = get_sites()
        
        if not sites:
            st.info("No construction sites found. Add your first site using the 'Add New Site' tab.")
        else:
            # Search and filter
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Search sites", placeholder="Search by name or location...")
            with col2:
                status_filter = st.selectbox("Filter by Status", ["All", "Active", "Completed", "On Hold"])
            
            for site in sites:
                site_id = site[0]
                name = site[1]
                location = site[2]
                description = site[3] if len(site) > 3 else ""
                start_date = site[4] if len(site) > 4 else ""
                status = site[5] if len(site) > 5 else "Active"
                # Handle new fields with defaults for backward compatibility
                num_basements = site[6] if len(site) > 6 else 0
                num_floors = site[7] if len(site) > 7 else 10
                has_roof = site[8] if len(site) > 8 else 1
                
                # Apply filters
                if search_term and search_term.lower() not in name.lower() and search_term.lower() not in location.lower():
                    continue
                if status_filter != "All" and status != status_filter:
                    continue
                
                # Get site statistics
                site_stats = get_site_statistics(site_id)
                
                with st.expander(f"🏗️ **{name}** - {location}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Location:** {location}")
                        if description:
                            st.write(f"**Description:** {description}")
                        if start_date:
                            st.write(f"**Start Date:** {start_date}")
                        st.write(f"**Status:** `{status}`")
                        
                        # Floor structure info
                        floor_structure = []
                        if num_basements > 0:
                            floor_structure.append(f"{num_basements} Basement(s)")
                        floor_structure.append("Ground Floor")
                        floor_structure.append(f"{num_floors} Floor(s)")
                        if has_roof:
                            floor_structure.append("Roof/Terrace")
                        st.write(f"**Building Structure:** {' + '.join(floor_structure)}")
                    
                    with col2:
                        st.metric("Progress", f"{site_stats['latest_progress']}%")
                        st.metric("Total Updates", site_stats['total_updates'])
                    
                    # Floor-wise progress preview (if data available)
                    floor_data = get_floor_wise_progress(site_id)
                    if floor_data:
                        st.markdown("**🏢 Floor-wise Progress Overview:**")
                        floor_df = pd.DataFrame(floor_data, columns=['Floor', 'Updates', 'Avg Progress %', 'Latest Phase', 'Work Types Count'])
                        floor_df['Avg Progress %'] = floor_df['Avg Progress %'].round(1).astype(str) + '%'
                        st.dataframe(
                            floor_df[['Floor', 'Avg Progress %', 'Latest Phase']],
                            use_container_width=True,
                            hide_index=True,
                            height=150
                        )
                    
                    # Status update
                    st.markdown("**Update Status:**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("🟢 Active", key=f"active_{site_id}"):
                            update_site_status(site_id, "Active")
                            st.success("Status updated!")
                            st.rerun()
                    with col2:
                        if st.button("✅ Completed", key=f"completed_{site_id}"):
                            update_site_status(site_id, "Completed")
                            st.success("Status updated!")
                            st.rerun()
                    with col3:
                        if st.button("⏸️ On Hold", key=f"hold_{site_id}"):
                            update_site_status(site_id, "On Hold")
                            st.success("Status updated!")
                            st.rerun()
                    with col4:
                        if st.button("❌ Cancelled", key=f"cancelled_{site_id}"):
                            update_site_status(site_id, "Cancelled")
                            st.success("Status updated!")
                            st.rerun()
    
    with tab2:
        st.header("Add New Construction Site")
        
        with st.form("add_site_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Site Name *", placeholder="e.g., Downtown Office Complex")
                location = st.text_input("Location *", placeholder="e.g., 123 Main St, City")
                start_date = st.date_input("Start Date", value=datetime.date.today())
            
            with col2:
                description = st.text_area("Description", placeholder="Brief description of the project...", height=100)
            
            st.markdown("---")
            st.subheader("🏢 Building Structure Details")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                num_basements = st.number_input("Number of Basements", min_value=0, max_value=5, value=0, step=1,
                                               help="How many basement levels? (0-5)")
            
            with col2:
                num_floors = st.number_input("Number of Floors", min_value=1, max_value=100, value=10, step=1,
                                            help="How many floors above ground? (1-100)")
            
            with col3:
                has_roof = st.checkbox("Has Roof/Terrace Level", value=True,
                                      help="Include roof/terrace in floor list?")
            
            # Preview floor structure
            st.info(f"**Floor Structure Preview:** {num_basements} basement(s) + Ground Floor + {num_floors} floor(s)" + 
                   (" + Roof/Terrace" if has_roof else ""))
            
            submitted = st.form_submit_button("➕ Add Site", use_container_width=True)
            
            if submitted:
                if not name or not location:
                    st.error("⚠️ Please fill in all required fields (marked with *)")
                else:
                    if add_site(name, location, description, start_date.strftime("%Y-%m-%d"), 
                              num_basements, num_floors, has_roof):
                        st.success(f"✅ Site '{name}' added successfully with {num_basements} basement(s), ground floor, {num_floors} floor(s)" + 
                                 (" and roof/terrace!" if has_roof else "!"))
                        st.rerun()
                    else:
                        st.error(f"❌ Site '{name}' already exists.")
    
    with tab3:
        st.header("User Management")
        
        users = get_all_users()
        
        st.markdown("### Registered Users")
        for user in users:
            user_id, username, role = user
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{username}**")
            with col2:
                st.write(f"`{role.title()}`")
