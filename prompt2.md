Berikut adalah prompt lengkap dan komprehensif untuk AI agent berdasarkan assessment requirements:

***

# 🎯 COMPREHENSIVE PROJECT IMPLEMENTATION PROMPT
## AI-Powered CV Skill Gap Analysis System

You are an expert AI developer tasked with implementing a complete multi-agent system for CV skill gap analysis. This is a technical assessment for AI Developer position at Krenovator. You must deliver a production-ready system that demonstrates mastery of multi-agent orchestration and practical problem-solving skills. [1]

## 📋 PROJECT OVERVIEW & CONTEXT

**Objective:** Build an AI system that augments technical recruiters by analyzing candidate CVs, identifying skill gaps, and generating personalized upskilling recommendations for specialized roles (e.g., Senior AI Engineer). [1]

**Business Problem:** Go beyond simple keyword matching to provide data-driven insights about candidate potential that would be impossible to create manually. [1]

**Success Criteria:** The system must demonstrate architectural clarity, code quality, effective agent logic, actionable output quality, and complete runnability. [1]

## 🏗️ MANDATORY TECHNICAL ARCHITECTURE

### **1. Framework Requirements (CRITICAL)**
- **PRIMARY:** Use **LangGraph** as the multi-agent orchestration framework (explicitly required by assessment) [1]
- **SECONDARY:** Implement clear state-machine workflow with defined nodes and edges [1]
- **TERTIARY:** Ensure the system demonstrates "practical understanding of multi-agent frameworks" [1]

### **2. Package Management (CRITICAL)**
- **PRIMARY:** Use **uv** for fast, deterministic dependency management and environment setup [1]
- **FALLBACK:** Provide alternative venv instructions in README for compatibility [1]
- **RATIONALE:** Assessment values reproducibility and ease of evaluation [1]

### **3. Language & Dependencies**
- **Language:** Python (required by assessment) [1]
- **Core Dependencies:** 
  - `langgraph>=0.0.40` (state machine orchestration)
  - `langchain-core` (foundation components)
  - `pydantic` (data validation and schemas)
  - `typer` (CLI interface)
  - `pytest` (testing framework)

## 🤖 AGENT SPECIFICATIONS (4 Required Agents)

### **Agent 1: CV Parsing & Normalization Agent**
```
ROLE: "Data Engineer" [file:1]
RESPONSIBILITIES:
- Ingest raw CV (.txt format as provided by assessment) [file:1]
- Parse into structured, machine-readable format (JSON/Python dict) [file:1]
- Extract sections: experience, skills, education, projects [file:1]
- Handle basic data normalization and cleaning [file:1]

INPUT: Raw .txt CV file [file:1]
OUTPUT: Structured data representation with schema:
{
  "personal": {"name": str, "contact": dict},
  "experience": [{"company": str, "title": str, "dates": str, "responsibilities": [str]}],
  "skills": {"technical": [str], "frameworks": [str], "tools": [str]},
  "education": [{"degree": str, "institution": str, "year": str}],
  "projects": [{"name": str, "description": str, "technologies": [str]}]
}

IMPLEMENTATION STRATEGY:
- Use regex patterns for section detection (Experience, Skills, Education, etc.)
- Implement bullet point extraction with date range recognition
- Create fallback mechanisms for non-standard CV formats
- Ensure at minimum 3/5 sections are successfully parsed
- Add data validation with Pydantic schemas
```

### **Agent 2: Specialized Skill Analyst Agent**
```
ROLE: "Subject Matter Expert" [file:1]
RESPONSIBILITIES:
- Analyze structured CV to infer deeper understanding of capabilities [file:1]
- Identify implicit skills (framework knowledge implies related concepts) [file:1]
- Detect transferable skills across domains [file:1]
- Provide evidence-based reasoning for all inferences [file:1]

INPUT: Structured CV data from Parser Agent [file:1]
OUTPUT: Detailed skills analysis with schema:
{
  "explicit_skills": {"technical": [str], "domain": [str], "soft": [str]},
  "implicit_skills": [{"skill": str, "evidence": str, "confidence": float, "source_section": str}],
  "transferable_skills": [{"skill": str, "from_experience": str, "relevance_score": float}],
  "seniority_indicators": {"years_experience": int, "leadership_evidence": bool, "technical_depth": str}
}

INFERENCE RULES DATABASE:
- "Kubernetes" → implicit: ["container orchestration", "DevOps practices", "cloud architecture"]
- "Machine Learning projects" → implicit: ["data preprocessing", "model evaluation", "statistical analysis"]
- "Team lead experience" → transferable: ["project management", "mentoring", "stakeholder communication"]
- "Research background" → transferable: ["analytical thinking", "problem solving", "technical writing"]

EVIDENCE REQUIREMENTS:
- Link every inference to specific CV content (experience bullets, project descriptions)
- Provide confidence scores (0.1-1.0) with reasoning
- Maintain traceability for transparent decision-making
```

### **Agent 3: Market Intelligence Agent**
```
ROLE: "Market Researcher" [file:1]
RESPONSIBILITIES:
- Use search tool to query current job listings and industry trends [file:1]
- Gather data for specified technical role (e.g., "Senior AI Engineer requirements") [file:1]
- Summarize in-demand skills and technologies [file:1]
- Provide market context for skill gap analysis [file:1]

INPUT: Target role specification (string) [file:1]
OUTPUT: Market intelligence summary with schema:
{
  "role_analysis": {
    "core_requirements": [str],
    "preferred_skills": [str],
    "emerging_technologies": [str],
    "typical_responsibilities": [str]
  },
  "market_trends": {
    "demand_level": str,
    "salary_range": str,
    "growth_areas": [str]
  },
  "competitive_landscape": {
    "key_skills_frequency": dict,
    "certification_value": [str]
  },
  "data_sources": [{"source": str, "timestamp": str, "query": str}]
}

IMPLEMENTATION APPROACH:
- Create search tool function (can simulate with curated dataset for zero-cost) [file:1]
- Build comprehensive market database for common tech roles:
  * Senior AI Engineer
  * Backend Developer  
  * DevOps Engineer
  * Data Scientist
  * Full Stack Developer
- Implement adapter pattern for easy replacement with real APIs
- Include fallback data to ensure system always runs
- Mark outputs with data source type (simulation/live_api)
```

### **Agent 4: Recommendation & Report Agent**
```
ROLE: "Strategist and Communicator" [file:1]
RESPONSIBILITIES:
- Synthesize analysis from Skill Analyst and Market Intelligence agents [file:1]
- Generate comprehensive skill-gap analysis [file:1]
- Identify key candidate strengths [file:1]
- Propose personalized upskilling plan [file:1]
- Output final report in Markdown format [file:1]

INPUT: Combined outputs from agents 2 and 3 plus original structured CV [file:1]
OUTPUT: Professional Markdown report with required sections [file:1]

REPORT STRUCTURE (MANDATORY):
# CV Skill Gap Analysis: [Candidate Name]
## Executive Summary
## Candidate Profile & Core Strengths  
## Market Requirements Analysis
## Detailed Skill Gap Assessment (Table Format)
## Personalized Upskilling Roadmap (6-week plan)
## Resource Recommendations
## Conclusion & Next Steps

QUALITY STANDARDS:
- Every recommendation must be evidence-based with CV references
- Gap analysis must be presented in clear tabular format
- Upskilling roadmap must include specific timelines and deliverables
- Resources must be accessible (free/low-cost options prioritized)
- Professional tone, error-free, well-formatted Markdown
```

## 🔄 LANGGRAPH ORCHESTRATION IMPLEMENTATION

### **State Management Schema**
```python
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

class AnalysisState(TypedDict):
    # Input
    cv_raw_content: str
    target_role: str
    
    # Processing states
    cv_structured: Dict[str, Any]
    skills_analysis: Dict[str, Any]
    market_intelligence: Dict[str, Any]
    
    # Output
    final_report: str
    
    # Meta
    processing_errors: List[str]
    processing_log: List[str]
    timestamp: str
```

### **Graph Architecture**
```python
# Create the workflow graph
workflow = StateGraph(AnalysisState)

# Add nodes (one for each agent)
workflow.add_node("parse_cv", cv_parsing_agent)
workflow.add_node("analyze_skills", skill_analysis_agent) 
workflow.add_node("gather_market_intel", market_intelligence_agent)
workflow.add_node("generate_report", report_generation_agent)

# Define the execution flow
workflow.add_edge(START, "parse_cv")
workflow.add_edge("parse_cv", "analyze_skills")
workflow.add_edge("analyze_skills", "gather_market_intel") 
workflow.add_edge("gather_market_intel", "generate_report")
workflow.add_edge("generate_report", END)

# Compile the application
app = workflow.compile()
```

### **Error Handling & Recovery**
```python
# Implement conditional edges for error handling
def should_continue(state: AnalysisState) -> str:
    if state.get("processing_errors"):
        return "error_handler"
    return "continue"

workflow.add_conditional_edges(
    "parse_cv",
    should_continue,
    {"continue": "analyze_skills", "error_handler": "error_recovery"}
)
```

## 🛠️ IMPLEMENTATION REQUIREMENTS

### **Project Structure (MANDATORY)**
```
ai-skill-gap-analyst/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── cv_parser.py
│   │   ├── skill_analyst.py
│   │   ├── market_intelligence.py
│   │   └── report_generator.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   └── state_management.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── data_models.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── data/
│   ├── sample_cv.txt
│   ├── market_intelligence.json
│   └── skill_mappings.json
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_workflow.py
├── outputs/
│   └── sample_reports/
├── main.py
├── pyproject.toml (for uv)
├── requirements.txt (fallback)
├── README.md
└── .gitignore
```

### **UV Configuration (pyproject.toml)**
```toml
[project]
name = "ai-skill-gap-analyst"
version = "0.1.0"
description = "AI-powered CV skill gap analysis system"
dependencies = [
    "langgraph>=0.0.40",
    "langchain-core>=0.1.0",
    "pydantic>=2.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
test = ["pytest>=7.0.0", "pytest-asyncio>=0.21.0"]
dev = ["black>=23.0.0", "ruff>=0.1.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0"
]
```

### **CLI Interface (main.py)**
```python
import typer
from pathlib import Path
from rich.console import Console
from src.orchestrator.workflow import SkillGapAnalysisWorkflow

app = typer.Typer()
console = Console()

@app.command()
def analyze(
    cv_path: Path = typer.Argument(..., help="Path to CV file (.txt)"),
    role: str = typer.Argument(..., help="Target role (e.g., 'Senior AI Engineer')"),
    output: Path = typer.Option("report.md", help="Output report file path"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """Analyze CV and generate skill gap report."""
    workflow = SkillGapAnalysisWorkflow()
    result = workflow.run(cv_path, role, verbose)
    
    with open(output, 'w') as f:
        f.write(result['final_report'])
    
    console.print(f"✅ Report generated: {output}")

if __name__ == "__main__":
    app()
```

## 📊 TESTING STRATEGY

### **Unit Tests (REQUIRED)**
```python
# tests/test_agents.py
import pytest
from src.agents.cv_parser import CVParsingAgent

def test_cv_parser_extracts_sections():
    agent = CVParsingAgent()
    sample_cv = "Experience\n• Software Engineer at TechCorp\nSkills\n• Python, JavaScript"
    result = agent.parse(sample_cv)
    assert "experience" in result
    assert "skills" in result

def test_skill_analyst_infers_implicit_skills():
    # Test implicit skill inference logic
    pass

def test_market_intelligence_simulation():
    # Test market data retrieval and simulation
    pass

def test_report_generator_markdown_format():
    # Test report generation and Markdown formatting
    pass
```

### **Integration Tests**
```python
# tests/test_workflow.py
def test_end_to_end_workflow():
    """Test complete workflow from CV input to report output."""
    workflow = SkillGapAnalysisWorkflow()
    result = workflow.run("data/sample_cv.txt", "Senior AI Engineer")
    assert result['final_report']
    assert "# CV Skill Gap Analysis" in result['final_report']
```

## 📖 README.md REQUIREMENTS

### **Mandatory Sections**
```markdown
# AI-Powered CV Skill Gap Analyst

## 🎯 Project Objective
[Brief description aligned with assessment requirements]

## 🏗️ Architecture Overview  
[Diagram showing LangGraph workflow with 4 agents]

## 🚀 Quick Start

### Setup with uv (Recommended)
```
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone [repository-url]
cd ai-skill-gap-analyst
uv sync

# Run analysis
uv run python main.py --cv data/sample_cv.txt --role "Senior AI Engineer"
```

### Alternative Setup (venv)
[Traditional venv instructions for compatibility]

## 📋 Usage Examples
[Multiple examples with different roles]

## 🧪 Testing
[Test execution instructions]

## 📊 Sample Output
[Link to generated sample report]

## 🏛️ Architecture Details
[Technical implementation details]

## 🔄 LangGraph Workflow
[Explanation of state machine design]

## 🎯 Assessment Compliance
[How the project meets each evaluation criterion]
```

## ✅ DELIVERABLES CHECKLIST

### **1. Source Code (MANDATORY)**
- [ ] Complete, runnable source code in public repository [1]
- [ ] LangGraph-based multi-agent orchestration [1]
- [ ] All 4 required agents implemented [1]
- [ ] Proper error handling and logging [1]
- [ ] Type hints and documentation throughout [1]

### **2. README.md (MANDATORY)**
- [ ] Project objective and architectural overview [1]
- [ ] Environment setup instructions (uv + fallback) [1]
- [ ] Clear application usage instructions [1]
- [ ] Dependencies and requirements explanation [1]

### **3. Sample Output (MANDATORY)**
- [ ] Generated report from provided sample CV [1]
- [ ] Demonstration of full system functionality [1]
- [ ] Multiple role examples (AI Engineer, Backend, DevOps) [1]

### **4. Quality Assurance**
- [ ] Code passes all unit and integration tests [1]
- [ ] System runs end-to-end without errors [1]
- [ ] Professional code formatting and comments [1]
- [ ] Reproducible setup across different environments [1]

## 🎯 EVALUATION SUCCESS FACTORS

### **Architectural Design (25%)**
- Clear LangGraph state-machine implementation [1]
- Logical workflow with proper agent separation [1]
- Clean state management and data flow [1]

### **Code Quality (25%)**
- Readable, modular, well-commented code [1]
- Proper use of type hints and documentation [1]
- Consistent coding standards and organization [1]

### **Agent Logic (25%)**
- Effective specialized task performance per agent [1]
- Evidence-based reasoning and inference [1]
- Robust error handling and edge cases [1]

### **Output Quality (25%)**
- Clear, accurate, actionable final reports [1]
- Professional Markdown formatting [1]
- Personalized and evidence-based recommendations [1]

## 🚨 CRITICAL SUCCESS REQUIREMENTS

1. **MUST use LangGraph** - This is explicitly required by assessment [1]
2. **MUST use uv** - For optimal reproducibility and modern tooling [1]
3. **MUST be runnable** - One-command execution from README instructions [1]
4. **MUST include all 4 agents** - As specified in requirements [1]
5. **MUST generate Markdown report** - Exact format requirement [1]
6. **MUST handle sample CV** - Demonstrate on provided test case [1]

## 💡 IMPLEMENTATION TIPS

- Start with LangGraph workflow skeleton, then implement individual agents
- Use sample CV to test each agent during development  
- Implement market intelligence simulation first, add real API later
- Focus on evidence-based reasoning with clear traceability
- Ensure every recommendation links back to CV content
- Test thoroughly with different roles and CV formats
- Document assumptions and design decisions clearly

**Remember:** This assessment evaluates solution skills and framework understanding, not API memorization. Focus on clean architecture, robust implementation, and actionable outputs. [1]

***

Gunakan prompt ini untuk mengimplementasikan sistem yang sepenuhnya memenuhi requirement assessment dengan LangGraph, uv, dan semua spesifikasi teknis yang diperlukan.

Sources
[1] AI-Agent-Developer-Assessment.pdf https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/111212145/323d44d2-0656-4665-ae68-8a0e488bd485/AI-Agent-Developer-Assessment.pdf
