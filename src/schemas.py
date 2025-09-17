"""
Data schemas and type definitions for the CV Skill Gap Analysis System.
Compatible with LangGraph StateGraph requirements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TypedDict
from enum import Enum


class SkillLevel(Enum):
    """Skill proficiency levels."""
    NONE = "None"
    BASIC = "Basic"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class Priority(Enum):
    """Priority levels for skill gaps."""
    CRITICAL = "Critical"
    IMPORTANT = "Important"
    NICE_TO_HAVE = "Nice-to-have"


class Gap(Enum):
    """Gap severity levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class PersonalInfo:
    """Personal information from CV."""
    name: str = ""
    contact: Dict[str, str] = field(default_factory=dict)


@dataclass
class Experience:
    """Work experience entry."""
    company: str = ""
    title: str = ""
    dates: str = ""
    bullets: List[str] = field(default_factory=list)


@dataclass
class Skills:
    """Skill categories."""
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)


@dataclass
class Education:
    """Education entry."""
    degree: str = ""
    institution: str = ""
    year: str = ""


@dataclass
class Project:
    """Project entry."""
    name: str = ""
    description: str = ""
    tech_stack: List[str] = field(default_factory=list)


@dataclass
class StructuredCV:
    """Structured CV data."""
    personal: PersonalInfo = field(default_factory=PersonalInfo)
    experience: List[Experience] = field(default_factory=list)
    skills: Skills = field(default_factory=Skills)
    education: List[Education] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)


@dataclass
class ImplicitSkill:
    """Inferred implicit skill."""
    skill: str = ""
    evidence: str = ""
    confidence: float = 0.0


@dataclass
class TransferableSkill:
    """Transferable skill from other domains."""
    skill: str = ""
    from_domain: str = ""
    relevance: str = ""


@dataclass
class SeniorityIndicators:
    """Indicators of seniority level."""
    years_exp: int = 0
    leadership: bool = False
    architecture: bool = False


@dataclass
class SkillsAnalysis:
    """Comprehensive skills analysis."""
    explicit_skills: Dict[str, List[str]] = field(default_factory=lambda: {"tech": [], "domain": [], "soft": []})
    implicit_skills: List[ImplicitSkill] = field(default_factory=list)
    transferable_skills: List[TransferableSkill] = field(default_factory=list)
    seniority_indicators: SeniorityIndicators = field(default_factory=SeniorityIndicators)


@dataclass
class RoleRequirements:
    """Market role requirements."""
    core_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    emerging_trends: List[str] = field(default_factory=list)


@dataclass
class TechStackPopularity:
    """Popular tech stack components."""
    language: List[str] = field(default_factory=list)
    framework: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)


@dataclass
class MarketInsights:
    """Market intelligence insights."""
    salary_range: str = ""
    demand_level: str = ""
    growth_areas: List[str] = field(default_factory=list)


@dataclass
class MarketIntelligence:
    """Market intelligence data."""
    role_requirements: RoleRequirements = field(default_factory=RoleRequirements)
    tech_stack_popularity: TechStackPopularity = field(default_factory=TechStackPopularity)
    market_insights: MarketInsights = field(default_factory=MarketInsights)
    source: str = "simulation"  # "simulation" or "live_api"


@dataclass
class AnalysisState:
    """Main state object for the analysis workflow."""
    cv_raw: str = ""
    cv_structured: StructuredCV = field(default_factory=StructuredCV)
    skills_analysis: SkillsAnalysis = field(default_factory=SkillsAnalysis)
    market_intelligence: MarketIntelligence = field(default_factory=MarketIntelligence)
    target_role: str = ""
    final_report: str = ""
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error to the state."""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0


# LangGraph-compatible TypedDict state
class LangGraphState(TypedDict):
    """
    LangGraph-compatible state schema for workflow orchestration.
    
    This TypedDict is required by LangGraph's StateGraph for proper
    state management and type checking.
    """
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
