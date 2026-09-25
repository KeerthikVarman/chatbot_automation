# AI Conversational Workflow Builder

An agentic AI workflow planning system built with LangGraph, FastAPI, Streamlit, and UI/UX Pro Max design standards.

The application converts natural language automation requests into structured, executable DAG (Directed Acyclic Graph) workflow specifications with dynamic parameter extraction, single-question clarification loops, and automatic multi-model fallbacks.

---

## Architecture Overview

```mermaid
graph TD
    A[User Input] --> B[analyze_request_node]
    B --> C{Missing Info Check}
    C -- Clarification Required --> D[clarification_node]
    D --> E[Wait for User Reply]
    C -- All Info Collected --> F[generate_workflow_node]
    F --> G[Workflow Spec Ready]
```

### Directory Structure

```
AI_cov/
├── agent.py                 # LangGraph state machine & node logic
├── api.py                   # FastAPI REST server & static web app host
├── app.py                   # Streamlit web dashboard
├── config.py                # LLM provider configuration & fallback manager
├── models.py                # Pydantic schemas & state models
├── state_manager.py         # Conversation state persistence
├── tools.py                 # Tool prompt summaries
├── static/                  # Single-Page Web Application frontend
│   ├── index.html           # Web app structure
│   ├── styles.css           # UI/UX Pro Max dark mode stylesheet
│   └── app.js               # Client controller & Mermaid DAG renderer
├── design-system/           # UI/UX Pro Max Master Specification
│   └── ai-workflow-builder/
│       └── MASTER.md
├── tests/                   # Automated pytest test suite
│   └── test_workflow_builder.py
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local container orchestration
├── cloudbuild.yaml          # Google Cloud Build CI/CD pipeline
└── requirements.txt         # Python dependencies
```

---

## Step-by-Step Setup Guide

Follow these steps sequentially to set up, configure, and run the project locally.

### Step 1: Clone Repository and Navigate to Workspace

```bash
git clone https://github.com/KeerthikVarman/chatbot_automation.git
cd chatbot_automation
```

### Step 2: Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install All Project Dependencies

Install all required Python packages specified in `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory of the project:

```env
OPENROUTER_API_KEY="your_openrouter_api_key_here"
OPENROUTER_MODEL="openai/gpt-oss-20b"
```

*Optional alternative providers:*
```env
GROQ_API_KEY="your_groq_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"
```

---

## Running the Applications

### Option A: Run Streamlit Interactive Web Dashboard

Launch the Streamlit interface on `http://localhost:8501`:

```bash
streamlit run app.py
```

### Option B: Run FastAPI Server & Single-Page Web Client

Launch the FastAPI server and web client on `http://localhost:8000`:

```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```

- **Interactive Web App**: Open `http://localhost:8000/` in your browser.
- **REST API Swagger Documentation**: Open `http://localhost:8000/docs`.

---

## Running Automated Tests

Run the full `pytest` test suite to verify all 7 scenario test cases:

```bash
pytest -v
```

---

## Docker Container Deployment

### Local Docker Compose Run

```bash
docker compose up --build
```

### Manual Docker Build and Run

```bash
docker build -t ai-workflow-builder:latest .
docker run -d -p 8000:8000 --env-file .env --name workflow_builder ai-workflow-builder:latest
```

---

## Google Cloud Build & Cloud Run CI/CD

Submit the Cloud Build pipeline to deploy to Google Artifact Registry and Cloud Run:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Serves the interactive HTML5/JS Web Application |
| `/chat` | `POST` | Processes user prompt turn and returns clarification or workflow |
| `/conversations/{id}` | `GET` | Retrieves session state for visual inspection |
| `/conversations/{id}/reset` | `POST` | Resets state for a given conversation ID |
| `/health` | `GET` | Health check endpoint |

---

## License

MIT License.
