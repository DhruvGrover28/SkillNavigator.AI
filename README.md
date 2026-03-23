# 🚀 SkillNavigator - AI-Powered Job Application Platform

An intelligent multi-agent system that revolutionizes job searching through AI-powered automation, smart matching, and seamless application tracking.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![AI Powered](https://img.shields.io/badge/AI-Powered-orange.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Overview

SkillNavigator is a cutting-edge job application platform that leverages artificial intelligence to automate and optimize the entire job search process. Built as part of the IBM SkillsBuild initiative, it demonstrates advanced AI integration, multi-agent architecture, and modern web technologies.

## 🎯 Key Features

### 🤖 **Multi-Agent AI System**
- **🕷️ Scraper Agent**: Intelligent web scraping from multiple job platforms (Indeed, LinkedIn, Glassdoor)
- **🎯 Scoring Agent**: AI-powered job-candidate matching using advanced ML algorithms
- **✉️ AutoApply Agent**: Automated application submission with personalized cover letters
- **📊 Tracker Agent**: Real-time application status monitoring and analytics
- **🎭 Supervisor Agent**: Orchestrates all agents with intelligent workflow management

### 💡 **Smart Capabilities**
- 🔍 **Intelligent Job Discovery**: Multi-platform scraping with anti-detection measures
- 🧠 **AI-Driven Matching**: Sentence transformers and ML scoring for perfect job-candidate alignment
- 📝 **Dynamic Cover Letters**: GPT-powered personalized application materials
- 📧 **Email Integration**: Automated application submission and follow-up notifications
- 📈 **Analytics Dashboard**: Comprehensive tracking and success metrics
- 🔄 **Workflow Automation**: Smart scheduling and task coordination

## 🛠️ **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.13 | High-performance async API |
| **Database** | SQLite + SQLAlchemy | Lightweight, efficient data storage |
| **AI/ML** | OpenAI GPT + Sentence Transformers | Natural language processing |
| **Web Scraping** | Playwright + BeautifulSoup | Robust, stealth web automation |
| **Scheduling** | Python Schedule | Automated task management |
| **Email** | SMTP + aiosmtplib | Asynchronous email handling |

## 🚀 **Quick Start Guide**

### Prerequisites
- 🐍 Python 3.8+ (3.13.5 recommended)
- 🔑 OpenAI API key
- 🌐 Internet connection for web scraping

### 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/DhruvGrover28/IBM-Skillsbuild-Project.git
cd IBM-Skillsbuild-Project

# 2. Install core dependencies
pip install -r requirements_simple.txt

# 3. Install additional packages
pip install schedule aiosmtplib email-validator

# 4. Install Playwright browsers
python -m playwright install chromium

# 5. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 6. Initialize database with sample data
python scripts/init_db.py

# 7. Verify installation
python scripts/verify_system.py
```

### 🎬 **Launch Application**

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

🌐 **Access**: `http://localhost:8000`  
📚 **API Docs**: `http://localhost:8000/docs`

## 📁 **Project Architecture**

```
skillnavigator/
├── 🧠 backend/
│   ├── 🤖 agents/           # AI agent implementations
│   │   ├── scraper_agent.py      # Web scraping automation
│   │   ├── scoring_agent.py      # ML-based job matching
│   │   ├── autoapply_agent.py    # Application submission
│   │   ├── tracker_agent.py      # Status monitoring
│   │   └── supervisor_agent.py   # Workflow orchestration
│   ├── 🗄️ database/         # Data layer
│   │   ├── db_connection.py      # SQLAlchemy models
│   │   └── schema.sql           # Database schema
│   ├── 🛣️ routes/           # API endpoints
│   │   ├── jobs.py              # Job-related operations
│   │   ├── user.py              # User management
│   │   └── tracker.py           # Application tracking
│   ├── 🔧 utils/            # Helper functions
│   │   ├── scraper_helpers.py   # Web scraping utilities
│   │   ├── matching.py          # AI matching algorithms
│   │   └── prompt_templates.py  # GPT prompt engineering
│   └── 🚀 main.py           # FastAPI application
├── 📊 data/                 # Sample data and configs
│   ├── applications.json        # Sample application data
│   ├── job_listings.json        # Sample job listings
│   └── user_profiles.json       # Sample user profiles
├── �️ database/             # Database files
│   └── schema.sql               # Database schema
├── �🔧 scripts/              # Utility and setup scripts
│   ├── init_db.py               # Database initialization
│   ├── test_api.py              # API testing script
│   └── verify_system.py         # System verification
├── 📋 requirements.txt      # Python dependencies
├── 📋 requirements_simple.txt # Simplified dependencies
├── � start.bat            # Windows startup script
├── 🚀 start.sh             # Linux/Mac startup script
├── ✅ verify.bat           # Windows verification script
├── ✅ verify.sh            # Linux/Mac verification script
├── 🐳 docker-compose.yml   # Docker configuration
├── 🐳 Dockerfile           # Docker container setup
├── ⚙️ .env.example          # Environment template
└── 📚 Documentation files  # README, VERIFICATION, etc.
```

## 🔌 **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jobs/search` | POST | 🔍 Search and scrape jobs from multiple platforms |
| `/jobs/score` | POST | 🎯 AI-powered job scoring and ranking |
| `/applications/apply` | POST | ✉️ Automated job application submission |
| `/applications/track` | GET | 📊 Track application status and analytics |
| `/users/create` | POST | 👤 Create and manage user profiles |
| `/agents/supervisor/start` | POST | 🎭 Start automated job search workflow |

## ⚙️ **Configuration**

### 🔐 Environment Variables
```env
# Core Configuration
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secure_secret_key
DATABASE_URL=sqlite:///./skillnavigator.db

# Optional Settings
DEBUG=false
LOG_LEVEL=info
MAX_APPLICATIONS_PER_DAY=10
EMAIL_NOTIFICATIONS=true
```

### 🎛️ Agent Settings
Configure through the supervisor agent interface:
- 🔍 **Search Parameters**: Keywords, location, experience level
- 🎯 **Scoring Criteria**: Skills match weight, salary preferences
- ✉️ **Application Settings**: Cover letter templates, follow-up schedules
- 📧 **Notifications**: Email alerts, success metrics

## 🧪 **Testing & Verification**

```bash
# Run comprehensive system verification
python scripts/verify_system.py

# Test API endpoints
python scripts/test_api.py

# Quick health check
python -c "from backend.main import app; print('✅ System Ready!')"
```

## 📈 **Usage Examples**

### 🔍 **Search for Jobs**
```python
import requests

response = requests.post("http://localhost:8000/jobs/search", json={
    "keywords": "Python Developer",
    "location": "Remote",
    "experience_level": "mid-level"
})
jobs = response.json()
```

### 🎯 **Score Job Matches**
```python
response = requests.post("http://localhost:8000/jobs/score", json={
    "user_id": 1,
    "job_ids": [1, 2, 3, 4, 5]
})
scores = response.json()
```

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🔄 Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- 🎓 **IBM SkillsBuild** for providing the learning platform and project opportunity
- 🤖 **OpenAI** for GPT API integration
- 🌐 **FastAPI** community for the excellent framework
- 🧠 **Hugging Face** for sentence transformers

## 📞 **Support & Contact**

- 📧 **Issues**: [GitHub Issues](https://github.com/DhruvGrover28/IBM-Skillsbuild-Project/issues)
- 📖 **Documentation**: Check the `/docs` folder for detailed guides
- 🔧 **Troubleshooting**: Run `python scripts/verify_system.py` for diagnostics

---

**Built with ❤️ for IBM SkillsBuild | Empowering careers through AI innovation**
