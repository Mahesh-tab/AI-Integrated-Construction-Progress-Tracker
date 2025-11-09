import streamlit as st
from database import get_user, init_db
from utils import verify_password
import admin_page
import engineer_page_new as engineer_page

# Page configuration
st.set_page_config(
    page_title="Construction Progress Tracker",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #0066cc;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #0052a3;
    }
    h1 {
        color: #1f1f1f;
        padding-bottom: 1rem;
        border-bottom: 3px solid #0066cc;
    }
    h2 {
        color: #2c3e50;
        margin-top: 2rem;
    }
    .user-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .metric-card h3 {
        margin-top: 0;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .metric-card h1 {
        margin: 0.5rem 0 0 0;
        font-size: 2.5rem;
        font-weight: 700;
        border: none;
        padding: 0;
    }
    </style>
    """, unsafe_allow_html=True)

def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.role = ''
        st.session_state.user_id = None

    if st.session_state.logged_in:
        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"""
                <div class="user-info">
                    <h3>👤 {st.session_state.username}</h3>
                    <p><strong>Role:</strong> {st.session_state.role.title()}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ''
                st.session_state.role = ''
                st.session_state.user_id = None
                st.rerun()

        # Show appropriate page based on role
        if st.session_state.role == 'admin':
            admin_page.show()
        elif st.session_state.role == 'engineer':
            engineer_page.show()
    else:
        # Login page
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>🏗️ Construction Progress Tracker</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>AI-Powered Construction Monitoring System</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.container():
                st.markdown("### 🔐 Login")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Login", use_container_width=True):
                    if not username or not password:
                        st.error("⚠️ Please enter both username and password")
                    else:
                        user = get_user(username)
                        if user and verify_password(password, user[2]):
                            st.session_state.logged_in = True
                            st.session_state.username = user[1]
                            st.session_state.role = user[3]
                            st.session_state.user_id = user[0]
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            with st.expander("ℹ️ Demo Credentials"):
                st.markdown("""
                **Admin Account:**
                - Username: `admin`
                - Password: `admin`
                
                **Engineer Account:**
                - Username: `engineer`
                - Password: `engineer`
                """)

if __name__ == '__main__':
    init_db()
    login()
