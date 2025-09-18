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

from src.schemas import AnalysisState
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
        self.assertIsNotNone(result.structured_cv.personal.name)
        
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
        result = self.parser.run(state)
        
        self.assertEqual(result.structured_cv.personal.name, "Jane Smith")
        self.assertIn("email", result.structured_cv.personal.contact)
    
    def test_skills_extraction(self):
        """Test skills extraction."""
        state = AnalysisState(cv_raw=self.sample_cv)
        result = self.parser.run(state)
        
        skills = result.structured_cv.skills
        all_skills = skills.languages + skills.frameworks + skills.tools
        
        self.assertIn("python", all_skills)
        self.assertIn("docker", all_skills)
        self.assertTrue(len(all_skills) > 0)
    
    def test_experience_extraction(self):
        """Test experience extraction."""
        state = AnalysisState(cv_raw=self.sample_cv)
        result = self.parser.run(state)
        
        experience = result.structured_cv.experience
        self.assertTrue(len(experience) > 0)
        self.assertIn("StartupXYZ", experience[0].company)
    
    def test_regex_parsing_mode(self):
        """Test regex parsing mode explicitly."""
        # Ensure regex mode
        os.environ['USE_SPACY_PARSER'] = 'false'
        parser = CVParserAgent()
        
        state = AnalysisState(cv_raw=self.sample_cv)
        result = parser.run(state)
        
        self.assertIsNotNone(result.structured_cv.personal.name)
        self.assertTrue(len(result.structured_cv.skills.languages + 
                           result.structured_cv.skills.frameworks + 
                           result.structured_cv.skills.tools) > 0)
    
    def test_spacy_parsing_mode(self):
        """Test spaCy parsing mode with fallback."""
        # Set spaCy mode
        os.environ['USE_SPACY_PARSER'] = 'true'
        parser = CVParserAgent()
        
        state = AnalysisState(cv_raw=self.sample_cv)
        result = parser.run(state)
        
        # Should work either with spaCy or fallback to regex
        self.assertIsNotNone(result.structured_cv.personal.name)
        self.assertTrue(len(result.structured_cv.skills.languages + 
                           result.structured_cv.skills.frameworks + 
                           result.structured_cv.skills.tools) > 0)
    
    def test_cv_parser_spacy_fallback(self):
        """Test spaCy failure fallback to regex parsing."""
        # Mock spaCy failure by setting environment but ensuring fallback works
        os.environ['USE_SPACY_PARSER'] = 'true'
        parser = CVParserAgent()
        
        # Force spaCy to None to simulate failure
        parser._spacy_nlp = None
        
        state = AnalysisState(cv_raw=self.sample_cv)
        
        # Mock spaCy import failure by temporarily modifying the parse_with_spacy method
        original_method = parser.parse_with_spacy
        def mock_spacy_failure(text):
            # Simulate spaCy failure and fallback
            return parser.parse_with_regex(text)
        
        parser.parse_with_spacy = mock_spacy_failure
        
        result = parser.run(state)
        
        # Should successfully parse using regex fallback
        self.assertIsNotNone(result.structured_cv.personal.name)
        self.assertTrue(len(result.structured_cv.skills.languages + 
                           result.structured_cv.skills.frameworks + 
                           result.structured_cv.skills.tools) > 0)
        
        # Restore original method
        parser.parse_with_spacy = original_method
        
        # Clean up environment
        if 'USE_SPACY_PARSER' in os.environ:
            del os.environ['USE_SPACY_PARSER']


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
