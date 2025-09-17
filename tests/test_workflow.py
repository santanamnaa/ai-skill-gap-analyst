"""
Basic tests for the CV Skill Gap Analysis System
"""

import unittest
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.schemas import AnalysisState, StructuredCV
from src.orchestrator.workflow import create_workflow, LangGraphWorkflow, SimpleWorkflowOrchestrator
from src.agents.cv_parser import CVParserAgent
from src.agents.market_intelligence import MarketIntelligenceAgent


class TestWorkflow(unittest.TestCase):
    """Test the main workflow orchestration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_cv = """
        John Doe
        Software Engineer
        Email: john@example.com
        
        EXPERIENCE
        Software Engineer, Tech Corp (2020-2023)
        • Developed web applications using Python and React
        • Implemented CI/CD pipelines with Docker
        • Led team of 3 developers
        
        SKILLS
        Python, JavaScript, React, Docker, AWS, PostgreSQL
        
        EDUCATION
        Bachelor of Computer Science, University (2016-2020)
        
        PROJECTS
        E-commerce Platform
        Built full-stack application with React and Python Flask
        """
        
        self.target_role = "Senior AI Engineer"
    
    def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        # Test LangGraph workflow creation
        try:
            workflow = create_workflow(use_langgraph=True)
            self.assertIsNotNone(workflow)
            self.assertIsInstance(workflow, (LangGraphWorkflow, SimpleWorkflowOrchestrator))
        except ImportError:
            # Fallback to simple orchestrator if LangGraph not available
            workflow = create_workflow(use_langgraph=False)
            self.assertIsNotNone(workflow)
            self.assertIsInstance(workflow, SimpleWorkflowOrchestrator)
    
    def test_complete_workflow(self):
        """Test complete workflow execution."""
        workflow = create_workflow(use_langgraph=False)  # Use simple orchestrator for reliable testing
        result = workflow.run_analysis(self.sample_cv, self.target_role)
        
        # Check that we have a result
        self.assertIsInstance(result, AnalysisState)
        self.assertEqual(result.target_role, self.target_role)
        
        # Check that CV was parsed
        self.assertIsNotNone(result.cv_structured.personal.name)
        
        # Check that analysis was performed
        self.assertIsNotNone(result.skills_analysis)
        
        # Check that market intelligence was gathered
        self.assertIsNotNone(result.market_intelligence)
        
        # Check that report was generated
        self.assertTrue(len(result.final_report) > 0)


class TestCVParser(unittest.TestCase):
    """Test CV parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = CVParserAgent()
        self.sample_cv = """
        Jane Smith
        Senior Developer
        jane.smith@email.com
        
        EXPERIENCE
        Senior Developer, StartupXYZ (2021-Present)
        • Built microservices with Python and Docker
        • Mentored junior developers
        
        SKILLS
        Python, Docker, Kubernetes, React, PostgreSQL
        """
    
    def test_personal_info_extraction(self):
        """Test personal information extraction."""
        state = AnalysisState(cv_raw=self.sample_cv)
        result = self.parser.parse_cv(state)
        
        self.assertEqual(result.cv_structured.personal.name, "Jane Smith")
        self.assertIn("email", result.cv_structured.personal.contact)
    
    def test_skills_extraction(self):
        """Test skills extraction."""
        state = AnalysisState(cv_raw=self.sample_cv)
        result = self.parser.parse_cv(state)
        
        skills = result.cv_structured.skills
        all_skills = skills.languages + skills.frameworks + skills.tools
        
        self.assertIn("python", all_skills)
        self.assertIn("docker", all_skills)
        self.assertTrue(len(all_skills) > 0)
    
    def test_experience_extraction(self):
        """Test experience extraction."""
        state = AnalysisState(cv_raw=self.sample_cv)
        result = self.parser.parse_cv(state)
        
        experience = result.cv_structured.experience
        self.assertTrue(len(experience) > 0)
        self.assertIn("StartupXYZ", experience[0].company)


class TestMarketIntelligence(unittest.TestCase):
    """Test market intelligence functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = MarketIntelligenceAgent()
    
    def test_role_normalization(self):
        """Test role name normalization."""
        # Test direct mapping
        normalized = self.agent._normalize_role_name("AI Engineer")
        self.assertEqual(normalized, "senior_ai_engineer")
        
        # Test partial matching
        normalized = self.agent._normalize_role_name("Machine Learning Engineer")
        self.assertEqual(normalized, "senior_ai_engineer")
    
    def test_market_data_retrieval(self):
        """Test market data retrieval."""
        state = AnalysisState(target_role="Senior AI Engineer")
        result = self.agent.gather_market_intelligence(state)
        
        market_intel = result.market_intelligence
        self.assertTrue(len(market_intel.role_requirements.core_skills) > 0)
        self.assertEqual(market_intel.source, "simulation")
    
    def test_fallback_data(self):
        """Test fallback data for unknown roles."""
        state = AnalysisState(target_role="Unknown Role")
        result = self.agent.gather_market_intelligence(state)
        
        market_intel = result.market_intelligence
        self.assertTrue(len(market_intel.role_requirements.core_skills) > 0)
        self.assertEqual(market_intel.source, "simulation")


if __name__ == "__main__":
    unittest.main()
