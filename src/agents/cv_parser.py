"""
CV Parsing & Normalization Agent

This agent parses raw CV text files into structured JSON/dict format.
Role: Data Engineer in the multi-agent system.
"""

import re
from typing import List, Dict, Optional
import logging
from datetime import datetime

from ..schemas import (
    AnalysisState, StructuredCV, PersonalInfo, Experience, 
    Skills, Education, Project
)

logger = logging.getLogger(__name__)


class CVParserAgent:
    """
    CV Parser Agent that extracts structured data from raw CV text.
    
    Handles various CV formats and normalizes the extracted information.
    """
    
    def __init__(self):
        self.section_patterns = {
            'experience': [
                r'(?i)(work\s+)?experience',
                r'(?i)professional\s+experience',
                r'(?i)employment\s+history',
                r'(?i)career\s+history'
            ],
            'skills': [
                r'(?i)skills?',
                r'(?i)technical\s+skills?',
                r'(?i)competencies',
                r'(?i)technologies'
            ],
            'education': [
                r'(?i)education',
                r'(?i)academic\s+background',
                r'(?i)qualifications'
            ],
            'projects': [
                r'(?i)projects?',
                r'(?i)personal\s+projects?',
                r'(?i)portfolio'
            ]
        }
        
        # Common technology normalizations5456yujm 
        self.tech_normalizations = {
            'node.js': 'nodejs',
            'node': 'nodejs',
            'react.js': 'react',
            'vue.js': 'vue',
            'angular.js': 'angular',
            'c++': 'cpp',
            'c#': 'csharp',
            '.net': 'dotnet',
            'postgresql': 'postgres',
            'mongodb': 'mongo'
        }
    
    def parse_cv(self, state: AnalysisState) -> AnalysisState:
        """
        Main parsing function that processes raw CV text.
        
        Args:
            state: Analysis state containing raw CV text
            
        Returns:
            Updated state with structured CV data
        """
        try:
            logger.info("Starting CV parsing...")
            
            if not state.cv_raw.strip():
                state.add_error("Empty CV content provided")
                return state
            
            # Initialize structured CV
            structured_cv = StructuredCV()
            
            # Parse different sections
            structured_cv.personal = self._extract_personal_info(state.cv_raw)
            structured_cv.experience = self._extract_experience(state.cv_raw)
            structured_cv.skills = self._extract_skills(state.cv_raw)
            structured_cv.education = self._extract_education(state.cv_raw)
            structured_cv.projects = self._extract_projects(state.cv_raw)
            
            # Quality checks
            sections_found = self._validate_extraction(structured_cv)
            if sections_found < 3:
                state.add_error(f"Only {sections_found} out of 5 sections detected. CV may be poorly formatted.")
            
            state.cv_structured = structured_cv
            logger.info(f"CV parsing completed. Found {sections_found}/5 sections.")
            
        except Exception as e:
            error_msg = f"CV parsing failed: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
    def _extract_personal_info(self, text: str) -> PersonalInfo:
        """Extract personal information from CV text."""
        personal = PersonalInfo()
        
        # Extract name (usually first non-empty line or after common headers)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Skip common headers and get the first substantial line
            for line in lines[:5]:  # Check first 5 lines
                if not re.match(r'(?i)(curriculum|vitae|resume|cv)\b', line) and len(line) > 2:
                    personal.name = line
                    break
        
        # Extract contact information
        contact = {}
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            contact['phone'] = phone_match.group()
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
        if linkedin_match:
            contact['linkedin'] = linkedin_match.group()
        
        # GitHub
        github_match = re.search(r'github\.com/[\w-]+', text, re.IGNORECASE)
        if github_match:
            contact['github'] = github_match.group()
        
        personal.contact = contact
        return personal
    
    def _extract_experience(self, text: str) -> List[Experience]:
        """Extract work experience from CV text."""
        experiences = []
        
        # Find experience section
        exp_section = self._find_section(text, 'experience')
        if not exp_section:
            return experiences
        
        # Split into individual experiences
        # Look for patterns like company names, job titles, dates
        exp_blocks = self._split_experience_blocks(exp_section)
        
        for block in exp_blocks:
            experience = self._parse_experience_block(block)
            if experience.company or experience.title:  # Valid if has company or title
                experiences.append(experience)
        
        return experiences
    
    def _extract_skills(self, text: str) -> Skills:
        """Extract skills from CV text."""
        skills = Skills()
        
        # Find skills section
        skills_section = self._find_section(text, 'skills')
        
        # Also extract from entire document for comprehensive coverage
        all_text = skills_section + "\n" + text if skills_section else text
        
        # Define skill categories with common technologies
        programming_languages = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql'
        ]
        
        frameworks = [
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
            'express', 'nodejs', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'keras', 'opencv'
        ]
        
        tools = [
            'docker', 'kubernetes', 'git', 'jenkins', 'aws', 'azure', 'gcp',
            'terraform', 'ansible', 'mongodb', 'postgresql', 'redis', 'elasticsearch',
            'kafka', 'spark', 'hadoop', 'tableau', 'powerbi'
        ]
        
        # Extract skills using pattern matching
        skills.languages = self._extract_skill_category(all_text, programming_languages)
        skills.frameworks = self._extract_skill_category(all_text, frameworks)
        skills.tools = self._extract_skill_category(all_text, tools)
        
        return skills
    
    def _extract_education(self, text: str) -> List[Education]:
        """Extract education information from CV text."""
        education_list = []
        
        # Find education section
        edu_section = self._find_section(text, 'education')
        if not edu_section:
            return education_list
        
        # Look for degree patterns
        degree_patterns = [
            r'(?i)(bachelor|master|phd|doctorate|diploma|certificate).*?(\d{4})',
            r'(?i)(b\.?s\.?|m\.?s\.?|ph\.?d\.?).*?(\d{4})',
            r'(?i)(undergraduate|graduate).*?(\d{4})'
        ]
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, edu_section)
            for match in matches:
                education = Education()
                education.degree = match.group(1)
                education.year = match.group(2) if len(match.groups()) > 1 else ""
                
                # Try to find institution near the degree
                context = edu_section[max(0, match.start()-100):match.end()+100]
                institution_match = re.search(r'(?i)(university|college|institute|school)\s+of\s+\w+|\w+\s+(university|college|institute)', context)
                if institution_match:
                    education.institution = institution_match.group()
                
                education_list.append(education)
        
        return education_list
    
    def _extract_projects(self, text: str) -> List[Project]:
        """Extract projects from CV text."""
        projects = []
        
        # Find projects section
        projects_section = self._find_section(text, 'projects')
        if not projects_section:
            return projects
        
        # Split into project blocks
        project_blocks = re.split(r'\n\s*[-•]\s*|\n\s*\d+\.\s*', projects_section)
        
        for block in project_blocks:
            if len(block.strip()) < 10:  # Skip very short blocks
                continue
                
            project = Project()
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            if lines:
                # First line is usually project name
                project.name = lines[0]
                # Rest is description
                project.description = ' '.join(lines[1:]) if len(lines) > 1 else lines[0]
                
                # Extract tech stack from description
                project.tech_stack = self._extract_tech_from_text(project.description)
                
                projects.append(project)
        
        return projects
    
    def _find_section(self, text: str, section_type: str) -> str:
        """Find and extract a specific section from CV text."""
        patterns = self.section_patterns.get(section_type, [])
        
        for pattern in patterns:
            match = re.search(f'{pattern}:?\\s*\\n', text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                
                # Find next section or end of text
                next_section_patterns = []
                for other_type, other_patterns in self.section_patterns.items():
                    if other_type != section_type:
                        next_section_patterns.extend(other_patterns)
                
                end = len(text)
                for next_pattern in next_section_patterns:
                    next_match = re.search(f'{next_pattern}:?\\s*\\n', text[start:], re.IGNORECASE | re.MULTILINE)
                    if next_match:
                        end = min(end, start + next_match.start())
                
                return text[start:end].strip()
        
        return ""
    
    def _split_experience_blocks(self, exp_text: str) -> List[str]:
        """Split experience section into individual job blocks."""
        # Split by common separators
        blocks = re.split(r'\n\s*(?=\w+.*(?:\d{4}|\w+\s+\d{4}))', exp_text)
        return [block.strip() for block in blocks if block.strip()]
    
    def _parse_experience_block(self, block: str) -> Experience:
        """Parse individual experience block."""
        experience = Experience()
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return experience
        
        # First line usually contains company and/or title
        first_line = lines[0]
        
        # Look for date patterns
        date_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|present|current)'
        date_match = re.search(date_pattern, first_line, re.IGNORECASE)
        if date_match:
            experience.dates = date_match.group()
            # Remove dates from first line to get company/title
            first_line = re.sub(date_pattern, '', first_line, flags=re.IGNORECASE).strip()
        
        # Try to separate company and title
        if ',' in first_line:
            parts = first_line.split(',', 1)
            experience.company = parts[0].strip()
            experience.title = parts[1].strip()
        elif ' at ' in first_line.lower():
            parts = first_line.lower().split(' at ', 1)
            experience.title = parts[0].strip()
            experience.company = parts[1].strip()
        else:
            # Assume it's company name
            experience.company = first_line
        
        # Remaining lines are bullets
        bullets = []
        for line in lines[1:]:
            if line.startswith(('•', '-', '*')) or re.match(r'^\d+\.', line):
                bullets.append(re.sub(r'^[•\-*]\s*|\d+\.\s*', '', line))
            elif line and not re.search(date_pattern, line, re.IGNORECASE):
                bullets.append(line)
        
        experience.bullets = bullets
        return experience
    
    def _extract_skill_category(self, text: str, skill_list: List[str]) -> List[str]:
        """Extract skills from a specific category."""
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_list:
            # Normalize skill name
            normalized_skill = self.tech_normalizations.get(skill.lower(), skill.lower())
            
            # Check for skill mentions (word boundaries to avoid partial matches)
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(normalized_skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def _extract_tech_from_text(self, text: str) -> List[str]:
        """Extract technology stack from project description."""
        all_techs = []
        
        # Combine all known technologies
        all_known_techs = []
        for category in [
            ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust'],
            ['react', 'angular', 'vue', 'django', 'flask', 'tensorflow', 'pytorch'],
            ['docker', 'kubernetes', 'aws', 'mongodb', 'postgresql', 'git']
        ]:
            all_known_techs.extend(category)
        
        return self._extract_skill_category(text, all_known_techs)
    
    def _validate_extraction(self, cv: StructuredCV) -> int:
        """Validate the extraction quality and return number of sections found."""
        sections_found = 0
        
        if cv.personal.name:
            sections_found += 1
        
        if cv.experience and any(exp.company or exp.title for exp in cv.experience):
            sections_found += 1
        
        if cv.skills.languages or cv.skills.frameworks or cv.skills.tools:
            sections_found += 1
        
        if cv.education:
            sections_found += 1
        
        if cv.projects:
            sections_found += 1
        
        return sections_found


def cv_parser_node(state: AnalysisState) -> AnalysisState:
    """
    LangGraph node function for CV parsing.
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with parsed CV data
    """
    parser = CVParserAgent()
    return parser.parse_cv(state)
