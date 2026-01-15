# 🚀 Next.js + TypeScript + FastAPI Rebuild

## Overview
This branch contains a complete rebuild of the Poker Skill Analyzer using modern, industry-standard technologies.

## 🎯 What Changed

### Tech Stack Migration
- **Frontend**: Flask templates → Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: Flask → FastAPI (async Python)
- **State Management**: React Context API
- **Charts**: Recharts for interactive visualizations
- **Styling**: Tailwind CSS with custom design system

### Why This Stack?
1. **Next.js 14**: Server-side rendering, better performance, modern React features
2. **TypeScript**: Type safety, better IDE support, fewer runtime errors
3. **FastAPI**: Async support, automatic API docs, better performance than Flask
4. **Tailwind CSS**: Utility-first, consistent design, smaller bundle size

## 📁 New Project Structure

```
poker_tracker/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/             # Next.js 14 app directory
│   │   │   ├── page.tsx     # Home/Analysis page
│   │   │   ├── dashboard/   # Dashboard page
│   │   │   ├── graphs/      # Graphs page
│   │   │   └── layout.tsx   # Root layout
│   │   ├── components/      # React components
│   │   │   ├── ui/          # Reusable UI components
│   │   │   ├── analysis/    # Analysis-specific components
│   │   │   ├── dashboard/   # Dashboard components
│   │   │   └── graphs/      # Graph components
│   │   ├── lib/             # Utilities and helpers
│   │   ├── types/           # TypeScript type definitions
│   │   └── styles/          # Global styles
│   ├── public/              # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── api/             # API routes
│   │   │   ├── analysis.py  # Analysis endpoints
│   │   │   ├── dashboard.py # Dashboard endpoints
│   │   │   └── graphs.py    # Graphs endpoints
│   │   ├── core/            # Core functionality
│   │   │   ├── config.py    # Configuration
│   │   │   ├── ai_provider.py
│   │   │   ├── hand_parser.py
│   │   │   └── playstyle_analyzer.py
│   │   ├── models/          # Pydantic models
│   │   └── utils/           # Utility functions
│   ├── requirements.txt
│   └── README.md
│
├── hand_histories/          # Hand history files (unchanged)
├── sample_data/             # Sample data (unchanged)
├── reports/                 # Generated reports (unchanged)
└── docs/                    # Documentation
```

## ✨ New Features

### 1. Professional UI/UX
- Modern, clean design inspired by Stripe and Linear
- Smooth animations and transitions
- Responsive design (mobile, tablet, desktop)
- Dark mode support
- Loading states and error handling
- Toast notifications for user feedback

### 2. Enhanced Dashboard
- **Real-time Statistics**: Win rate, VPIP, PFR, aggression factor
- **Performance Trends**: Charts showing improvement over time
- **Position Analysis**: Win rate by table position
- **Session History**: Track individual sessions
- **Bankroll Tracking**: Monitor your poker bankroll
- **Hand Range Heatmap**: Visual representation of hands played

### 3. Interactive Graphs
- **Win Rate Over Time**: Line chart with trend analysis
- **Results Distribution**: Pie chart (wins/losses/folds)
- **Position Performance**: Bar chart by position
- **Profit/Loss Trend**: Cumulative P/L chart
- **Hand Strength Distribution**: What hands you play
- **Aggression Metrics**: Bet/raise/call ratios
- **All charts are interactive**: Hover for details, click to filter

### 4. Improved Analysis
- **Persistent Results**: Analysis saved to localStorage
- **Export to PDF**: Download analysis reports
- **Comparison Mode**: Compare different time periods
- **AI Insights**: More detailed, structured feedback
- **Hand Replayer**: Visual replay of hands (future feature)

## 🔧 Technical Improvements

### Frontend
- **Type Safety**: Full TypeScript coverage
- **Component Architecture**: Reusable, composable components
- **State Management**: React Context for global state
- **API Client**: Axios with interceptors for error handling
- **Form Validation**: Zod schemas for type-safe validation
- **Code Splitting**: Automatic with Next.js
- **SEO Optimized**: Meta tags, Open Graph support

### Backend
- **Async/Await**: Better performance with async operations
- **API Documentation**: Auto-generated with FastAPI
- **CORS Configured**: Secure cross-origin requests
- **Error Handling**: Consistent error responses
- **Validation**: Pydantic models for request/response validation
- **Logging**: Structured logging for debugging
- **Testing**: Unit tests for core functionality

### Performance
- **Server-Side Rendering**: Faster initial page load
- **Image Optimization**: Next.js automatic image optimization
- **Code Splitting**: Load only what's needed
- **Caching**: Smart caching strategies
- **Bundle Size**: Optimized with tree-shaking

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ (you have v24.12.0 ✅)
- Python 3.10+ (you have 3.14.2 ✅)
- npm or yarn

### Installation

1. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

2. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
# Copy example config
cp config.example.json config.json

# Edit config.json with your settings
# - Add your Gemini API key
# - Set your PokerStars username
```

### Development

1. **Start Backend** (Terminal 1)
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

2. **Start Frontend** (Terminal 2)
```bash
cd frontend
npm run dev
```

3. **Open Browser**
```
http://localhost:3000
```

### Production Build

```bash
# Build frontend
cd frontend
npm run build
npm start

# Run backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📊 API Endpoints

### Analysis
- `POST /api/analyze/summary` - Get overall performance summary
- `POST /api/analyze/detailed` - Get detailed hand-by-hand analysis
- `POST /api/scan` - Scan for new hand history files

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/trends` - Get performance trends
- `GET /api/dashboard/sessions` - Get session history

### Graphs
- `GET /api/graphs/winrate` - Win rate over time data
- `GET /api/graphs/position` - Position performance data
- `GET /api/graphs/profit` - Profit/loss trend data

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/ai/status` - Check AI provider status

## 🎨 Design System

### Colors
- **Primary**: Blue (#3b82f6)
- **Success**: Green (#10b981)
- **Danger**: Red (#ef4444)
- **Warning**: Yellow (#f59e0b)
- **Info**: Cyan (#06b6d4)

### Typography
- **Font**: Inter (system font fallback)
- **Headings**: Bold, tight letter-spacing
- **Body**: Regular, comfortable line-height

### Components
- **Cards**: Rounded corners, subtle shadows
- **Buttons**: Solid, outline, ghost variants
- **Inputs**: Clean, accessible, with validation states
- **Charts**: Consistent color scheme, interactive

## 🧪 Testing

```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
pytest
```

## 📝 Code Quality

### Frontend
- **ESLint**: Configured with Next.js rules
- **Prettier**: Consistent code formatting
- **TypeScript**: Strict mode enabled
- **Husky**: Pre-commit hooks for linting

### Backend
- **Black**: Python code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing framework

## 🔒 Security

- **API Key Protection**: Never exposed to frontend
- **CORS**: Configured for specific origins
- **Input Validation**: All inputs validated
- **SQL Injection**: N/A (no SQL database)
- **XSS Protection**: React escapes by default

## 📈 Performance Metrics

- **Lighthouse Score**: 95+ (target)
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Bundle Size**: < 200KB (gzipped)

## 🐛 Known Issues

None yet! This is a fresh rebuild.

## 🔮 Future Enhancements

1. **Hand Replayer**: Visual replay of poker hands
2. **Opponent Tracking**: Track opponent tendencies
3. **Range Analysis**: Advanced hand range tools
4. **Tournament Mode**: Specific tournament analysis
5. **Mobile App**: React Native version
6. **Multiplayer**: Compare stats with friends
7. **AI Training**: Train custom AI models
8. **Video Analysis**: Upload and analyze poker videos

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (FastAPI auto-generated)
- **Component Storybook**: Coming soon
- **User Guide**: See `/docs/user-guide.md`
- **Developer Guide**: See `/docs/developer-guide.md`

## 🤝 Contributing

This is a personal project, but contributions are welcome!

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- **Gemini AI**: For poker analysis
- **PokerStars**: For hand history format
- **Next.js Team**: For amazing framework
- **FastAPI Team**: For modern Python API framework

## 💬 Questions?

Check the documentation or create an issue on GitHub.

---

**Built with ❤️ for poker players who want to improve their game**
