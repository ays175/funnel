# Funnel 🎯

**Ask once, get exactly what you need—like AI with a laser focus.**

Funnel is a precision-targeting system for AI queries. Instead of casting one wide net and getting generic answers, Funnel decomposes your question into specific angles, lets you pick what matters, and delivers focused, traceable answers.

---

## 🌟 Why Funnel?

### The Problem
You ask your AI a question and get a wall of text that somehow misses *exactly* what you needed. You try again, refine it, ask it differently... but you're still playing guessing games.

### The Funnel Approach
1. **We Show All the Angles**: Ask anything. We'll show you all the ways it can be answered—beginner or expert, modern or historical, theory or examples.
2. **You Pick What You Need**: Check the boxes for what matters. Ignore the rest. Small targeted nets, not one giant one.
3. **Answer + Full Trace**: Get exactly what you wanted, plus see the reasoning behind it. No black box—everything's transparent.

---

## ✨ Key Features

### 🎨 Modern React UI
- **3-Screen Wizard Flow**: Query setup → Facet selection → Answer with trace
- **Elegant Design**: Purple gradient theme with glassmorphism effects
- **Mobile-Responsive**: Works beautifully on all devices
- **Gradient Tagline**: Eye-catching golden-to-purple gradient promise statement

### 🎣 Angle-Based Selection (Fishing Metaphor)
- **Dynamic Facet Discovery**: AI generates topic-specific angles based on your query
- **Multi-Select with "All Options"**: Choose multiple perspectives at once
- **Subchoices**: Drill down into specific aspects (e.g., "Historical Period" → "Safavid Dynasty")
- **Angle Navigation**: Numbered badges (Angle 1/5, 2/5, etc.) for clear progression
- **Clickable Selections**: Click any selection chip to jump back to that angle for refinement

### 🎛️ Output Control
- **Audience**: Beginner, Intermediate, Expert, Executive
- **Format**: Bullets, Steps, Table, Paragraphs
- **Length**: 300, 600, 900, or 1200 words
- **Domain Hints**: Optional context (finance, legal, medical, etc.)

### 📊 Traceability & Explainability
- **Full Trace View**: See every decision the AI made
- **Transparent Reasoning**: Understand why you got the answer you did
- **Request ID Tracking**: Every query session is traceable
- **Event Ledger**: Complete append-only log of the discovery process

### 🎯 Smart Navigation
- **Stepper Interface**: Navigate through angles with Previous/Next
- **Sticky Actions**: Always-accessible navigation bar at bottom
- **New Query Button**: Start fresh anytime (Screen 2 & 3)
- **Back to Facets**: Return from answer to refine selections
- **Smooth Scrolling**: Automatic scroll on navigation

### 📝 Answer Presentation
- **Markdown Rendering**: Full markdown support with proper formatting
- **Plain Text Mode**: Simple, unformatted view
- **Presentation Toggle**: Switch between modes seamlessly
- **Syntax Highlighting**: Headers, lists, blockquotes, bold, italic

---

## 🏗️ Architecture

### Backend (FastAPI)
```
app/
├── main.py                 # FastAPI app, static file serving
├── api/
│   ├── routes.py          # /discover, /refine, /answer endpoints
│   └── schemas.py         # Pydantic models
├── core/
│   ├── config.py          # Settings, env vars
│   ├── llm_client.py      # OpenAI API wrapper
│   ├── facet_discovery.py # LLM-driven facet generation
│   ├── facet_ranker.py    # Information gain ranking
│   ├── prompt_compiler.py # Selection → structured prompt
│   ├── trace_ledger.py    # Event logging
│   └── domain_router.py   # Domain-specific packs
├── packs/
│   ├── universal.json     # Default facets
│   ├── legal.json         # Legal domain facets
│   └── finance.json       # Finance domain facets
└── storage/
    └── trace_store.py     # SQLite/JSONL trace persistence
```

### Frontend (React)
- **Single-Page Application**: Built with React via Babel Standalone
- **Component Architecture**: Screen1, Screen2, Screen3, FacetChoices
- **State Management**: React Hooks (useState, useEffect)
- **No Build Step**: Runs directly in browser for simplicity

---

## 🚀 Deployment

### Railway (Recommended - Single Service)

Deploy the entire application (API + UI) as one service:

1. **Create Railway Service** from this repo (branch `main` or `React`)
2. **Set Environment Variables**:
   ```
   OPENAI_API_KEY=sk-...
   MAX_FACET_QUESTIONS=10
   PORT=$PORT  # Railway auto-sets this
   ```
3. **Configure Start Command** (in `railway.toml` or Railway UI):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Access**:
   - UI: `https://your-app.up.railway.app/`
   - API: `https://your-app.up.railway.app/api/discover`
   - Docs: `https://your-app.up.railway.app/docs`

### Local Development

```bash
# Install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run server
uvicorn app.main:app --host 127.0.0.1 --port 8001

# Open browser
open http://127.0.0.1:8001
```

---

## 🎯 API Endpoints

### `POST /api/discover`
Initial facet discovery based on raw query.

**Request:**
```json
{
  "raw_query": "What was the role of mollahs in Iranian history?",
  "domain_hint": "history"
}
```

**Response:**
```json
{
  "request_id": "uuid-...",
  "facet_candidates": [
    {
      "id": "historical_period",
      "title": "Historical Period",
      "question": "Which period should be emphasized?",
      "reason": "Mollahs' influence varied across eras",
      "choices": [
        {
          "value": "Safavid Dynasty (1501–1736)",
          "subchoices": []
        },
        {
          "value": "all options",
          "subchoices": []
        }
      ]
    }
  ],
  "proceed_defaults": {
    "audience": "intermediate",
    "format": "paragraphs",
    "length": "600 words"
  }
}
```

### `POST /api/refine`
Get additional facets based on selections (Round 2).

**Request:**
```json
{
  "request_id": "uuid-...",
  "facet_selections": [
    {
      "id": "historical_period",
      "value": "Safavid Dynasty (1501–1736)"
    }
  ],
  "refine_round": 2
}
```

**Response:**
```json
{
  "facet_candidates": [
    {
      "id": "safavid_focus",
      "title": "Safavid Period Focus",
      "question": "What aspect of the Safavid era?",
      "choices": [...]
    }
  ]
}
```

### `POST /api/answer`
Generate final answer with full trace.

**Request:**
```json
{
  "request_id": "uuid-...",
  "facet_selections": [
    {"id": "audience", "value": "expert"},
    {"id": "format", "value": "bullets"},
    {"id": "length", "value": "600 words"},
    {"id": "historical_period", "value": "Safavid Dynasty"}
  ],
  "user_overrides": null
}
```

**Response:**
```json
{
  "answer": "# Role of Mollahs in Safavid Iran\n\n- Established...",
  "trace": [
    {
      "timestamp": "2026-01-18T...",
      "event": "prompt_compiled",
      "data": {"sections": [...]}
    },
    {
      "event": "llm_response",
      "data": {"model": "gpt-4", "tokens": 523}
    }
  ]
}
```

---

## 🎨 UI Features in Detail

### Screen 1: Query Setup
- **Large White Query Field**: High-contrast, prominent input (2/3 width)
- **Domain + Button** (1/3 width):
  - Domain hint field (optional)
  - "Show All Angles" button (purple gradient)
- **How it Works**: Step-by-step explanation with numbered badges
- **Promise Statement**: Golden gradient tagline
- **Explanation Card**: Pain point → solution → payoff

### Screen 2: Angle Selection
- **Request ID Display** with "New Query" button (blue)
- **Action Buttons**:
  - "Pick More Angles" (orange) - adds more facets
  - "Proceed" (purple) - go to answer
- **Angle Card** with:
  - Blue "Angle X/Y" badge (larger, prominent)
  - Facet title
  - Question and reasoning
  - Interactive chips for choices and subchoices
- **Output Settings Card** (Audience/Format/Length)
- **Selections Summary** (clickable chips to navigate back)
- **Sticky Navigation Bar**: Previous, Pick More Angles, Proceed, Next

### Screen 3: Answer Display
- **Navigation**: "Back to facets" + "New Query" (both blue)
- **Presentation Toggle**: Plain ↔ Markdown
- **Answer Card**: Beautifully formatted markdown
- **Full Trace**: JSON view of all events and decisions

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
OPENAI_MODEL=gpt-4o              # LLM model to use
MAX_FACET_QUESTIONS=10           # Max facets per round
CORS_ORIGINS=*                   # CORS allowed origins
HOST=0.0.0.0                     # Server host
PORT=8000                        # Server port
```

### Domain Packs

Create custom domain packs in `app/packs/`:

```json
{
  "domain": "medical",
  "facets": [
    {
      "id": "patient_population",
      "title": "Patient Population",
      "question": "Which patient group?",
      "suggested_values": [
        "pediatric",
        "adult",
        "geriatric",
        "all options"
      ]
    }
  ]
}
```

---

## 🎯 Use Cases

### Research & Learning
- **Academic Research**: Narrow literature reviews by methodology, time period, geography
- **Student Learning**: Get beginner explanations vs. expert deep-dives
- **Professional Development**: Theory vs. practice, historical vs. modern approaches

### Professional Work
- **Legal Research**: Narrow by jurisdiction, case type, precedent era
- **Financial Analysis**: Focus on specific markets, time periods, risk factors
- **Medical Queries**: Filter by patient population, treatment approach, evidence level

### Content Creation
- **Technical Writing**: Adjust depth, format (bullets/steps), and length
- **Documentation**: Audience-specific content (beginner vs. expert)
- **Marketing Copy**: Tone, length, and style tailoring

---

## 🛠️ Development

### Tech Stack
- **Backend**: FastAPI, Pydantic, OpenAI Python SDK
- **Frontend**: React (Babel Standalone), vanilla CSS with CSS variables
- **Database**: SQLite (for trace storage)
- **Deployment**: Railway, Docker-ready

### Design System
- **Colors**: 
  - Primary: Purple gradient (`hsl(270, 91%, 65%)` → `hsl(330, 81%, 60%)`)
  - Secondary: Blue gradient (`hsl(200, 70%, 50%)` → `hsl(210, 75%, 55%)`)
  - Accent: Orange gradient (`hsl(25, 95%, 53%)` → `hsl(15, 100%, 55%)`)
- **Font**: Sora (Google Fonts)
- **Effects**: Glassmorphism, subtle shadows, smooth transitions

### Code Style
- **Backend**: Black formatter, type hints, async/await
- **Frontend**: Functional React components, hooks, inline styles for dynamic values

---

## 📚 Further Reading

### Concept Papers
- Progressive disclosure in UI design (Nielsen Norman Group)
- Recognition over recall (cognitive load reduction)
- Information gain in facet ranking
- Prompt engineering for structured outputs

### Related Work
- Faceted search interfaces
- Conversational AI refinement
- Explainable AI (XAI) systems
- Structured prompt engineering

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- FastAPI for the excellent backend framework
- React for the UI library
- Railway for seamless deployment

---

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ for precision AI querying**
