# 🏗️ Construction Progress Tracking System

A comprehensive, AI-powered construction site management system built with Streamlit, featuring multi-floor tracking, work type management, and intelligent progress verification.

---

## ✨ Key Features

### 👷 For Engineers:
- **Multi-Floor Data Entry** - Track progress across multiple floors simultaneously
- **Work Type Management** - Detailed tracking of 12+ work types (structural, MEP, finishing)
- **AI-Powered Analysis** - Google Gemini AI analyzes photos and verifies work
- **Progress History** - Complete audit trail with images and reports
- **Interactive Analytics** - Real-time charts and visualizations

### 👨‍💼 For Project Managers:
- **Floor-wise Analytics** - Compare progress across all floors
- **Work Type Breakdown** - Track completion status by work type
- **Verification Dashboard** - AI verification status tracking
- **PDF Reports** - Generate professional progress reports
- **Filter & Export** - Advanced filtering and data export

### 🤖 AI Features:
- **Collective Image Analysis** - Analyze multiple images together
- **Technical Quality Assessment** - Workmanship and compliance checks
- **Safety Compliance** - PPE and hazard identification
- **Progress Verification** - Cross-reference claims with visual evidence
- **Detailed Recommendations** - Actionable insights and next steps

---

## 🚀 Quick Start

### Prerequisites:
```bash
Python 3.8+
SQLite 3
Google Gemini API Key
```

### Installation:

1. **Clone the repository:**
```bash
git clone <repository-url>
cd mtech-project
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Create .env file
echo GOOGLE_API_KEY=your_gemini_api_key_here > .env
```

4. **Initialize database:**
```bash
python migrate_database.py
```

5. **Run the application:**
```bash
streamlit run app/main.py
```

6. **Access the app:**
Open browser to `http://localhost:8501`

---

## 📁 Project Structure

```
mtech-project/
├── app/                          # Main application code
│   ├── main.py                   # Entry point
│   ├── database.py               # Database operations
│   ├── admin_page.py            # Admin dashboard
│   ├── engineer_page_new.py     # Engineer dashboard (new)
│   └── utils.py                 # Utility functions
│
├── docs/                         # Documentation (19 guides)
│   ├── README.md                # Documentation index
│   ├── QUICK_START.md           # Quick start guide
│   ├── NEW_ENGINEER_PAGE_GUIDE.md  # Engineer manual
│   ├── ANALYTICS_UPDATE_SUMMARY.md # Analytics guide
│   └── ... (15+ more docs)
│
├── construction.db              # SQLite database
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables
│
├── migrate_database.py         # Database migration script
├── add_work_types_table.py    # Work types table setup
├── verify_work_types.py       # Data verification script
└── README.md                  # This file
```

---

## 📊 Database Schema

### Main Tables:
- **users** - User accounts (admin/engineer)
- **sites** - Construction site details
- **progress** - Progress updates with AI analysis
- **work_types** - Floor-wise work type tracking

### Key Relationships:
```
sites (1) ──→ (many) progress
progress (1) ──→ (many) work_types
users (1) ──→ (many) progress
```

---

## 🎯 Core Workflows

### 1. Engineer Workflow:
```
Select Site → Add Floor Data → Upload Photos → AI Analysis → Review & Confirm → Database Save
```

### 2. Admin Workflow:
```
Add Sites → Manage Users → View Reports → Monitor Progress → Generate Analytics
```

### 3. AI Analysis Workflow:
```
Upload Images → Collective Analysis → Technical Assessment → Safety Check → Verification Status
```

---

## 📚 Documentation

Complete documentation is available in the **[docs/](docs/)** folder:

### Quick Access:
- **[Quick Start Guide](docs/QUICK_START_NEW_ENGINEER_PAGE.md)** - Get started in 5 minutes
- **[Engineer Manual](docs/NEW_ENGINEER_PAGE_GUIDE.md)** - Complete feature guide (4500+ words)
- **[Analytics Guide](docs/ANALYTICS_UPDATE_SUMMARY.md)** - Analytics features
- **[Architecture Diagram](docs/ARCHITECTURE_DIAGRAM.md)** - System design
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Database setup

**[📖 View Full Documentation Index](docs/README.md)**

---

## 🔧 Tech Stack

### Backend:
- **Python 3.x** - Core language
- **SQLite** - Database
- **Google Gemini AI** - Image analysis

### Frontend:
- **Streamlit** - Web framework
- **Plotly** - Interactive charts
- **Pandas** - Data processing

### Additional:
- **PIL/Pillow** - Image handling
- **FPDF** - PDF generation
- **python-dotenv** - Environment management

---

## 📈 Features Breakdown

### Multi-Floor Tracking:
- Dynamic floor generation (basements, ground, upper, roof)
- Individual floor progress tracking
- Floor-wise work type management
- Collective floor analysis

### Work Types (12 Categories):
**Core Construction:**
- Structural Work
- Masonry Work
- Plastering

**MEP Works:**
- Plumbing Work
- Electrical Work
- HVAC Work

**Finishing Works:**
- Waterproofing
- Toilet Finishes
- Lift Lobby Finishes
- Painting
- Flooring
- False Ceiling

### Analytics Visualizations:
- Progress Timeline
- Category Breakdown
- Verification Status
- Floor-wise Progress
- Work Type Heatmap
- Floor Comparison Charts
- Detailed Data Tables

---

## 🎨 Key Highlights

✅ **Professional UI** - Modern, intuitive interface  
✅ **Multi-floor Support** - Track unlimited floors  
✅ **AI-Powered** - Intelligent verification  
✅ **Real-time Analytics** - Live data visualization  
✅ **Comprehensive Reports** - Detailed PDF exports  
✅ **Filter & Search** - Advanced data filtering  
✅ **Audit Trail** - Complete history tracking  
✅ **Mobile Friendly** - Responsive design  

---

## 🔐 User Roles

### Engineer:
- Submit progress updates
- Upload photos
- View AI analysis
- Access analytics
- Download reports

### Admin:
- All engineer features
- Add/manage sites
- Manage users
- System configuration
- Advanced analytics

---

## 🚀 Deployment

### Local Development:
```bash
streamlit run app/main.py
```

### Production Deployment:
See [CHECKLIST.md](docs/CHECKLIST.md) for deployment guide

---

## 📝 Changelog

### Version 2.0 (Current)
- ✅ Multi-floor data entry
- ✅ Work type tracking
- ✅ Collective AI analysis
- ✅ Floor-wise analytics
- ✅ Advanced filtering
- ✅ Enhanced visualizations

### Version 1.0
- ✅ Basic progress tracking
- ✅ Single floor support
- ✅ Simple AI analysis
- ✅ Basic analytics

---

## 🤝 Contributing

1. Read the documentation in `docs/`
2. Follow the existing code style
3. Update documentation for new features
4. Test thoroughly before committing

---

## 📞 Support

- **Documentation:** Check `docs/` folder
- **Issues:** Review existing documentation
- **Features:** See feature-specific guides in `docs/`

---

## 📄 License

[Add your license here]

---

## 🙏 Acknowledgments

- **Google Gemini AI** - For intelligent image analysis
- **Streamlit** - For the amazing web framework
- **Plotly** - For interactive visualizations

---

## 📊 Project Stats

- **Total Code Files:** 7+
- **Documentation Files:** 19
- **Database Tables:** 4
- **Work Types Tracked:** 12
- **AI Verification:** Yes
- **Multi-floor Support:** Unlimited
- **Documentation Coverage:** 30,000+ words

---

**Built with ❤️ for Construction Management**

**Version:** 2.0  
**Last Updated:** November 9, 2025  
**Status:** Production Ready ✅
