# Character Profile Generator Agent

An AI-powered character profile generator that creates deep, nuanced personas using Google's Gemini API. Designed as a database administrator tool for managing character profiles.

## Features

- **AI-Powered Generation**: Uses Gemini 2.0 Flash for creative character profile creation
- **Standardized Format**: Generates profiles with NAME, RESONANCE TYPE, LAST OBSERVED, and ECHO
- **Database Integration**: Stores profiles in SQLite (easily swappable to PostgreSQL/MySQL)
- **Web Interface**: Built with Streamlit for easy deployment and use
- **CRUD Operations**: View, create, delete character profiles
- **Free Technologies**: Uses free-tier Gemini API

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set your Google Gemini API key:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey)

## Running

```bash
streamlit run app.py
```

## Deployment

### Streamlit Cloud (Free)
1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add `GOOGLE_API_KEY` in Secrets

### Production Database
For production, replace SQLite with PostgreSQL:

```python
import psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"])
```

## Character Profile Format

```
NAME: 
J. Robert Oppenheimer

RESONANCE TYPE: 
Existential
Reflective
Visionary
Melancholic
Defiant
Obsessive
Transcendent

LAST OBSERVED
Los Alamos, 1945

ECHO(bio)
"We thought the equations would save us."
```
