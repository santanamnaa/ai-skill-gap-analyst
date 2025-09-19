# AI Skill Gap Analyst

This project is a CV skill gap analysis system I built using a multi-agent architecture with LangGraph. It can analyze a CV against a target job role and provide a detailed report, even pulling in real-time market data to keep the analysis relevant.

## Features

- **Multi-Agent Architecture**: The system uses a pipeline of agents: CV Parser → Skill Analyst → Market Intelligence → Report Generator.
- **Real-time Market Data**: Can connect to job market APIs (like JSearch) to analyze current job demands.
- **Intelligent Skill Analysis**: Identifies not just the skills explicitly listed, but also skills that are implied by the experience described.
- **Dual-mode Operations**: It has a core rule-based system that works offline, but can be enhanced with LLMs (like GPT or Claude) for deeper analysis.
- **Professional Reports**: Generates a personalized report with an upskilling roadmap and learning resources.
- **PDF Support**: Can process both plain text and PDF CVs.
- **Flexible Configuration**: Easy to switch between modes using environment variables.

## Quick Start

### 1. Installation

First, you'll need to clone the repository and install the dependencies. I'm using `uv` for package management as it's quite fast.

```bash
# Clone the repository
git clone <repository-url>
cd ai-skill-gap-analyst

# Install dependencies using uv
uv sync
```

### 2. Configuration

The application uses a `.env` file to manage API keys and other settings. You can start by copying the example file:

```bash
# Create a .env file from the example
cp .env.example .env
```

Now, open the `.env` file and add your API keys. 

#### Market Intelligence API (for RAG mode)

To pull in live job data, you'll need an API key from a service like JSearch. They have a free tier that's good for development.

1.  Go to [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) and sign up.
2.  Subscribe to the free tier and get your API key.
3.  Add it to your `.env` file:
    ```
    RAPIDAPI_KEY="your_jsearch_api_key_here"
    ```

#### LLM Enhancement (Optional)

For more advanced analysis, you can connect an LLM provider.

-   **OpenAI**: Get your key from the [OpenAI Platform](https://platform.openai.com/api-keys) and add `OPENAI_API_KEY="..."` to your `.env` file.
-   **Anthropic**: Get your key from the [Anthropic Console](https://console.anthropic.com/) and add `ANTHROPIC_API_KEY="..."`.

### 3. Usage

#### Web Interface (Recommended)

This is the easiest way to use the application.

```bash
# Start the web app
uv run python app.py
```

Then open your browser to `http://localhost:5001`. The interface allows you to upload a CV, select a role, and see the analysis logs in real-time.

#### Command Line Interface

You can also run the analysis directly from the command line.

```bash
# Basic analysis using rule-based system
uv run python main.py analyze "path/to/your/cv.pdf" "Senior AI Engineer"

# Enable RAG mode for live market data
USE_RAG=true uv run python main.py analyze "path/to/your/cv.pdf" "Senior AI Engineer"

# Enable LLM-powered analysis (if key is set)
USE_LLM_ANALYST=true uv run python main.py analyze "path/to/your/cv.pdf" "Senior AI Engineer"
```

## Architecture

The system is built around a simple pipeline of agents that pass the analysis state from one to the next.

```
CV Input → CV Parser → Skill Analyst → Market Intelligence → Report Generator
```

When RAG mode is enabled, the `Market Intelligence` agent calls external APIs to get real-time job data.

## Configuration Details

You can control the application's behavior using environment variables in the `.env` file:

-   `USE_RAG=true`: Enables the call to the JSearch API for live market data.
-   `USE_LLM_ANALYST=true`: Uses an LLM for the skill analysis part. Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.
-   `USE_LLM_REPORT=true`: Uses an LLM to generate the final report.
-   `USE_SPACY_PARSER=true`: Uses the spaCy library for more advanced CV parsing.

If an API key is missing or a feature is disabled, the system will gracefully fall back to its internal rule-based methods, so it can always produce a result.
