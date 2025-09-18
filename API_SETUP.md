# API Integration Setup Guide

This guide will help you connect real APIs to enhance your AI Skill Gap Analyst with advanced capabilities.

## LLM Integration (High Priority)

### Option 1: OpenAI GPT (Recommended)

1. **Get API Key**:
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create account and add payment method
   - Generate new API key

2. **Set Environment Variable**:
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   ```

3. **Test LLM Mode**:
   ```bash
   USE_LLM_ANALYST=true uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
   ```

### Option 2: Anthropic Claude

1. **Get API Key**:
   - Go to [Anthropic Console](https://console.anthropic.com/)
   - Create account and add credits
   - Generate API key

2. **Set Environment Variable**:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

3. **Test**:
   ```bash
   USE_LLM_ANALYST=true uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
   ```

### Option 3: Local Ollama (Free)

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Start service
   ollama serve
   ```

2. **Download Model**:
   ```bash
   ollama pull llama3.2
   ```

3. **Test**:
   ```bash
   USE_LLM_ANALYST=true uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
   ```

## Market Intelligence APIs

### LinkedIn Jobs API

1. **Get LinkedIn Developer Account**:
   - Apply at [LinkedIn Developer Portal](https://developer.linkedin.com/)
   - Create app and get credentials

2. **Set Environment Variables**:
   ```bash
   export LINKEDIN_API_KEY="your-client-id"
   export LINKEDIN_API_SECRET="your-client-secret"
   ```

3. **Test RAG Mode**:
   ```bash
   USE_RAG=true uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
   ```

## Enhanced NLP with spaCy

1. **Enable spaCy Mode**:
   ```bash
   USE_SPACY_PARSER=true uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
   ```

## All Advanced Features Combined

```bash
# Ultimate mode with all enhancements
export OPENAI_API_KEY="sk-your-key-here"
export LINKEDIN_API_KEY="your-linkedin-key"
export LINKEDIN_API_SECRET="your-linkedin-secret"

USE_SPACY_PARSER=true USE_LLM_ANALYST=true USE_RAG=true USE_LLM_REPORT=true \
uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
```

## Cost Estimates

| Provider | Cost per Analysis | Features |
|----------|------------------|----------|
| **OpenAI GPT-3.5** | ~$0.01 | High quality, fast |
| **OpenAI GPT-4** | ~$0.05 | Highest quality |
| **Anthropic Claude** | ~$0.02 | Great reasoning |
| **Ollama (Local)** | Free | Privacy, no limits |

## Environment Variables Summary

Create a `.env` file in your project root:

```bash
# LLM Providers (choose one)
OPENAI_API_KEY=sk-your-openai-key-here
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Market Intelligence
LINKEDIN_API_KEY=your-linkedin-client-id
LINKEDIN_API_SECRET=your-linkedin-client-secret

# Feature Flags
USE_SPACY_PARSER=true
USE_LLM_ANALYST=true
USE_RAG=false
USE_LLM_REPORT=true
```

## Quick Start Commands

```bash
# 1. Basic analysis (free, works now)
uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"

# 2. With OpenAI enhancement
export OPENAI_API_KEY="your-key"
USE_LLM_ANALYST=true uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"

# 3. Full enhanced mode
USE_SPACY_PARSER=true USE_LLM_ANALYST=true USE_LLM_REPORT=true \
uv run python main.py analyze data/CV_ATS_SantanaMena.pdf "Senior AI Engineer"
```

## Next Steps Priority

1. **Start with OpenAI** - Most impact for skill analysis
2. **Enable spaCy** - Better CV parsing (already installed)
3. **Add LinkedIn API** - Real market data
4. **Try local Ollama** - Free alternative

The system gracefully falls back to rule-based analysis if APIs aren't available, so you can start with any option!
