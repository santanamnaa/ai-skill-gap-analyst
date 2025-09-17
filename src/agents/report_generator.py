"""
Recommendation & Report Agent

This agent synthesizes skill analysis and market intelligence into comprehensive reports.
Role: Strategist and Communicator in the multi-agent system.
"""

from typing import List, Dict, Tuple
import logging
from datetime import datetime

from ..schemas import (
    AnalysisState, SkillLevel, Priority, Gap, 
    SkillsAnalysis, MarketIntelligence, StructuredCV
)

logger = logging.getLogger(__name__)


class ReportGeneratorAgent:
    """
    Report Generator Agent that creates comprehensive skill gap analysis reports.
    
    Synthesizes all analysis data into actionable Markdown reports with
    personalized upskilling roadmaps.
    """
    
    def __init__(self):
        # Resource recommendations database
        self.learning_resources = {
            'python': {
                'beginner': ['Python.org Tutorial', 'Codecademy Python Course', 'Automate the Boring Stuff (free book)'],
                'intermediate': ['Real Python', 'Python Tricks book', 'Effective Python'],
                'advanced': ['Fluent Python', 'Architecture Patterns with Python', 'High Performance Python']
            },
            'machine learning': {
                'beginner': ['Coursera ML Course (Andrew Ng)', 'Kaggle Learn', 'Scikit-learn documentation'],
                'intermediate': ['Hands-On Machine Learning book', 'Fast.ai course', 'Papers with Code'],
                'advanced': ['Deep Learning book (Goodfellow)', 'MLOps specialization', 'Research papers']
            },
            'docker': {
                'beginner': ['Docker Official Tutorial', 'Docker for Beginners (YouTube)', 'Play with Docker'],
                'intermediate': ['Docker Deep Dive book', 'Docker Compose documentation', 'Best practices guide'],
                'advanced': ['Docker internals', 'Multi-stage builds', 'Security scanning']
            },
            'kubernetes': {
                'beginner': ['Kubernetes Basics (official)', 'Minikube tutorial', 'kubectl cheat sheet'],
                'intermediate': ['Kubernetes in Action book', 'CKA certification prep', 'Helm documentation'],
                'advanced': ['Kubernetes operators', 'Custom controllers', 'CKAD certification']
            },
            'react': {
                'beginner': ['React Official Tutorial', 'freeCodeCamp React', 'React documentation'],
                'intermediate': ['React Hooks guide', 'Testing React apps', 'State management patterns'],
                'advanced': ['React internals', 'Performance optimization', 'Custom hooks patterns']
            }
        }
        
        # Skill priority mapping
        self.skill_priorities = {
            'critical': ['python', 'javascript', 'sql', 'git', 'docker'],
            'important': ['kubernetes', 'aws', 'react', 'tensorflow', 'postgresql'],
            'nice_to_have': ['graphql', 'redis', 'elasticsearch', 'kafka']
        }
    
    def generate_report(self, state: AnalysisState) -> AnalysisState:
        """
        Main report generation function.
        
        Args:
            state: Analysis state with all collected data
            
        Returns:
            Updated state with final report
        """
        try:
            logger.info("Starting report generation...")
            
            # Validate required data
            if not state.cv_structured.personal.name:
                state.add_error("No candidate data available for report generation")
                return state
            
            if not state.target_role:
                state.add_error("No target role specified for report generation")
                return state
            
            # Generate report sections
            report_sections = []
            
            # Executive Summary
            report_sections.append(self._generate_executive_summary(state))
            
            # Candidate Profile
            report_sections.append(self._generate_candidate_profile(state))
            
            # Market Requirements Analysis
            report_sections.append(self._generate_market_analysis(state))
            
            # Skill Gap Assessment
            report_sections.append(self._generate_skill_gap_assessment(state))
            
            # Upskilling Roadmap
            report_sections.append(self._generate_upskilling_roadmap(state))
            
            # Resource Recommendations
            report_sections.append(self._generate_resource_recommendations(state))
            
            # Combine all sections
            final_report = "\n\n".join(report_sections)
            
            state.final_report = final_report
            logger.info("Report generation completed successfully")
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
    def _generate_executive_summary(self, state: AnalysisState) -> str:
        """Generate executive summary section."""
        candidate_name = state.cv_structured.personal.name or "Candidate"
        target_role = state.target_role
        
        # Calculate key metrics
        total_skills = len(state.skills_analysis.explicit_skills.get('tech', []))
        implicit_skills_count = len(state.skills_analysis.implicit_skills)
        years_exp = state.skills_analysis.seniority_indicators.years_exp
        
        # Identify top strengths
        strengths = self._identify_top_strengths(state)
        
        # Identify critical gaps
        gaps = self._identify_critical_gaps(state)
        
        summary = f"""# CV Skill Gap Analysis: {candidate_name}

## Executive Summary

**Candidate Overview:** {candidate_name} is a professional with {years_exp} years of experience seeking to transition into or advance in the {target_role} role. Our analysis identified {total_skills} explicit technical skills and {implicit_skills_count} additional implicit capabilities.

**Key Strengths:** {candidate_name} demonstrates strong capabilities in {', '.join(strengths[:3])}. The candidate shows {self._assess_seniority_level(state)} level experience with evidence of {self._get_leadership_indicator(state)}.

**Primary Recommendations:** To successfully transition to {target_role}, we recommend focusing on {len(gaps)} critical skill areas over the next 6-8 weeks. The highest priority areas are {', '.join(gaps[:3])}. With focused learning and practical application, {candidate_name} can bridge these gaps and become competitive for {target_role} positions.

**Market Outlook:** The {target_role} market shows {state.market_intelligence.market_insights.demand_level.lower()} demand with salary ranges of {state.market_intelligence.market_insights.salary_range}. This presents excellent opportunities for career growth."""
        
        return summary
    
    def _generate_candidate_profile(self, state: AnalysisState) -> str:
        """Generate candidate profile section."""
        cv = state.cv_structured
        analysis = state.skills_analysis
        
        # Strengths with evidence
        strengths_section = "### Strengths\n"
        
        # Technical strengths
        tech_skills = analysis.explicit_skills.get('tech', [])
        if tech_skills:
            strengths_section += f"- **Technical Foundation**: Proficient in {len(tech_skills)} technologies including {', '.join(tech_skills[:5])}\n"
        
        # Experience-based strengths
        if analysis.seniority_indicators.leadership:
            strengths_section += "- **Leadership Experience**: Demonstrated leadership capabilities in previous roles\n"
        
        if analysis.seniority_indicators.architecture:
            strengths_section += "- **System Design**: Experience with architectural and system design decisions\n"
        
        # Implicit skills strengths
        high_confidence_skills = [skill.skill for skill in analysis.implicit_skills if skill.confidence > 0.8]
        if high_confidence_skills:
            strengths_section += f"- **Advanced Capabilities**: Strong evidence of {', '.join(high_confidence_skills[:3])}\n"
        
        # Current skill set table
        skills_table = self._generate_skills_table(analysis)
        
        profile = f"""## Candidate Profile

{strengths_section}

### Current Skill Set
{skills_table}

### Experience Summary
- **Total Experience**: {analysis.seniority_indicators.years_exp} years
- **Leadership Roles**: {'Yes' if analysis.seniority_indicators.leadership else 'No'}
- **Architecture Experience**: {'Yes' if analysis.seniority_indicators.architecture else 'No'}
- **Key Projects**: {len(cv.projects)} documented projects with diverse technology stacks"""
        
        return profile
    
    def _generate_market_analysis(self, state: AnalysisState) -> str:
        """Generate market requirements analysis section."""
        market = state.market_intelligence
        target_role = state.target_role
        
        # Core skills analysis
        core_skills = market.role_requirements.core_skills
        preferred_skills = market.role_requirements.preferred_skills
        emerging_trends = market.role_requirements.emerging_trends
        
        analysis = f"""## Market Requirements: {target_role}

### Current Market Landscape
The {target_role} position is experiencing **{market.market_insights.demand_level.lower()}** demand in the current market. Companies are actively seeking professionals with a combination of foundational technical skills and emerging technology expertise.

**Salary Range**: {market.market_insights.salary_range}

### Core Requirements ({len(core_skills)} skills)
{self._format_skill_list(core_skills)}

### Preferred Qualifications ({len(preferred_skills)} skills)
{self._format_skill_list(preferred_skills)}

### Emerging Trends ({len(emerging_trends)} areas)
{self._format_skill_list(emerging_trends)}

### Growth Areas
The market is particularly focused on: {', '.join(market.market_insights.growth_areas)}

**Technology Stack Popularity:**
- **Languages**: {', '.join(market.tech_stack_popularity.language[:5])}
- **Frameworks**: {', '.join(market.tech_stack_popularity.framework[:5])}
- **Tools**: {', '.join(market.tech_stack_popularity.tools[:5])}"""
        
        return analysis
    
    def _generate_skill_gap_assessment(self, state: AnalysisState) -> str:
        """Generate skill gap assessment table."""
        # Calculate gaps
        gaps = self._calculate_skill_gaps(state)
        
        # Create table
        table_header = "| Required Skill | Current Level | Gap | Priority | Evidence |\n|----------------|---------------|-----|----------|----------|\n"
        
        table_rows = []
        for gap in gaps:
            evidence = gap.get('evidence', 'Not demonstrated in CV')
            if len(evidence) > 50:
                evidence = evidence[:47] + "..."
            
            row = f"| {gap['skill']} | {gap['current_level']} | {gap['gap_level']} | {gap['priority']} | {evidence} |"
            table_rows.append(row)
        
        assessment = f"""## Skill Gap Analysis

### Gap Summary
- **Critical Gaps**: {len([g for g in gaps if g['priority'] == 'Critical'])} skills requiring immediate attention
- **Important Gaps**: {len([g for g in gaps if g['priority'] == 'Important'])} skills for competitive advantage
- **Nice-to-Have**: {len([g for g in gaps if g['priority'] == 'Nice-to-have'])} skills for differentiation

### Detailed Gap Analysis
{table_header}{''.join(table_rows)}

### Gap Analysis Insights
{self._generate_gap_insights(gaps)}"""
        
        return assessment
    
    def _generate_upskilling_roadmap(self, state: AnalysisState) -> str:
        """Generate 6-week upskilling roadmap."""
        gaps = self._calculate_skill_gaps(state)
        critical_gaps = [g for g in gaps if g['priority'] == 'Critical']
        important_gaps = [g for g in gaps if g['priority'] == 'Important']
        
        roadmap = f"""## Upskilling Roadmap (6-Week Plan)

### Phase 1 (Weeks 1-2): Foundation Building
**Focus**: Critical technical skills

**Learning Goals:**
{self._format_learning_goals(critical_gaps[:2])}

**Deliverable**: Build a simple project demonstrating {critical_gaps[0]['skill'] if critical_gaps else 'core skills'}

### Phase 2 (Weeks 3-4): Skill Integration
**Focus**: Combining foundational skills with practical application

**Learning Goals:**
{self._format_learning_goals(critical_gaps[2:4] if len(critical_gaps) > 2 else important_gaps[:2])}

**Deliverable**: Extend Phase 1 project with new technologies and deploy to cloud platform

### Phase 3 (Weeks 5-6): Advanced Concepts & Portfolio
**Focus**: Advanced skills and portfolio development

**Learning Goals:**
{self._format_learning_goals(important_gaps[:2])}

**Deliverable**: Complete portfolio project showcasing multiple skills, write technical blog post

### Success Metrics
- [ ] Complete all hands-on projects
- [ ] Demonstrate proficiency in {len(critical_gaps)} critical skills
- [ ] Build portfolio with 2-3 substantial projects
- [ ] Contribute to open source project (optional)
- [ ] Network with professionals in target role"""
        
        return roadmap
    
    def _generate_resource_recommendations(self, state: AnalysisState) -> str:
        """Generate curated resource recommendations."""
        gaps = self._calculate_skill_gaps(state)
        critical_skills = [g['skill'].lower() for g in gaps if g['priority'] == 'Critical']
        
        resources = """## Recommended Resources

### Free Learning Platforms
- **Coursera**: Audit courses for free, certificates available for fee
- **edX**: MIT and Harvard courses, free audit option
- **freeCodeCamp**: Comprehensive web development curriculum
- **Kaggle Learn**: Micro-courses in data science and ML
- **YouTube**: Channels like Traversy Media, Tech with Tim, Sentdex

### Hands-On Practice
- **GitHub**: Build portfolio, contribute to open source
- **LeetCode/HackerRank**: Algorithm and coding practice
- **Kaggle**: Data science competitions and datasets
- **AWS Free Tier**: Cloud platform experimentation
- **Docker Hub**: Container experimentation

### Skill-Specific Resources"""
        
        # Add specific resources for critical skills
        for skill in critical_skills[:5]:  # Top 5 critical skills
            if skill in self.learning_resources:
                resources += f"\n\n#### {skill.title()}\n"
                skill_resources = self.learning_resources[skill]
                for level, resource_list in skill_resources.items():
                    resources += f"**{level.title()}**: {', '.join(resource_list)}\n"
        
        resources += """

### Professional Development
- **LinkedIn Learning**: Professional skills and networking
- **Meetup.com**: Local tech meetups and networking events
- **Dev.to**: Technical articles and community
- **Stack Overflow**: Problem-solving and community support
- **Podcasts**: Software Engineering Daily, Talk Python to Me

### Certification Paths (Optional)
- **AWS Certified Solutions Architect**: Cloud architecture
- **Google Cloud Professional**: GCP expertise
- **Certified Kubernetes Administrator (CKA)**: Container orchestration
- **TensorFlow Developer Certificate**: Machine learning"""
        
        return resources
    
    def _identify_top_strengths(self, state: AnalysisState) -> List[str]:
        """Identify candidate's top strengths."""
        strengths = []
        
        # Technical skills
        tech_skills = state.skills_analysis.explicit_skills.get('tech', [])
        if tech_skills:
            strengths.extend(tech_skills[:3])
        
        # High-confidence implicit skills
        implicit_skills = [skill.skill for skill in state.skills_analysis.implicit_skills if skill.confidence > 0.8]
        strengths.extend(implicit_skills[:2])
        
        # Domain expertise
        domain_skills = state.skills_analysis.explicit_skills.get('domain', [])
        strengths.extend(domain_skills[:2])
        
        return strengths[:5]  # Top 5 strengths
    
    def _identify_critical_gaps(self, state: AnalysisState) -> List[str]:
        """Identify critical skill gaps."""
        market_core = set(skill.lower() for skill in state.market_intelligence.role_requirements.core_skills)
        candidate_tech = set(skill.lower() for skill in state.skills_analysis.explicit_skills.get('tech', []))
        
        critical_gaps = list(market_core - candidate_tech)
        return critical_gaps[:5]  # Top 5 gaps
    
    def _assess_seniority_level(self, state: AnalysisState) -> str:
        """Assess candidate's seniority level."""
        years = state.skills_analysis.seniority_indicators.years_exp
        leadership = state.skills_analysis.seniority_indicators.leadership
        architecture = state.skills_analysis.seniority_indicators.architecture
        
        if years >= 7 or (years >= 5 and leadership and architecture):
            return "senior"
        elif years >= 3 or (years >= 2 and (leadership or architecture)):
            return "mid-level"
        else:
            return "junior"
    
    def _get_leadership_indicator(self, state: AnalysisState) -> str:
        """Get leadership indicator text."""
        indicators = state.skills_analysis.seniority_indicators
        
        if indicators.leadership and indicators.architecture:
            return "both leadership and technical architecture experience"
        elif indicators.leadership:
            return "leadership and team management experience"
        elif indicators.architecture:
            return "technical architecture and system design experience"
        else:
            return "strong individual contributor capabilities"
    
    def _generate_skills_table(self, analysis: SkillsAnalysis) -> str:
        """Generate current skills table."""
        table = "| Category | Skills | Level |\n|----------|--------|-------|\n"
        
        # Technical skills
        tech_skills = analysis.explicit_skills.get('tech', [])
        if tech_skills:
            level = self._determine_skill_level(len(tech_skills), analysis.seniority_indicators.years_exp)
            table += f"| Technical | {', '.join(tech_skills[:8])} | {level} |\n"
        
        # Domain skills
        domain_skills = analysis.explicit_skills.get('domain', [])
        if domain_skills:
            table += f"| Domain | {', '.join(domain_skills)} | Intermediate |\n"
        
        # Soft skills
        soft_skills = analysis.explicit_skills.get('soft', [])
        if soft_skills:
            table += f"| Soft Skills | {', '.join(soft_skills)} | Demonstrated |\n"
        
        return table
    
    def _determine_skill_level(self, skill_count: int, years_exp: int) -> str:
        """Determine skill level based on count and experience."""
        if years_exp >= 5 and skill_count >= 10:
            return "Senior"
        elif years_exp >= 3 and skill_count >= 6:
            return "Mid-level"
        else:
            return "Junior"
    
    def _format_skill_list(self, skills: List[str]) -> str:
        """Format skill list as bullet points."""
        return '\n'.join([f"- {skill}" for skill in skills])
    
    def _calculate_skill_gaps(self, state: AnalysisState) -> List[Dict]:
        """Calculate detailed skill gaps."""
        gaps = []
        
        # Get market requirements
        core_skills = state.market_intelligence.role_requirements.core_skills
        preferred_skills = state.market_intelligence.role_requirements.preferred_skills
        
        # Get candidate skills
        candidate_skills = set()
        candidate_skills.update(skill.lower() for skill in state.skills_analysis.explicit_skills.get('tech', []))
        candidate_skills.update(skill.skill.lower() for skill in state.skills_analysis.implicit_skills)
        
        # Analyze core skills gaps
        for skill in core_skills:
            skill_lower = skill.lower()
            gap_info = {
                'skill': skill,
                'current_level': 'None',
                'gap_level': 'High',
                'priority': 'Critical',
                'evidence': 'Not found in CV'
            }
            
            if skill_lower in candidate_skills:
                gap_info['current_level'] = 'Basic'
                gap_info['gap_level'] = 'Medium'
                gap_info['priority'] = 'Important'
                gap_info['evidence'] = self._find_skill_evidence(skill, state)
            
            gaps.append(gap_info)
        
        # Analyze preferred skills gaps
        for skill in preferred_skills[:5]:  # Limit to top 5
            skill_lower = skill.lower()
            if skill_lower not in candidate_skills:
                gap_info = {
                    'skill': skill,
                    'current_level': 'None',
                    'gap_level': 'Medium',
                    'priority': 'Nice-to-have',
                    'evidence': 'Not demonstrated in CV'
                }
                gaps.append(gap_info)
        
        return gaps
    
    def _find_skill_evidence(self, skill: str, state: AnalysisState) -> str:
        """Find evidence for a skill in the CV."""
        skill_lower = skill.lower()
        
        # Check explicit skills
        if skill_lower in [s.lower() for s in state.skills_analysis.explicit_skills.get('tech', [])]:
            return f"Listed in technical skills section"
        
        # Check implicit skills
        for implicit_skill in state.skills_analysis.implicit_skills:
            if skill_lower in implicit_skill.skill.lower():
                return implicit_skill.evidence[:100] + "..."
        
        # Check experience
        for exp in state.cv_structured.experience:
            for bullet in exp.bullets:
                if skill_lower in bullet.lower():
                    return f"Used in {exp.title}: {bullet[:80]}..."
        
        return "Skill presence inferred from related technologies"
    
    def _generate_gap_insights(self, gaps: List[Dict]) -> str:
        """Generate insights from gap analysis."""
        critical_count = len([g for g in gaps if g['priority'] == 'Critical'])
        
        if critical_count == 0:
            return "**Strong Match**: Candidate demonstrates most required skills for the target role."
        elif critical_count <= 3:
            return f"**Good Foundation**: {critical_count} critical gaps identified. With focused learning, candidate can become competitive within 6-8 weeks."
        else:
            return f"**Significant Gaps**: {critical_count} critical areas need development. Recommend extended learning period of 10-12 weeks."
    
    def _format_learning_goals(self, gaps: List[Dict]) -> str:
        """Format learning goals for roadmap phases."""
        if not gaps:
            return "- Continue strengthening existing skills\n- Explore advanced concepts in current tech stack"
        
        goals = []
        for gap in gaps[:2]:  # Max 2 goals per phase
            skill = gap['skill']
            goals.append(f"- Master {skill} fundamentals and complete hands-on project")
        
        return '\n'.join(goals)


def report_generator_node(state: AnalysisState) -> AnalysisState:
    """
    LangGraph node function for report generation.
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with final report
    """
    generator = ReportGeneratorAgent()
    return generator.generate_report(state)
