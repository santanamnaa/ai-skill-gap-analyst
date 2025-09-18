import re
import os
import json
from pathlib import Path
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
    CV Parser Agent that extracts structured data from raw CV text using dual-mode parsing.
    
    Supports both spaCy NER mode for intelligent extraction and regex fallback mode
    for robust pattern-based parsing. Configuration is loaded from JSON files for
    easy maintenance and customization.
    
    Attributes:
        use_spacy (bool): Whether to use spaCy NER mode (from USE_SPACY_PARSER env var)
        config (dict): Loaded configuration including patterns and skill categories
        _spacy_nlp: Lazy-loaded spaCy model (only when USE_SPACY_PARSER=True)
    """
    
    def __init__(self):
        # Environment configuration
        self.use_spacy = os.getenv('USE_SPACY_PARSER', 'false').lower() == 'true'
        self._spacy_nlp = None  # Lazy-loaded spaCy model
        
        # Load configuration from JSON file
        self.config = self._load_config()
        
        # Extract frequently used patterns for performance
        self.section_patterns = self.config['section_patterns']
        self.tech_normalizations = self.config['tech_normalizations']
        self.skill_categories = self.config['skill_categories']
        self.degree_patterns = self.config['degree_patterns']
    
    def _load_config(self) -> Dict:
        """
        Load CV parser configuration from JSON file.
        
        Returns:
            dict: Configuration containing section patterns, skill categories,
                 technology normalizations, and degree patterns
                 
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_path = Path(__file__).parent.parent.parent / 'data' / 'cv_parser_config.json'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded CV parser configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            # Fallback to minimal default configuration
            return {
                'section_patterns': {'experience': [], 'skills': [], 'education': [], 'projects': []},
                'skill_categories': {'programming_languages': [], 'frameworks': [], 'tools': []},
                'tech_normalizations': {},
                'degree_patterns': []
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def run(self, state: AnalysisState) -> AnalysisState:
        """
        Main parsing function that processes raw CV text using dual-mode parsing.
        
        Selects between spaCy NER mode and regex mode based on the USE_SPACY_PARSER
        environment variable. Performs quality validation and error handling.
        
        Args:
            state (AnalysisState): Analysis state containing:
                - cv_raw (str): Raw CV text content to parse
                
        Returns:
            AnalysisState: Updated state containing:
                - structured_cv (StructuredCV): Parsed and structured CV data
                - processing_errors (List[str]): Any errors encountered during parsing
                
        Note:
            Only initializes spaCy model if USE_SPACY_PARSER=True to keep
            initial setup lightweight. Validates extraction quality and logs
            warnings for poorly formatted CVs.
        """
        try:
            logger.info(f"Starting CV parsing in {'spaCy' if self.use_spacy else 'regex'} mode...")
            
            if not state.cv_raw.strip():
                state.add_error("Empty CV content provided")
                return state
            
            # Parse using selected mode (spaCy model only loaded if needed)
            if self.use_spacy:
                structured_cv = self.parse_with_spacy(state.cv_raw)
            else:
                structured_cv = self.parse_with_regex(state.cv_raw)
            
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
    
    def parse_with_spacy(self, text: str) -> StructuredCV:
        """
        Parse CV text using spaCy Named Entity Recognition for intelligent extraction.
        
        This method leverages spaCy's NER capabilities to identify entities like PERSON,
        ORG, and DATE, then combines them with regex patterns for comprehensive parsing.
        Automatically falls back to regex parsing if spaCy fails.
        
        Args:
            text (str): Raw CV text content to parse
            
        Returns:
            StructuredCV: Structured CV object containing:
                - personal (PersonalInfo): Name and contact information
                - experience (List[Experience]): Work history with companies, titles, dates, bullets
                - skills (Skills): Categorized technical skills (languages, frameworks, tools)
                - education (List[Education]): Academic background with degrees, institutions, years
                - projects (List[Project]): Personal/professional projects with descriptions
                
        Raises:
            Exception: Any spaCy-related errors trigger automatic fallback to regex parsing
            
        Example:
            >>> parser = CVParserAgent()
            >>> os.environ['USE_SPACY_PARSER'] = 'true'
            >>> cv = parser.parse_with_spacy("John Doe\nSoftware Engineer at Google\n...")
            >>> print(cv.personal.name)  # "John Doe"
            >>> print(cv.experience[0].company)  # "Google"
        """
        try:
            # Lazy import and load spaCy model only when needed
            if self._spacy_nlp is None:
                self._initialize_spacy_model()
            
            # Process text with spaCy
            doc = self._spacy_nlp(text)
            
            # Initialize structured CV
            structured_cv = StructuredCV()
            
            # Extract entities using spaCy NER with fallback enhancement
            structured_cv.personal = self._extract_personal_info_spacy(doc, text)
            structured_cv.experience = self._extract_experience_spacy(doc, text)
            structured_cv.skills = self._extract_skills_spacy(doc, text)
            structured_cv.education = self._extract_education_spacy(doc, text)
            structured_cv.projects = self._extract_projects_spacy(doc, text)
            
            logger.info("spaCy parsing completed successfully")
            return structured_cv
            
        except Exception as e:
            logger.warning(f"spaCy parsing failed: {e}. Falling back to regex parsing.")
            return self.parse_with_regex(text)
    
    def _initialize_spacy_model(self):
        """
        Initialize spaCy model with proper error handling.
        
        Only called when USE_SPACY_PARSER=True to avoid unnecessary imports
        and model loading during normal operation.
        
        Raises:
            ImportError: If spaCy is not installed
            OSError: If en_core_web_sm model is not available
        """
        try:
            import spacy
            self._spacy_nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except (ImportError, OSError) as e:
            logger.warning(f"Failed to load spaCy model: {e}. Falling back to regex parsing.")
            raise
    
    def parse_with_regex(self, text: str) -> StructuredCV:
        """
        Parse CV text using regex patterns with robust fallback handling.
        
        This method uses pattern-based extraction to identify CV sections and extract
        structured information. It's the default parsing mode and serves as a reliable
        fallback when spaCy is unavailable.
        
        Args:
            text (str): Raw CV text content to parse
            
        Returns:
            StructuredCV: Structured CV object containing:
                - personal (PersonalInfo): Extracted name, email, phone, LinkedIn, GitHub
                - experience (List[Experience]): Work history with parsed companies, titles,
                  date ranges, and bullet points
                - skills (Skills): Technical skills categorized into:
                  * languages: Programming languages (Python, Java, etc.)
                  * frameworks: Frameworks and libraries (React, Django, etc.)
                  * tools: Development tools and platforms (Docker, AWS, etc.)
                - education (List[Education]): Academic qualifications with degrees,
                  institutions, and graduation years
                - projects (List[Project]): Personal/professional projects with names,
                  descriptions, and extracted technology stacks
                  
        Note:
            Uses configuration from cv_parser_config.json for patterns and skill categories.
            Handles various CV formats including bullet points, tables, and free text.
            
        Example:
            >>> parser = CVParserAgent()
            >>> cv = parser.parse_with_regex("John Doe\nEmail: john@example.com\n...")
            >>> print(cv.personal.contact['email'])  # "john@example.com"
            >>> print(len(cv.skills.languages))  # Number of programming languages found
        """
        logger.info("Using regex parsing mode")
        
        # Initialize structured CV
        structured_cv = StructuredCV()
        
        # Parse different sections using regex patterns from configuration
        structured_cv.personal = self._extract_personal_info(text)
        structured_cv.experience = self._extract_experience(text)
        structured_cv.skills = self._extract_skills(text)
        structured_cv.education = self._extract_education(text)
        structured_cv.projects = self._extract_projects(text)
        
        return structured_cv
    
    def _extract_personal_info(self, text: str) -> PersonalInfo:
        """
        Extract personal information from CV text using pattern matching.
        
        Identifies the candidate's name and contact information including
        email, phone, LinkedIn, and GitHub profiles.
        
        Args:
            text (str): Raw CV text to analyze
            
        Returns:
            PersonalInfo: Object containing:
                - name (str): Candidate's full name (from first substantial line)
                - contact (Dict[str, str]): Contact information with keys:
                  * email: Email address
                  * phone: Phone number
                  * linkedin: LinkedIn profile URL
                  * github: GitHub profile URL
                  
        Note:
            Name extraction skips common CV headers like "Curriculum Vitae" or "Resume".
            Contact patterns use regex for reliable extraction of structured data.
        """
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
        """
        Extract work experience from CV text using section detection and parsing.
        
        Identifies the experience section and parses individual job entries
        including company names, job titles, date ranges, and bullet points.
        
        Args:
            text (str): Raw CV text to analyze
            
        Returns:
            List[Experience]: List of work experience entries, each containing:
                - company (str): Company/organization name
                - title (str): Job title/position
                - dates (str): Employment date range (e.g., "2020-2023")
                - bullets (List[str]): List of responsibilities/achievements
                
        Note:
            Uses section_patterns from configuration to locate experience section.
            Handles various formats including "Title at Company" and "Company, Title".
        """
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
        """
        Extract and categorize technical skills from CV text.
        
        Searches both the dedicated skills section and the entire document
        to ensure comprehensive skill detection. Uses configuration-based
        skill categories for easy maintenance.
        
        Args:
            text (str): CV text to analyze
            
        Returns:
            Skills: Object containing categorized skills:
                - languages (List[str]): Programming languages (normalized)
                - frameworks (List[str]): Frameworks and libraries (normalized)
                - tools (List[str]): Development tools and platforms (normalized)
                
        Note:
            Skill normalization is applied (e.g., "Node.js" -> "nodejs")
            based on tech_normalizations in configuration.
        """
        skills = Skills()
        
        # Find skills section
        skills_section = self._find_section(text, 'skills')
        
        # Also extract from entire document for comprehensive coverage
        all_text = skills_section + "\n" + text if skills_section else text
        
        # Extract skills using configuration-based categories
        skills.languages = self._extract_skill_category(
            all_text, self.skill_categories['programming_languages']
        )
        skills.frameworks = self._extract_skill_category(
            all_text, self.skill_categories['frameworks']
        )
        skills.tools = self._extract_skill_category(
            all_text, self.skill_categories['tools']
        )
        
        return skills
    
    def _extract_education(self, text: str) -> List[Education]:
        """
        Extract education information from CV text using improved pattern matching.
        
        Identifies academic qualifications including degrees, institutions,
        and graduation years from the education section.
        
        Args:
            text (str): CV text to analyze
            
        Returns:
            List[Education]: List of education entries, each containing:
                - degree (str): Degree type (Bachelor, Master, PhD, etc.)
                - institution (str): Educational institution name
                - year (str): Graduation year
                - field (str): Field of study (if detected)
                
        Note:
            Uses degree_patterns from configuration for flexible pattern matching.
            Improved institution detection for better accuracy.
        """
        education_list = []
        
        # Find education section
        edu_section = self._find_section(text, 'education')
        if not edu_section:
            return education_list
        
        # Split education section into lines for better processing
        edu_lines = [line.strip() for line in edu_section.split('\n') if line.strip()]
        
        # Use degree patterns from configuration
        for pattern in self.degree_patterns:
            matches = re.finditer(pattern, edu_section)
            for match in matches:
                education = Education()
                education.degree = match.group(1)
                education.year = match.group(2) if len(match.groups()) > 1 else ""
                
                # Find the line containing this match
                match_line = ""
                for line in edu_lines:
                    if match.group(0) in line:
                        match_line = line
                        break
                
                # Extract institution from the same line or nearby lines
                institution = self._extract_institution_from_line(match_line, edu_lines)
                if institution:
                    education.institution = institution
                
                # Try to extract field of study
                field = self._extract_field_of_study(match_line)
                if field:
                    education.field = field
                
                education_list.append(education)
        
        return education_list
    
    def _extract_institution_from_line(self, match_line: str, all_lines: List[str]) -> str:
        """
        Extract institution name from education line with improved patterns.
        
        Args:
            match_line: Line containing the degree match
            all_lines: All lines from education section
            
        Returns:
            Institution name if found
        """
        # Remove degree and year information to isolate institution
        clean_line = match_line
        
        # Remove common degree patterns
        degree_remove_patterns = [
            r'\b(?:bachelor|master|phd|doctorate|diploma|certificate)\b.*?(?:\d{4}|\b)',
            r'\b(?:b\.?s\.?|m\.?s\.?|ph\.?d\.?)\b.*?(?:\d{4}|\b)',
            r'\b(?:undergraduate|graduate)\b.*?(?:\d{4}|\b)',
            r'\(\d{4}\)',
            r'\d{4}'
        ]
        
        for pattern in degree_remove_patterns:
            clean_line = re.sub(pattern, '', clean_line, flags=re.IGNORECASE)
        
        # Clean up extra punctuation and whitespace
        clean_line = re.sub(r'[,\-–]\s*$', '', clean_line).strip()
        clean_line = re.sub(r'^\s*[,\-–]\s*', '', clean_line).strip()
        
        # Look for institution patterns
        institution_patterns = [
            # Full institution names
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:University|College|Institute|School))\b',
            # Abbreviated forms
            r'\b(MIT|Stanford|Harvard|Berkeley|CMU|Caltech|UCLA|USC|NYU)\b',
            # University of X pattern
            r'\b(University\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            # X University pattern
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+University)\b',
            # X College pattern
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+College)\b',
            # X Institute pattern
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Institute)\b'
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, clean_line)
            if match:
                return match.group(1).strip()
        
        # If no specific pattern found, return the cleaned line if it looks like an institution
        if clean_line and len(clean_line) > 3 and not re.match(r'^\d+', clean_line):
            # Check if it contains institution keywords
            if any(keyword in clean_line.lower() for keyword in ['university', 'college', 'institute', 'school']):
                return clean_line
        
        return ""
    
    def _extract_field_of_study(self, line: str) -> str:
        """
        Extract field of study from education line.
        
        Args:
            line: Education line to analyze
            
        Returns:
            Field of study if found
        """
        # Common field patterns
        field_patterns = [
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:major|concentration|specialization):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, line)
            if match:
                field = match.group(1).strip()
                # Filter out common non-field words
                if field.lower() not in ['science', 'arts', 'engineering', 'technology']:
                    return field
        
        return ""
    
    def _extract_projects(self, text: str) -> List[Project]:
        """
        Extract personal and professional projects from CV text.
        
        Identifies the projects section and parses individual project entries
        including names, descriptions, and technology stacks.
        
        Args:
            text (str): Raw CV text to analyze
            
        Returns:
            List[Project]: List of project entries, each containing:
                - name (str): Project name/title
                - description (str): Project description and details
                - tech_stack (List[str]): Technologies used (extracted from description)
                
        Note:
            Automatically extracts technology stack from project descriptions
            using the same skill detection logic as the main skills extraction.
        """
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
        """
        Parse individual experience block with improved title/company detection.
        
        Handles various formats:
        - "Title, Company (dates)"
        - "Title at Company (dates)" 
        - "Company - Title (dates)"
        - "Title | Company (dates)"
        """
        experience = Experience()
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return experience
        
        # First line usually contains company and/or title
        first_line = lines[0]
        
        # Look for date patterns and extract them
        date_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|present|current)'
        date_match = re.search(date_pattern, first_line, re.IGNORECASE)
        if date_match:
            experience.dates = date_match.group()
            # Remove dates from first line to get company/title
            first_line = re.sub(date_pattern, '', first_line, flags=re.IGNORECASE).strip()
            # Clean up extra parentheses or brackets
            first_line = re.sub(r'[()[\]]\s*$', '', first_line).strip()
        
        # Try to separate company and title using various patterns
        if ', ' in first_line and ' at ' not in first_line.lower():
            # Format: "Title, Company" 
            parts = first_line.split(', ', 1)
            experience.title = parts[0].strip()
            experience.company = parts[1].strip()
        elif ' at ' in first_line.lower():
            # Format: "Title at Company"
            parts = first_line.lower().split(' at ', 1)
            experience.title = parts[0].strip()
            experience.company = parts[1].strip()
        elif ' - ' in first_line:
            # Format: "Company - Title" or "Title - Company"
            parts = first_line.split(' - ', 1)
            # Heuristic: if first part has common company indicators, it's company
            if any(indicator in parts[0].lower() for indicator in ['inc', 'corp', 'llc', 'ltd', 'company', 'technologies']):
                experience.company = parts[0].strip()
                experience.title = parts[1].strip()
            else:
                experience.title = parts[0].strip()
                experience.company = parts[1].strip()
        elif ' | ' in first_line:
            # Format: "Title | Company"
            parts = first_line.split(' | ', 1)
            experience.title = parts[0].strip()
            experience.company = parts[1].strip()
        else:
            # Single item - try to determine if it's title or company
            # If it contains common job titles, assume it's a title
            job_title_indicators = ['engineer', 'developer', 'manager', 'analyst', 'scientist', 'architect', 'lead', 'senior', 'junior']
            if any(indicator in first_line.lower() for indicator in job_title_indicators):
                experience.title = first_line
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
        """
        Extract technology stack from project description text.
        
        Uses the same skill detection logic as the main skills extraction
        to identify technologies mentioned in project descriptions.
        
        Args:
            text (str): Project description text to analyze
            
        Returns:
            List[str]: List of normalized technology names found in the text
            
        Note:
            Combines all skill categories (languages, frameworks, tools) for
            comprehensive technology detection in project contexts.
        """
        all_techs = []
        
        # Combine all known technologies
        # Combine all skill categories from configuration
        all_known_techs = []
        for category in self.skill_categories.values():
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
    
    def _extract_personal_info_spacy(self, doc, text: str) -> PersonalInfo:
        """
        Extract personal information using spaCy NER.
        
        Args:
            doc: spaCy processed document
            text: Original text for fallback extraction
            
        Returns:
            PersonalInfo object with extracted data
        """
        personal = PersonalInfo()
        
        # Extract person names using NER
        person_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        if person_names:
            # Take the first person name found (usually the CV owner)
            personal.name = person_names[0]
        else:
            # Fallback to regex extraction
            personal.name = self._extract_personal_info(text).name
        
        # Extract contact information (use regex as it's more reliable for structured data)
        contact = {}
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone
        phone_match = re.search(r'(\+?\d{1,3}[-.]\s?)?\(?\d{3}\)?[-.]\s?\d{3}[-.]\s?\d{4}', text)
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
    
    def _extract_experience_spacy(self, doc, text: str) -> List[Experience]:
        """
        Extract work experience using spaCy NER and organizational entities.
        
        Args:
            doc: spaCy processed document
            text: Original text for section detection
            
        Returns:
            List of Experience objects
        """
        experiences = []
        
        # Find experience section first
        exp_section = self._find_section(text, 'experience')
        if not exp_section:
            return experiences
        
        # Process experience section with spaCy
        exp_doc = self._spacy_nlp(exp_section)
        
        # Extract organizations (potential employers)
        organizations = [ent.text for ent in exp_doc.ents if ent.label_ == "ORG"]
        
        # Extract dates
        dates = [ent.text for ent in exp_doc.ents if ent.label_ == "DATE"]
        
        # Combine with regex parsing for structured extraction
        exp_blocks = self._split_experience_blocks(exp_section)
        
        for i, block in enumerate(exp_blocks):
            experience = self._parse_experience_block(block)
            
            # Enhance with spaCy entities if available
            if i < len(organizations) and not experience.company:
                experience.company = organizations[i]
            
            if experience.company or experience.title:
                experiences.append(experience)
        
        return experiences
    
    def _extract_skills_spacy(self, doc, text: str) -> Skills:
        """
        Extract skills using spaCy NER with custom skill matching.
        
        Args:
            doc: spaCy processed document
            text: Original text for comprehensive skill extraction
            
        Returns:
            Skills object with categorized skills
        """
        skills = Skills()
        
        # Use regex-based extraction as baseline
        regex_skills = self._extract_skills(text)
        
        # Process text with spaCy for additional insights
        skill_keywords = []
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "WORK_OF_ART"] and len(ent.text) > 2:
                skill_keywords.append(ent.text.lower())
        
        # Merge with regex results
        skills.languages = list(set(regex_skills.languages + 
                                  [s for s in skill_keywords if s in ['python', 'java', 'javascript', 'typescript']]))
        skills.frameworks = list(set(regex_skills.frameworks + 
                                   [s for s in skill_keywords if s in ['react', 'angular', 'django', 'flask']]))
        skills.tools = list(set(regex_skills.tools + 
                              [s for s in skill_keywords if s in ['docker', 'kubernetes', 'aws', 'git']]))
        
        return skills
    
    def _extract_education_spacy(self, doc, text: str) -> List[Education]:
        """
        Extract education using spaCy NER for institutions and dates.
        
        Args:
            doc: spaCy processed document
            text: Original text for section detection
            
        Returns:
            List of Education objects
        """
        education_list = []
        
        # Find education section
        edu_section = self._find_section(text, 'education')
        if not edu_section:
            return education_list
        
        # Process education section with spaCy
        edu_doc = self._spacy_nlp(edu_section)
        
        # Extract organizations (universities/schools)
        institutions = [ent.text for ent in edu_doc.ents if ent.label_ == "ORG"]
        
        # Extract dates
        dates = [ent.text for ent in edu_doc.ents if ent.label_ == "DATE"]
        
        # Combine with regex parsing for degree detection
        regex_education = self._extract_education(text)
        
        # Enhance regex results with spaCy entities
        for i, edu in enumerate(regex_education):
            if i < len(institutions) and not edu.institution:
                edu.institution = institutions[i]
            education_list.append(edu)
        
        return education_list
    
    def _extract_projects_spacy(self, doc, text: str) -> List[Project]:
        """
        Extract projects using spaCy NER for enhanced project detection.
        
        Args:
            doc: spaCy processed document
            text: Original text for section detection
            
        Returns:
            List of Project objects
        """
        projects = []
        
        # Find projects section
        projects_section = self._find_section(text, 'projects')
        if not projects_section:
            return projects
        
        # Use regex-based extraction as baseline
        regex_projects = self._extract_projects(text)
        
        # Process projects section with spaCy for additional insights
        proj_doc = self._spacy_nlp(projects_section)
        
        # Extract potential project names (WORK_OF_ART, PRODUCT entities)
        project_entities = [ent.text for ent in proj_doc.ents 
                          if ent.label_ in ["WORK_OF_ART", "PRODUCT", "EVENT"]]
        
        # Enhance regex results
        for project in regex_projects:
            # Extract tech stack using both regex and spaCy
            tech_stack = self._extract_tech_from_text(project.description)
            project.tech_stack = tech_stack
            projects.append(project)
        
        return projects


def cv_parser_node(state: AnalysisState) -> AnalysisState:
    """
    LangGraph node function for CV parsing.
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with parsed CV data
    """
    parser = CVParserAgent()
    return parser.run(state)
