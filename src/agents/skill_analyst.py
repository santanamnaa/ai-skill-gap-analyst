"""
Specialized Skill Analyst Agent

This agent performs deep analysis of structured CV data to infer implicit and transferable skills.
Role: Subject Matter Expert in the multi-agent system.
"""

import re
from typing import List, Dict, Tuple
import logging
from datetime import datetime

from ..schemas import (
    AnalysisState, SkillsAnalysis, ImplicitSkill, TransferableSkill, 
    SeniorityIndicators, StructuredCV
)

logger = logging.getLogger(__name__)


class SkillAnalystAgent:
    """
    Skill Analyst Agent that performs deep skill analysis and inference.
    
    Analyzes structured CV data to identify implicit skills, transferable skills,
    and seniority indicators with evidence-based reasoning.
    """
    
    def __init__(self):
        # Inference rules for implicit skills
        self.inference_rules = {
            # DevOps and Infrastructure
            'kubernetes': {
                'skills': ['container orchestration', 'devops', 'cloud architecture', 'microservices'],
                'confidence': 0.9
            },
            'docker': {
                'skills': ['containerization', 'devops', 'deployment automation'],
                'confidence': 0.8
            },
            'terraform': {
                'skills': ['infrastructure as code', 'cloud architecture', 'automation'],
                'confidence': 0.9
            },
            'jenkins': {
                'skills': ['ci/cd', 'build automation', 'devops pipeline'],
                'confidence': 0.8
            },
            
            # AI/ML
            'tensorflow': {
                'skills': ['deep learning', 'neural networks', 'model training'],
                'confidence': 0.9
            },
            'pytorch': {
                'skills': ['deep learning', 'research', 'model experimentation'],
                'confidence': 0.9
            },
            'scikit-learn': {
                'skills': ['machine learning', 'data analysis', 'statistical modeling'],
                'confidence': 0.8
            },
            'hugging face': {
                'skills': ['nlp', 'transformer models', 'model fine-tuning'],
                'confidence': 0.9
            },
            'llm': {
                'skills': ['prompt engineering', 'model evaluation', 'nlp'],
                'confidence': 0.8
            },
            
            # Cloud Platforms
            'aws': {
                'skills': ['cloud computing', 'scalable architecture', 'cloud security'],
                'confidence': 0.8
            },
            'azure': {
                'skills': ['cloud computing', 'microsoft ecosystem', 'enterprise solutions'],
                'confidence': 0.8
            },
            'gcp': {
                'skills': ['cloud computing', 'google cloud services', 'data analytics'],
                'confidence': 0.8
            },
            
            # Data Engineering
            'spark': {
                'skills': ['big data processing', 'distributed computing', 'data engineering'],
                'confidence': 0.9
            },
            'kafka': {
                'skills': ['stream processing', 'event-driven architecture', 'real-time data'],
                'confidence': 0.8
            },
            'airflow': {
                'skills': ['workflow orchestration', 'data pipeline', 'automation'],
                'confidence': 0.8
            },
            
            # Web Development
            'react': {
                'skills': ['frontend development', 'component architecture', 'javascript ecosystem'],
                'confidence': 0.8
            },
            'microservices': {
                'skills': ['distributed systems', 'api design', 'system architecture'],
                'confidence': 0.9
            }
        }
        
        # Transferable skills mapping
        self.transferable_skills_map = {
            'phd': {
                'skills': ['analytical thinking', 'problem solving', 'technical writing', 'research methodology'],
                'domain': 'academic research'
            },
            'team lead': {
                'skills': ['project management', 'mentoring', 'stakeholder communication', 'conflict resolution'],
                'domain': 'leadership'
            },
            'startup': {
                'skills': ['adaptability', 'resourcefulness', 'rapid prototyping', 'cross-functional collaboration'],
                'domain': 'entrepreneurship'
            },
            'consultant': {
                'skills': ['client communication', 'problem diagnosis', 'solution design', 'presentation skills'],
                'domain': 'consulting'
            },
            'architect': {
                'skills': ['system design', 'technical strategy', 'stakeholder alignment', 'documentation'],
                'domain': 'technical architecture'
            }
        }
        
        # Seniority indicators
        self.leadership_keywords = [
            'lead', 'senior', 'principal', 'architect', 'manager', 'director',
            'team lead', 'tech lead', 'engineering manager', 'head of'
        ]
        
        self.architecture_keywords = [
            'architecture', 'design', 'system design', 'technical design',
            'scalability', 'performance optimization', 'distributed systems'
        ]
    
    def analyze_skills(self, state: AnalysisState) -> AnalysisState:
        """
        Main skill analysis function.
        
        Args:
            state: Analysis state with structured CV data
            
        Returns:
            Updated state with comprehensive skills analysis
        """
        try:
            logger.info("Starting skills analysis...")
            
            if not state.cv_structured.personal.name:
                state.add_error("No structured CV data available for skill analysis")
                return state
            
            # Initialize skills analysis
            analysis = SkillsAnalysis()
            
            # Extract explicit skills
            analysis.explicit_skills = self._extract_explicit_skills(state.cv_structured)
            
            # Infer implicit skills
            analysis.implicit_skills = self._infer_implicit_skills(state.cv_structured)
            
            # Identify transferable skills
            analysis.transferable_skills = self._identify_transferable_skills(state.cv_structured)
            
            # Analyze seniority indicators
            analysis.seniority_indicators = self._analyze_seniority(state.cv_structured)
            
            state.skills_analysis = analysis
            logger.info("Skills analysis completed successfully")
            
        except Exception as e:
            error_msg = f"Skills analysis failed: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
    def _extract_explicit_skills(self, cv: StructuredCV) -> Dict[str, List[str]]:
        """Extract explicitly mentioned skills from CV."""
        explicit_skills = {
            'tech': [],
            'domain': [],
            'soft': []
        }
        
        # Technical skills from skills section
        tech_skills = []
        tech_skills.extend(cv.skills.languages)
        tech_skills.extend(cv.skills.frameworks)
        tech_skills.extend(cv.skills.tools)
        
        # Add tech skills from projects
        for project in cv.projects:
            tech_skills.extend(project.tech_stack)
        
        explicit_skills['tech'] = list(set(tech_skills))
        
        # Domain skills from experience and education
        domain_skills = self._extract_domain_skills(cv)
        explicit_skills['domain'] = domain_skills
        
        # Soft skills from experience descriptions
        soft_skills = self._extract_soft_skills(cv)
        explicit_skills['soft'] = soft_skills
        
        return explicit_skills
    
    def _extract_domain_skills(self, cv: StructuredCV) -> List[str]:
        """Extract domain-specific skills from experience and education."""
        domain_skills = []
        
        # From job titles and company names
        for exp in cv.experience:
            title_lower = exp.title.lower()
            company_lower = exp.company.lower()
            
            # AI/ML domain
            if any(keyword in title_lower for keyword in ['ai', 'ml', 'machine learning', 'data scientist']):
                domain_skills.extend(['machine learning', 'data science', 'artificial intelligence'])
            
            # Backend development
            if any(keyword in title_lower for keyword in ['backend', 'server', 'api']):
                domain_skills.extend(['backend development', 'api development', 'server-side programming'])
            
            # Frontend development
            if any(keyword in title_lower for keyword in ['frontend', 'ui', 'ux']):
                domain_skills.extend(['frontend development', 'user interface design'])
            
            # DevOps
            if any(keyword in title_lower for keyword in ['devops', 'sre', 'infrastructure']):
                domain_skills.extend(['devops', 'infrastructure management', 'site reliability'])
            
            # Fintech
            if any(keyword in company_lower for keyword in ['bank', 'fintech', 'financial', 'trading']):
                domain_skills.extend(['financial technology', 'regulatory compliance'])
        
        # From education
        for edu in cv.education:
            degree_lower = edu.degree.lower()
            if 'computer science' in degree_lower:
                domain_skills.extend(['computer science fundamentals', 'algorithms', 'data structures'])
            elif 'engineering' in degree_lower:
                domain_skills.extend(['engineering principles', 'systematic problem solving'])
        
        return list(set(domain_skills))
    
    def _extract_soft_skills(self, cv: StructuredCV) -> List[str]:
        """Extract soft skills from experience descriptions."""
        soft_skills = []
        
        # Analyze experience bullets for soft skill indicators
        all_text = ""
        for exp in cv.experience:
            all_text += " ".join(exp.bullets) + " "
        
        # Project descriptions
        for project in cv.projects:
            all_text += project.description + " "
        
        text_lower = all_text.lower()
        
        # Leadership indicators
        if any(keyword in text_lower for keyword in ['led', 'managed', 'coordinated', 'supervised']):
            soft_skills.append('leadership')
        
        # Communication indicators
        if any(keyword in text_lower for keyword in ['presented', 'communicated', 'collaborated', 'stakeholder']):
            soft_skills.append('communication')
        
        # Problem solving indicators
        if any(keyword in text_lower for keyword in ['solved', 'optimized', 'improved', 'debugged']):
            soft_skills.append('problem solving')
        
        # Project management indicators
        if any(keyword in text_lower for keyword in ['planned', 'delivered', 'milestone', 'deadline']):
            soft_skills.append('project management')
        
        return list(set(soft_skills))
    
    def _infer_implicit_skills(self, cv: StructuredCV) -> List[ImplicitSkill]:
        """Infer implicit skills based on technologies and experience."""
        implicit_skills = []
        
        # Collect all technology mentions
        all_tech = []
        all_tech.extend(cv.skills.languages)
        all_tech.extend(cv.skills.frameworks)
        all_tech.extend(cv.skills.tools)
        
        for project in cv.projects:
            all_tech.extend(project.tech_stack)
        
        # Collect experience text for evidence
        experience_text = ""
        for exp in cv.experience:
            experience_text += f"{exp.title} at {exp.company}: " + " ".join(exp.bullets) + " "
        
        # Apply inference rules
        for tech in all_tech:
            tech_lower = tech.lower()
            if tech_lower in self.inference_rules:
                rule = self.inference_rules[tech_lower]
                
                for skill in rule['skills']:
                    # Find evidence in experience
                    evidence = self._find_evidence(tech, skill, cv)
                    
                    implicit_skill = ImplicitSkill(
                        skill=skill,
                        evidence=evidence,
                        confidence=rule['confidence']
                    )
                    implicit_skills.append(implicit_skill)
        
        # Additional inference from project complexity
        complex_projects = self._identify_complex_projects(cv)
        for project_skill in complex_projects:
            implicit_skills.append(project_skill)
        
        return implicit_skills
    
    def _find_evidence(self, tech: str, skill: str, cv: StructuredCV) -> str:
        """Find evidence for inferred skill in CV."""
        # Look for the technology in experience bullets
        for exp in cv.experience:
            for bullet in exp.bullets:
                if tech.lower() in bullet.lower():
                    return f"Used {tech} in {exp.title} role: {bullet[:100]}..."
        
        # Look in projects
        for project in cv.projects:
            if tech.lower() in project.description.lower() or tech in project.tech_stack:
                return f"Applied {tech} in project '{project.name}': {project.description[:100]}..."
        
        return f"Experience with {tech} indicates {skill} capability"
    
    def _identify_complex_projects(self, cv: StructuredCV) -> List[ImplicitSkill]:
        """Identify complex projects that indicate advanced skills."""
        complex_skills = []
        
        for project in cv.projects:
            desc_lower = project.description.lower()
            
            # Large scale indicators
            if any(keyword in desc_lower for keyword in ['scale', 'million', 'thousand', 'enterprise']):
                complex_skills.append(ImplicitSkill(
                    skill='scalable system design',
                    evidence=f"Project '{project.name}' involved large-scale implementation",
                    confidence=0.7
                ))
            
            # Performance optimization
            if any(keyword in desc_lower for keyword in ['optimize', 'performance', 'speed', 'efficiency']):
                complex_skills.append(ImplicitSkill(
                    skill='performance optimization',
                    evidence=f"Optimized performance in project '{project.name}'",
                    confidence=0.8
                ))
            
            # Research and innovation
            if any(keyword in desc_lower for keyword in ['research', 'novel', 'innovative', 'experiment']):
                complex_skills.append(ImplicitSkill(
                    skill='research and development',
                    evidence=f"Conducted research in project '{project.name}'",
                    confidence=0.7
                ))
        
        return complex_skills
    
    def _identify_transferable_skills(self, cv: StructuredCV) -> List[TransferableSkill]:
        """Identify transferable skills from various domains."""
        transferable_skills = []
        
        # Analyze job titles and experience
        all_text = ""
        for exp in cv.experience:
            all_text += f"{exp.title} {exp.company} " + " ".join(exp.bullets) + " "
        
        # Add education context
        for edu in cv.education:
            all_text += f"{edu.degree} {edu.institution} "
        
        text_lower = all_text.lower()
        
        # Apply transferable skills mapping
        for keyword, mapping in self.transferable_skills_map.items():
            if keyword in text_lower:
                for skill in mapping['skills']:
                    transferable_skill = TransferableSkill(
                        skill=skill,
                        from_domain=mapping['domain'],
                        relevance=self._assess_relevance(skill, cv)
                    )
                    transferable_skills.append(transferable_skill)
        
        return transferable_skills
    
    def _assess_relevance(self, skill: str, cv: StructuredCV) -> str:
        """Assess relevance of transferable skill to technical roles."""
        relevance_map = {
            'analytical thinking': 'High - Essential for problem-solving in technical roles',
            'problem solving': 'High - Core competency for engineering positions',
            'technical writing': 'High - Important for documentation and communication',
            'project management': 'Medium - Valuable for senior and lead positions',
            'mentoring': 'Medium - Important for senior and team lead roles',
            'stakeholder communication': 'Medium - Crucial for client-facing and senior roles',
            'adaptability': 'Medium - Valuable in fast-paced tech environments',
            'system design': 'High - Critical for architecture and senior engineering roles'
        }
        
        return relevance_map.get(skill, 'Medium - Applicable to collaborative technical work')
    
    def _analyze_seniority(self, cv: StructuredCV) -> SeniorityIndicators:
        """Analyze indicators of seniority level."""
        indicators = SeniorityIndicators()
        
        # Calculate years of experience
        current_year = datetime.now().year
        years = []
        
        for exp in cv.experience:
            if exp.dates:
                # Extract years from date ranges
                year_matches = re.findall(r'\d{4}', exp.dates)
                if len(year_matches) >= 2:
                    start_year = int(year_matches[0])
                    end_year = int(year_matches[1]) if year_matches[1] != 'present' else current_year
                    years.append(end_year - start_year)
                elif len(year_matches) == 1:
                    # Assume 1 year if only one year mentioned
                    years.append(1)
        
        indicators.years_exp = sum(years)
        
        # Check for leadership indicators
        all_text = ""
        for exp in cv.experience:
            all_text += f"{exp.title} " + " ".join(exp.bullets) + " "
        
        text_lower = all_text.lower()
        
        indicators.leadership = any(keyword in text_lower for keyword in self.leadership_keywords)
        indicators.architecture = any(keyword in text_lower for keyword in self.architecture_keywords)
        
        return indicators


def skill_analyst_node(state: AnalysisState) -> AnalysisState:
    """
    LangGraph node function for skill analysis.
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with skills analysis
    """
    analyst = SkillAnalystAgent()
    return analyst.analyze_skills(state)
