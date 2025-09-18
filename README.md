# AI Skill Gap Analyst

A comprehensive CV skill gap analysis system powered by LangGraph and multi-agent architecture.

## Features

- CV parsing with spaCy NER integration
- Intelligent skill analysis and gap identification
- Market intelligence gathering
- Professional report generation
- Multi-mode operation (rule-based and LLM-powered)

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python main.py analyze path/to/cv.pdf "Target Role"
```

## Environment Variables

- `USE_SPACY_PARSER=true` - Enable spaCy NER parsing
- `USE_LLM_ANALYST=true` - Enable LLM-powered skill analysis
- `USE_RAG=true` - Enable RAG-powered market intelligence
- `USE_LLM_REPORT=true` - Enable LLM-powered report generation
