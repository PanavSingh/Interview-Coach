# Interviewer AI — Django App

AI-powered interview practice with real-time question generation, answer evaluation, and voice input.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set AI API key for smart questions & feedback
export OPENAI_API_KEY=<your_key>
# OR
export GEMINI_API_KEY=<your_key>

# 3. Run migrations
python manage.py migrate

# 4. Start the dev server
python manage.py runserver

# 5. Open in browser
http://127.0.0.1:8000/
```

## Features

- **User Auth** — Sign in to persist progress, or continue as guest
- **AI Questions** — Generated per domain/role/skills via OpenAI or Gemini (falls back to static questions)
- **AI Evaluation** — Real-time scoring and feedback on each answer
- **Voice Input** — Click the mic button to speak your answer (Web Speech API)
- **Data Persistence** — SQLite DB stores users, sessions, and answers

## Screens

| URL              | Screen           |
|------------------|------------------|
| `/`              | Login / Register |
| `/domain/`       | Domain picker    |
| `/profile/`      | Profile form     |
| `/interview/`    | Questions + Mic  |
| `/complete/`     | Results + Feedback |
| `/api/evaluate/` | AJAX evaluation  |

## Architecture

```
interview_coach/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── interview_coach/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── interview/
    ├── models.py          # UserProfile, InterviewSession, Answer
    ├── views.py           # Auth, flow, AI integration
    ├── ai_service.py      # OpenAI/Gemini question gen + evaluation
    ├── urls.py
    └── templates/interview/
        ├── base.html
        ├── login.html
        ├── domain.html
        ├── profile.html
        ├── interview.html  # Voice input + live feedback
        └── complete.html   # Per-question scores
```
