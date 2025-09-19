"""
## Updated by AI Agent on September 18, 2025
Market Intelligence Agent with static data core and optional RAG/API fallback.
"""

import os
import logging
import json
import requests
from typing import Dict, List, Optional
from pathlib import Path
import time

from ..schemas import (
    AnalysisState, MarketIntelligence, RoleRequirements, 
    TechStackPopularity, MarketInsights
)

logger = logging.getLogger(__name__)


class MarketIntelligenceAgent:
    """
    Market Intelligence Agent with static data core and optional RAG/API fallback.
    
    Supports both static data analysis (default) and RAG-powered market intelligence
    with intelligent fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize Market Intelligence Agent with static data foundation."""
        self.data_path = Path(__file__).parent.parent.parent / "data" / "market_data.json"
        self.market_data = self._load_market_data()
        
        # Environment configuration
        self.use_rag = os.getenv('USE_RAG', 'true').lower() == 'true'
        
        # Role mapping for flexible matching
        self.role_mappings = {
            'ai engineer': 'senior_ai_engineer',
            'machine learning engineer': 'senior_ai_engineer',
            'ml engineer': 'senior_ai_engineer',
            'data scientist': 'data_scientist',
            'backend developer': 'backend_engineer',
            'backend engineer': 'backend_engineer',
            'devops engineer': 'devops_engineer',
            'site reliability engineer': 'devops_engineer',
            'sre': 'devops_engineer',
            'frontend developer': 'frontend_engineer',
            'frontend engineer': 'frontend_engineer',
            'fullstack developer': 'fullstack_engineer',
            'fullstack engineer': 'fullstack_engineer',
            'full stack developer': 'fullstack_engineer',
            'mobile developer': 'mobile_engineer',
            'mobile engineer': 'mobile_engineer',
            'security engineer': 'security_engineer',
            'cybersecurity engineer': 'security_engineer'
        }
    
    def run(self, state: AnalysisState) -> AnalysisState:
        """
        Main entry point for market intelligence gathering with environment-based mode selection.
        
        Args:
            state: Analysis state with target role
            
        Returns:
            Updated state with market intelligence data
        """
        try:
            logger.info(f"Starting market intelligence gathering for role: {state.target_role}")
            
            if not state.target_role.strip():
                state.add_error("No target role specified for market intelligence")
                return state
            
            # Check environment flag for analysis mode
            if self.use_rag:
                logger.info("Using RAG-powered market intelligence mode")
                state = self.gather_with_rag(state)
            else:
                logger.info("Using static data market intelligence mode")
                state = self.gather_with_static_data(state)
            
            logger.info("Market intelligence gathering completed successfully")
            
        except Exception as e:
            error_msg = f"Market intelligence gathering failed: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
    def gather_with_static_data(self, state: AnalysisState) -> AnalysisState:
        """
        Gather market intelligence using static data from local JSON/dict sources.
        
        Args:
            state: Analysis state with target role
            
        Returns:
            Updated state with market intelligence data
        """
        # Use static market data (default)
        market_intel = self._get_role_market_data(state.target_role)
        
        if not market_intel:
            # Fallback to generic data
            market_intel = self._get_fallback_market_data(state.target_role)
            logger.warning(f"Using fallback data for role: {state.target_role}")
        
        state.market_intelligence = market_intel
        return state
    
    def gather_with_rag(self, state: AnalysisState) -> AnalysisState:
        """
        RAG-powered market intelligence gathering using JSearch API (RapidAPI).
        
        Args:
            state: Analysis state with target role
            
        Returns:
            Updated state with market intelligence data
        """
        try:
            logger.info(f"RAG mode: Querying JSearch API for role: {state.target_role}")
            
            # Get API credentials from environment
            rapidapi_key = os.getenv('RAPIDAPI_KEY')
            if not rapidapi_key:
                logger.warning("RAPIDAPI_KEY not found. Falling back to static data.")
                return self.gather_with_static_data(state)
            
            # Try multiple search strategies for better results
            job_data = self._fetch_job_data_with_fallback(state.target_role, rapidapi_key)
            
            if not job_data or len(job_data.get('data', [])) == 0:
                logger.warning(f"No job data found for role: {state.target_role}")
                return self.gather_with_static_data(state)
            
            # Parse job postings to extract market intelligence
            market_intel = self._parse_job_data_to_market_intelligence(job_data, state.target_role)
            
            state.market_intelligence = market_intel
            logger.info(f"RAG analysis completed for {len(job_data.get('data', []))} job postings")
            
            return state
            
        except Exception as e:
            logger.warning(f"RAG market intelligence failed: {str(e)}. Falling back to static data.")
            # Fallback to static data analysis
            return self.gather_with_static_data(state)

    def _fetch_job_data_with_fallback(self, role: str, api_key: str) -> Dict:
        """
        Fetch job data with multiple search strategies and fallback queries.
        
        Args:
            role: Target job role
            api_key: RapidAPI key
            
        Returns:
            Job data from API with best available results
        """
        # Define search strategies based on role
        search_queries = self._generate_search_queries(role)
        
        best_result = None
        max_jobs = 0
        
        for query in search_queries:
            try:
                logger.info(f"Trying search query: '{query}'")
                result = self._fetch_jsearch_data_single(query, api_key)
                
                if result and len(result.get('data', [])) > max_jobs:
                    max_jobs = len(result.get('data', []))
                    best_result = result
                    logger.info(f"Found {max_jobs} jobs with query: '{query}'")
                    
                    # If we found enough jobs, use this result
                    if max_jobs >= 10:
                        break
                        
            except Exception as e:
                logger.warning(f"Search query '{query}' failed: {str(e)}")
                continue
        
        return best_result or {'data': []}

    def _generate_search_queries(self, role: str) -> List[str]:
        """
        Generate multiple search queries for better job matching.
        
        Args:
            role: Target role
            
        Returns:
            List of search queries to try
        """
        role_lower = role.lower().strip()
        queries = []
        
        # Role mapping for non-English terms
        role_translations = {
            'kedokteran': ['doctor', 'physician', 'medical doctor', 'healthcare professional'],
            'dokter': ['doctor', 'physician', 'medical practitioner'],
            'perawat': ['nurse', 'registered nurse', 'healthcare nurse'],
            'apoteker': ['pharmacist', 'pharmacy', 'pharmaceutical'],
            'bidan': ['midwife', 'obstetric nurse', 'maternal health'],
            'psikolog': ['psychologist', 'mental health', 'clinical psychology'],
            'fisioterapi': ['physiotherapist', 'physical therapy', 'rehabilitation'],
            'radiologi': ['radiologist', 'medical imaging', 'radiology technician'],
            'laboratorium': ['medical laboratory', 'lab technician', 'clinical laboratory'],
            'gizi': ['nutritionist', 'dietitian', 'clinical nutrition']
        }
        
        # Tech role variations
        tech_variations = {
            'ai engineer': ['artificial intelligence engineer', 'machine learning engineer', 'ai developer'],
            'data scientist': ['data analyst', 'data engineer', 'business intelligence'],
            'backend engineer': ['backend developer', 'server developer', 'api developer'],
            'frontend engineer': ['frontend developer', 'ui developer', 'web developer'],
            'devops engineer': ['devops', 'site reliability engineer', 'infrastructure engineer'],
            'mobile engineer': ['mobile developer', 'ios developer', 'android developer']
        }
        
        # 1. Original role
        queries.append(f"{role} jobs")
        
        # 2. Try translations if available
        if role_lower in role_translations:
            for translation in role_translations[role_lower]:
                queries.append(f"{translation} jobs")
        
        # 3. Try tech variations if available  
        if role_lower in tech_variations:
            for variation in tech_variations[role_lower]:
                queries.append(f"{variation} jobs")
        
        # 4. Generic fallbacks based on keywords
        if any(keyword in role_lower for keyword in ['engineer', 'developer', 'programmer']):
            queries.extend(['software engineer jobs', 'developer jobs'])
        elif any(keyword in role_lower for keyword in ['doctor', 'medical', 'health']):
            queries.extend(['healthcare jobs', 'medical professional jobs'])
        elif any(keyword in role_lower for keyword in ['data', 'analyst', 'science']):
            queries.extend(['data analyst jobs', 'business analyst jobs'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:5]  # Limit to 5 queries to avoid rate limits

    def _fetch_jsearch_data_single(self, query: str, api_key: str) -> Dict:
        """
        Fetch job data from JSearch API for a single query.
        
        Args:
            query: Search query
            api_key: RapidAPI key
            
        Returns:
            Job data from API
        """
        url = "https://jsearch.p.rapidapi.com/search"
        
        querystring = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "month"
        }
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        # Log API usage info
        remaining_requests = response.headers.get('X-RateLimit-Remaining', 'Unknown')
        logger.info(f"API requests remaining: {remaining_requests}")
        
        response.raise_for_status()
        return response.json()

    def _parse_job_data_to_market_intelligence(self, job_data: Dict, target_role: str) -> MarketIntelligence:
        """
        Parse job postings data to extract market intelligence.
        
        Args:
            job_data: Raw job data from API
            target_role: Target role for context
            
        Returns:
            MarketIntelligence object with extracted data
        """
        jobs = job_data.get('data', [])
        
        # Extract skills from job descriptions
        all_skills = set()
        core_skills = set()
        preferred_skills = set()
        emerging_trends = set()
        
        # Salary data collection
        salaries = []
        
        # Technology stack tracking
        languages = set()
        frameworks = set()
        tools = set()
        
        # Skill keywords for different categories
        skill_keywords = {
            'languages': ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'laravel', 'rails'],
            'tools': ['docker', 'kubernetes', 'git', 'jenkins', 'aws', 'azure', 'gcp', 'terraform', 'ansible'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch'],
            'emerging': ['ai', 'machine learning', 'blockchain', 'microservices', 'devops', 'cloud native']
        }
        
        for job in jobs[:20]:  # Analyze top 20 jobs
            description = job.get('job_description', '').lower()
            title = job.get('job_title', '').lower()
            
            # Extract salary if available
            salary_min = job.get('job_min_salary')
            salary_max = job.get('job_max_salary')
            if salary_min and salary_max:
                salaries.append((salary_min, salary_max))
            
            # Extract skills from description and title
            combined_text = f"{title} {description}"
            
            # Categorize skills
            for category, keywords in skill_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        if category == 'languages':
                            languages.add(keyword.title())
                        elif category == 'frameworks':
                            frameworks.add(keyword.title())
                        elif category == 'tools':
                            tools.add(keyword.title())
                        elif category == 'emerging':
                            emerging_trends.add(keyword.title())
                        
                        # Determine if core or preferred based on frequency
                        if combined_text.count(keyword) >= 2 or keyword in title:
                            core_skills.add(keyword.title())
                        else:
                            preferred_skills.add(keyword.title())
        
        # Calculate salary range
        if salaries:
            min_salaries = [s[0] for s in salaries]
            max_salaries = [s[1] for s in salaries]
            avg_min = sum(min_salaries) // len(min_salaries)
            avg_max = sum(max_salaries) // len(max_salaries)
            salary_range = f"${avg_min:,} - ${avg_max:,}"
        else:
            salary_range = "Salary data not available"
        
        # Determine demand level based on number of jobs found
        job_count = len(jobs)
        if job_count >= 50:
            demand_level = "Very High"
        elif job_count >= 20:
            demand_level = "High"
        elif job_count >= 10:
            demand_level = "Medium"
        else:
            demand_level = "Low"
        
        # Create market intelligence object
        role_requirements = RoleRequirements(
            core_skills=list(core_skills)[:10],  # Top 10 core skills
            preferred_skills=list(preferred_skills)[:10],  # Top 10 preferred skills
            emerging_trends=list(emerging_trends)[:5]  # Top 5 trends
        )
        
        tech_stack = TechStackPopularity(
            language=list(languages)[:5],
            framework=list(frameworks)[:5],
            tools=list(tools)[:5]
        )
        
        market_insights = MarketInsights(
            salary_range=salary_range,
            demand_level=demand_level,
            growth_areas=list(emerging_trends)[:3]
        )
        
        return MarketIntelligence(
            role_requirements=role_requirements,
            tech_stack_popularity=tech_stack,
            market_insights=market_insights,
            source="jsearch_api"
        )
    
    def gather_market_intelligence(self, state: AnalysisState) -> AnalysisState:
        """
        Legacy method for backward compatibility.
        Delegates to the new run() method.
        
        Args:
            state: Analysis state with target role
            
        Returns:
            Updated state with market intelligence data
        """
        return self.run(state)
    
    def fetch_linkedin_data(self, target_role: str) -> MarketIntelligence:
        """
        Fetch market intelligence data from LinkedIn Jobs API.
        
        Args:
            target_role: Target job role to search for
            
        Returns:
            MarketIntelligence object with LinkedIn data
            
        Environment Variables Required:
            LINKEDIN_API_KEY: Your LinkedIn API application key
            LINKEDIN_API_SECRET: Your LinkedIn API application secret
            
        Upgrade Instructions:
            1. Register LinkedIn Developer Application
            2. Set environment variables
            3. Initialize agent with use_linkedin=True
        """
        try:
            logger.info(f"Fetching LinkedIn data for role: {target_role}")
            
            # Step 1: Authenticate with LinkedIn API (OAuth2)
            if not self.linkedin_token:
                self.linkedin_token = self._authenticate_linkedin()
            
            # Step 2: Build query parameters for job search
            query_params = {
                'keywords': target_role,
                'location': '',  # Global search
                'count': 50,     # Maximum results per request
                'start': 0       # Pagination offset
            }
            
            # Step 3: Make API request with authentication
            headers = {
                'Authorization': f'Bearer {self.linkedin_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            logger.info(f"Making LinkedIn API request: {self.linkedin_endpoint}")
            response = requests.get(
                self.linkedin_endpoint,
                params=query_params,
                headers=headers,
                timeout=30
            )
            
            # Step 4: Handle rate limits and errors
            if response.status_code == 429:
                logger.warning("LinkedIn API rate limit exceeded. Retrying after delay...")
                time.sleep(60)  # Wait 1 minute for rate limit reset
                response = requests.get(
                    self.linkedin_endpoint,
                    params=query_params,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                # Fallback to simulation data on API failure
                return self._get_fallback_market_data(target_role)
            
            # Step 5: Parse JSON response
            linkedin_data = response.json()
            
            # Step 6: Convert LinkedIn response to MarketIntelligence schema
            market_intel = self._parse_linkedin_response(linkedin_data, target_role)
            
            logger.info("LinkedIn data fetched and parsed successfully")
            return market_intel
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LinkedIn API request failed: {str(e)}")
            # Fallback to simulation data on network error
            return self._get_fallback_market_data(target_role)
        
        except Exception as e:
            logger.error(f"LinkedIn data fetch failed: {str(e)}")
            # Fallback to simulation data on any other error
            return self._get_fallback_market_data(target_role)
    
    def _authenticate_linkedin(self) -> str:
        """
        Authenticate with LinkedIn API using OAuth2 client credentials flow.
        
        Returns:
            Access token for API requests
            
        Note: This is a simplified implementation. Production code should
        handle token refresh and proper OAuth2 flow.
        """
        auth_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.linkedin_api_key,
            'client_secret': self.linkedin_api_secret
        }
        
        response = requests.post(auth_url, data=auth_data, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"LinkedIn authentication failed: {response.status_code}")
        
        auth_response = response.json()
        return auth_response.get('access_token')
    
    def _parse_linkedin_response(self, linkedin_data: Dict, target_role: str) -> MarketIntelligence:
        """
        Parse LinkedIn API response and convert to MarketIntelligence schema.
        
        Args:
            linkedin_data: Raw LinkedIn API response
            target_role: Target role for context
            
        Returns:
            MarketIntelligence object with parsed data
            
        TODO: Handle pagination for comprehensive data collection
        """
        # Extract job postings from LinkedIn response
        jobs = linkedin_data.get('elements', [])
        
        # Analyze job requirements to extract skills and trends
        core_skills = set()
        preferred_skills = set()
        emerging_trends = set()
        languages = set()
        frameworks = set()
        tools = set()
        
        # Common tech keywords for categorization
        language_keywords = ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#']
        framework_keywords = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'tensorflow', 'pytorch']
        tool_keywords = ['docker', 'kubernetes', 'aws', 'azure', 'git', 'jenkins', 'terraform']
        
        salary_ranges = []
        
        # Process each job posting
        for job in jobs:
            # Extract job description and requirements
            description = job.get('description', {}).get('text', '').lower()
            title = job.get('title', '').lower()
            
            # Extract salary information if available
            salary_info = job.get('salaryInsights', {})
            if salary_info:
                salary_ranges.append(salary_info)
            
            # Extract skills from job description
            for skill in language_keywords:
                if skill in description or skill in title:
                    languages.add(skill)
                    core_skills.add(skill.title())
            
            for skill in framework_keywords:
                if skill in description or skill in title:
                    frameworks.add(skill)
                    preferred_skills.add(skill.title())
            
            for skill in tool_keywords:
                if skill in description or skill in title:
                    tools.add(skill)
                    preferred_skills.add(skill.title())
            
            # Extract emerging trends (AI, ML, Cloud keywords)
            if any(keyword in description for keyword in ['ai', 'machine learning', 'ml']):
                emerging_trends.add('AI/ML Integration')
            if any(keyword in description for keyword in ['cloud', 'aws', 'azure', 'gcp']):
                emerging_trends.add('Cloud Technologies')
            if any(keyword in description for keyword in ['devops', 'ci/cd', 'automation']):
                emerging_trends.add('DevOps Automation')
        
        # Calculate demand level based on job count
        job_count = len(jobs)
        if job_count > 30:
            demand_level = "High"
        elif job_count > 15:
            demand_level = "Medium"
        else:
            demand_level = "Low"
        
        # Calculate salary range from available data
        if salary_ranges:
            # Simplified salary calculation - in production, this would be more sophisticated
            salary_range = "Based on LinkedIn data: Varies by location and experience"
        else:
            salary_range = "Salary data not available from LinkedIn"
        
        # Build MarketIntelligence object
        role_requirements = RoleRequirements(
            core_skills=list(core_skills)[:10],  # Limit to top 10
            preferred_skills=list(preferred_skills)[:10],
            emerging_trends=list(emerging_trends)
        )
        
        tech_stack = TechStackPopularity(
            language=list(languages),
            framework=list(frameworks),
            tools=list(tools)
        )
        
        market_insights = MarketInsights(
            salary_range=salary_range,
            demand_level=demand_level,
            growth_areas=list(emerging_trends)
        )
        
        return MarketIntelligence(
            role_requirements=role_requirements,
            tech_stack_popularity=tech_stack,
            market_insights=market_insights,
            source="linkedin_api"
        )
    
    def _load_market_data(self) -> Dict:
        """Load market data from JSON file."""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Market data file not found: {self.data_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load market data: {str(e)}")
            return {}
    
    def _get_role_market_data(self, target_role: str) -> Optional[MarketIntelligence]:
        """Get market data for a specific role."""
        # Normalize role name
        role_key = self._normalize_role_name(target_role)
        
        if role_key in self.market_data:
            raw_data = self.market_data[role_key]
            return self._convert_to_market_intelligence(raw_data)
        
        return None
    
    def _normalize_role_name(self, role: str) -> str:
        """Normalize role name to match data keys."""
        role_lower = role.lower().strip()
        
        # Direct mapping
        if role_lower in self.role_mappings:
            return self.role_mappings[role_lower]
        
        # Partial matching
        for pattern, key in self.role_mappings.items():
            if pattern in role_lower or role_lower in pattern:
                return key
        
        # Check if it directly matches a key
        role_normalized = role_lower.replace(' ', '_').replace('-', '_')
        if role_normalized in self.market_data:
            return role_normalized
        
        return ""
    
    def _convert_to_market_intelligence(self, raw_data: Dict) -> MarketIntelligence:
        """Convert raw market data to MarketIntelligence object."""
        # Role requirements
        role_req = RoleRequirements(
            core_skills=raw_data.get('core_skills', []),
            preferred_skills=raw_data.get('preferred_skills', []),
            emerging_trends=raw_data.get('emerging_trends', [])
        )
        
        # Tech stack popularity
        tech_stack = TechStackPopularity(
            language=raw_data.get('languages', []),
            framework=raw_data.get('frameworks', []),
            tools=raw_data.get('tools', [])
        )
        
        # Market insights
        market_insights = MarketInsights(
            salary_range=raw_data.get('salary_range', 'Not specified'),
            demand_level=raw_data.get('demand_level', 'Medium'),
            growth_areas=raw_data.get('growth_areas', [])
        )
        
        return MarketIntelligence(
            role_requirements=role_req,
            tech_stack_popularity=tech_stack,
            market_insights=market_insights,
            source="simulation"
        )
    
    def _get_fallback_market_data(self, target_role: str) -> MarketIntelligence:
        """Provide fallback market data for unknown roles."""
        # Generic tech skills based on role keywords
        core_skills = ["Programming", "Problem Solving", "Version Control"]
        preferred_skills = ["Cloud Platforms", "Testing", "Documentation"]
        emerging_trends = ["AI Integration", "Cloud-Native Development", "Security"]
        
        languages = ["Python", "JavaScript", "SQL"]
        frameworks = ["React", "Django", "Docker"]
        tools = ["Git", "Docker", "AWS"]
        
        # Customize based on role keywords
        role_lower = target_role.lower()
        
        if any(keyword in role_lower for keyword in ['ai', 'ml', 'machine learning', 'data']):
            core_skills.extend(["Python", "Machine Learning", "Data Analysis"])
            frameworks.extend(["TensorFlow", "PyTorch", "Pandas"])
            emerging_trends.extend(["MLOps", "LLM Integration"])
        
        elif any(keyword in role_lower for keyword in ['backend', 'api', 'server']):
            core_skills.extend(["API Development", "Database Design", "System Architecture"])
            frameworks.extend(["FastAPI", "PostgreSQL", "Redis"])
        
        elif any(keyword in role_lower for keyword in ['frontend', 'ui', 'react']):
            core_skills.extend(["JavaScript", "React", "CSS"])
            frameworks.extend(["React", "Next.js", "Tailwind CSS"])
        
        elif any(keyword in role_lower for keyword in ['devops', 'infrastructure', 'cloud']):
            core_skills.extend(["Infrastructure as Code", "CI/CD", "Containerization"])
            frameworks.extend(["Terraform", "Kubernetes", "Jenkins"])
        
        elif any(keyword in role_lower for keyword in ['mobile', 'ios', 'android']):
            core_skills.extend(["Mobile Development", "iOS Development", "Android Development"])
            frameworks.extend(["React Native", "Flutter", "Xamarin"])
        
        # Create market intelligence object
        role_req = RoleRequirements(
            core_skills=core_skills,
            preferred_skills=preferred_skills,
            emerging_trends=emerging_trends
        )
        
        tech_stack = TechStackPopularity(
            language=languages,
            framework=frameworks,
            tools=tools
        )
        
        market_insights = MarketInsights(
            salary_range="$80,000 - $150,000",
            demand_level="Medium",
            growth_areas=["Cloud Technologies", "Automation", "Security"]
        )
        
        return MarketIntelligence(
            role_requirements=role_req,
            tech_stack_popularity=tech_stack,
            market_insights=market_insights,
            source="simulation"
        )
    
    def search_tool(self, query: str, role: str, query_source: str = "simulation") -> Dict:
        """
        Search tool that supports both LinkedIn API and simulation modes.
        
        This method provides a consistent interface for different data sources.
        
        Args:
            query: Search query
            role: Target role
            query_source: Data source ("linkedin" or "simulation")
            
        Returns:
            Search results from specified source
            
        Note: search_tool now supports LinkedIn or simulation based on query_source
        """
        logger.info(f"Search tool called: query='{query}', role='{role}', source='{query_source}'")
        
        try:
            # Choose data source based on query_source parameter
            if query_source == "linkedin" and self.use_linkedin:
                # Use LinkedIn Jobs API for real market data
                logger.info("Using LinkedIn API for search tool")
                market_intel = self.fetch_linkedin_data(role)
                source = "linkedin_api"
            else:
                # Use simulation data (default)
                logger.info("Using simulation data for search tool")
                market_intel = self._get_role_market_data(role) or self._get_fallback_market_data(role)
                source = "simulation"
            
            # Return standardized response format
            return {
                "status": "success",
                "source": source,
                "query": query,
                "role": role,
                "results": market_intel,
                "timestamp": "2024-01-01T00:00:00Z",
                "total_results": 1,
                "linkedin_enabled": self.use_linkedin
            }
            
        except Exception as e:
            logger.error(f"Search tool failed: {str(e)}")
            # Fallback to simulation on any error
            fallback_intel = self._get_fallback_market_data(role)
            return {
                "status": "error",
                "source": "simulation_fallback",
                "query": query,
                "role": role,
                "results": fallback_intel,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z",
                "total_results": 1,
                "linkedin_enabled": self.use_linkedin
            }
    
    def get_available_roles(self) -> List[str]:
        """Get list of available roles in the market data."""
        return list(self.market_data.keys())
    
    def get_role_summary(self, role: str) -> Dict:
        """Get a summary of role requirements."""
        market_intel = self._get_role_market_data(role)
        if market_intel:
            return {
                "role": role,
                "core_skills_count": len(market_intel.role_requirements.core_skills),
                "preferred_skills_count": len(market_intel.role_requirements.preferred_skills),
                "emerging_trends_count": len(market_intel.role_requirements.emerging_trends),
                "demand_level": market_intel.market_insights.demand_level,
                "salary_range": market_intel.market_insights.salary_range
            }
        return {}


# Adapter pattern for future real API integration
class LiveAPIAdapter:
    """
    Adapter for integrating with real job market APIs.
    
    This class can be used to replace the simulation with real API calls
    while maintaining the same interface.
    """
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def search_jobs(self, role: str, location: str = "remote") -> Dict:
        """
        Search for jobs using real API.
        
        This method would implement actual API calls to job boards
        like Indeed, LinkedIn, or specialized tech job sites.
        """
        # Placeholder for real implementation
        raise NotImplementedError("Live API integration not implemented")
    
    def get_salary_data(self, role: str, location: str) -> Dict:
        """Get salary data from real sources."""
        raise NotImplementedError("Live API integration not implemented")
    
    def get_skill_trends(self, role: str) -> Dict:
        """Get trending skills from real market data."""
        raise NotImplementedError("Live API integration not implemented")


def market_intelligence_node(state: AnalysisState) -> AnalysisState:
    """
    LangGraph node function for market intelligence gathering.
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with market intelligence data
    """
    agent = MarketIntelligenceAgent()
    return agent.run(state)
