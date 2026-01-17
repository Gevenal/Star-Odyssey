# Star-Odyssey 🚀

> An AI-powered space survival game where you command a damaged spacecraft's crew through a crisis, powered by Google Gemini.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)

## 🎮 About

Star-Odyssey is a narrative-driven survival game where:
- **Every decision matters**: Manage resources, crew morale, and relationships
- **AI-powered storytelling**: Google Gemini generates unique narratives based on your choices
- **Dynamic NPCs**: 9 crew members with evolving personalities and autonomous behaviors
- **ORACLE System**: The ship's AI gains sentience as you interact with it
- **Multiple endings**: Victory, defeat, or something in between

**Survive 7 days in deep space. Will you make it home?**

## ✨ Features

### Core Gameplay
- **Turn-based survival**: 84 turns (7 days) to survive
- **Resource management**: Oxygen, fuel, power, medical supplies, food, repair materials
- **8 ship locations**: Each with unique hazards and opportunities
- **9 crew members**: With deep personality systems and relationship dynamics
- **Random events**: AI-generated crises and opportunities
- **Multiple victory paths**: Repair, rescue, or evacuation

### AI Integration
- **Dynamic narration**: Gemini generates contextual story responses
- **NPC decision-making**: AI controls autonomous NPC actions
- **Consequence generation**: Emergent outcomes from player choices
- **Evolving ORACLE**: Ship AI that gains sentience through interaction
- **Real-time streaming**: SSE for typewriter-effect narration

## 🛠️ Tech Stack

**Backend:** FastAPI • Google Gemini • MongoDB • Redis • Pydantic  
**Frontend:** React • TypeScript • Zustand • Tailwind CSS • Axios

## 📦 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 6.0+
- Redis 7.0+
- Google Gemini API Key ([Get one](https://ai.google.dev/))

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/odyssey-7.git
cd odyssey-7

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install  # or yarn/bun
```

### 2. Configure Environment

**Backend `.env`:**
```bash
GEMINI_API_KEY=your_api_key_here
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Frontend `.env`:**
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. Start Services

```bash
# Start MongoDB
brew services start mongodb-community  # macOS
# or: docker run -d -p 27017:27017 mongo

# Start Redis
brew services start redis  # macOS
# or: docker run -d -p 6379:6379 redis
```

### 4. Run Application

```bash
# Backend (in backend/)
uvicorn app.main:app --reload

# Frontend (in frontend/)
npm run dev
```

**Access:**
- Game: http://localhost:5173
- API Docs: http://localhost:8000/docs

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design
- **[Game Design](docs/GAME_DESIGN.md)** - Mechanics & gameplay
- **[API Reference](docs/API.md)** - Endpoints

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app

# Frontend tests (when implemented)
cd frontend
npm test
```

## 📁 Project Structure

```
Star-Odyssey/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Game loop, rules
│   │   ├── ai/           # Gemini integration
│   │   ├── db/           # Database layer
│   │   └── models/       # Data models
│   └── tests/            # Test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── stores/       # State management
│   │   ├── hooks/        # Custom hooks
│   │   └── api/          # API client
│   └── package.json
│
└── docs/                 # Documentation
```

## 🐛 Troubleshooting

**MongoDB not connecting?**
```bash
mongosh --eval "db.version()"  # Test connection
```

**Redis issues?**
```bash
redis-cli ping  # Should return PONG
```

**Gemini API errors?**
- Verify API key in `.env`
- Check quota at https://ai.google.dev/

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

Built with Google Gemini, FastAPI, and React for the Google Gemini Hackathon

---

**Made with ❤️ for AI-powered storytelling**
