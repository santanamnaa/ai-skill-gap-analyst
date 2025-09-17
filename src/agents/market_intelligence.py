"""
Market Intelligence Agent

This agent gathers current market demands for specified technical roles.
Role: Market Researcher in the multi-agent system.

## LinkedIn API Integration

The agent supports both simulation mode and real LinkedIn Jobs API integration:

### Environment Variables Required:
- LINKEDIN_API_KEY: Your LinkedIn API application key
- LINKEDIN_API_SECRET: Your LinkedIn API application secret

### How to Enable LinkedIn Mode:
Set `use_linkedin=True` in agent constructor or via CLI flag.

### LinkedIn API Documentation:
https://docs.microsoft.com/en-us/linkedin/talent/integrations/job-search

### Usage Examples:
```python
# Simulation mode (default)
agent = MarketIntelligenceAgent()

# LinkedIn API mode
agent = MarketIntelligenceAgent(use_linkedin=True)
```
"""

import json
import os
import requests
from typing import Dict, List, Optional
import logging
from pathlib import Path
import time

from ..schemas import (
    AnalysisState, MarketIntelligence, RoleRequirements, 
    TechStackPopularity, MarketInsights
)

logger = logging.getLogger(__name__)


class MarketIntelligenceAgent:
    """
    Market Intelligence Agent that provides market analysis for technical roles.
    
    Uses simulation data for zero-cost implementation with adapter pattern
    for future real API integration.
    """
    
    def __init__(self, use_linkedin: bool = False):
        """
        Initialize Market Intelligence Agent.
        
        Args:
            use_linkedin: Enable LinkedIn Jobs API integration (requires env vars)
        
        Environment Variables for LinkedIn API:
            LINKEDIN_API_KEY: Your LinkedIn API application key
            LINKEDIN_API_SECRET: Your LinkedIn API application secret
        """
        self.data_path = Path(__file__).parent.parent.parent / "data" / "market_data.json"
        self.market_data = self._load_market_data()
        
        # LinkedIn API Configuration
        self.use_linkedin = use_linkedin
        self.linkedin_api_key = os.getenv('LINKEDIN_API_KEY')
        self.linkedin_api_secret = os.getenv('LINKEDIN_API_SECRET')
        self.linkedin_endpoint = "https://api.linkedin.com/v2/jobSearch"
        self.linkedin_token = None
        
        # Validate LinkedIn configuration if enabled
        if self.use_linkedin:
            if not self.linkedin_api_key or not self.linkedin_api_secret:
                logger.warning(
                    "LinkedIn API enabled but credentials not found. "
                    "Set LINKEDIN_API_KEY and LINKEDIN_API_SECRET environment variables. "
                    "Falling back to simulation mode."
                )
                self.use_linkedin = False
            else:
                logger.info("LinkedIn API integration enabled")
        
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
    
    def gather_market_intelligence(self, state: AnalysisState) -> AnalysisState:
        """
        Main market intelligence gathering function.
        
        Args:
            state: Analysis state with target role
            
        Returns:
            Updated state with market intelligence data
        
        Note: To enable LinkedIn: set use_linkedin=True and configure env vars.
        """
        try:
            logger.info(f"Gathering market intelligence for role: {state.target_role}")
            
            if not state.target_role.strip():
                state.add_error("No target role specified for market intelligence")
                return state
            
            # Choose data source based on configuration
            if self.use_linkedin:
                # Use LinkedIn Jobs API for real market data
                logger.info("Using LinkedIn Jobs API for market intelligence")
                market_intel = self.fetch_linkedin_data(state.target_role)
            else:
                # Use simulation data (default)
                logger.info("Using simulation data for market intelligence")
                market_intel = self._get_role_market_data(state.target_role)
                
                if not market_intel:
                    # Fallback to generic data
                    market_intel = self._get_fallback_market_data(state.target_role)
                    logger.warning(f"Using fallback data for role: {state.target_role}")
            
            state.market_intelligence = market_intel
            logger.info("Market intelligence gathering completed successfully")
            
        except Exception as e:
            error_msg = f"Market intelligence gathering failed: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
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
    return agent.gather_market_intelligence(state)
