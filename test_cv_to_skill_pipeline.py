"""
Test Pipeline: CV Parser -> Skill Analysis
Menggunakan CV PDF asli untuk menguji alur lengkap dari parsing CV hingga analisis skill.
"""

import os
import sys
import unittest
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from src.agents.cv_parser import CVParserAgent
from src.agents.skill_analyst import SkillAnalystAgent
from src.schemas import AnalysisState, StructuredCV

# Try to import PDF reading capability
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pdfplumber
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestCVToSkillPipeline(unittest.TestCase):
    """Test pipeline dari CV Parser ke Skill Analysis menggunakan CV PDF asli."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cv_parser = CVParserAgent()
        self.skill_analyst = SkillAnalystAgent()
        self.cv_pdf_path = "/Users/santana_mena/Desktop/langgraph/ai-skill-gap-analyst/data/CV_ATS_SantanaMena.pdf"
        self.cv_txt_path = "/Users/santana_mena/Desktop/langgraph/ai-skill-gap-analyst/data/sample_cv.txt"
        
        # Verify CV files exist
        if not Path(self.cv_txt_path).exists():
            self.skipTest(f"Sample CV file not found: {self.cv_txt_path}")
    
    def read_cv_file(self, file_path: str) -> str:
        """Read CV content from file (supports both TXT and PDF)."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"CV file not found: {file_path}")
        
        if path.suffix.lower() == '.pdf':
            if not PDF_AVAILABLE:
                raise ImportError("PDF reading libraries not available. Install PyPDF2 or pdfplumber.")
            return self._read_pdf(file_path)
        else:
            # Read as text file
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    
    def _read_pdf(self, pdf_path: str) -> str:
        """Read text content from PDF file."""
        try:
            # Try pdfplumber first (better text extraction)
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text.strip()
        except ImportError:
            # Fallback to PyPDF2
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text.strip()
    
    def test_cv_parser_basic_functionality(self):
        """Test CV Parser dengan CV teks."""
        logger.info("🔍 Testing CV Parser with sample CV...")
        
        # Read CV content
        cv_content = self.read_cv_file(self.cv_txt_path)
        
        # Create initial state with CV content
        state = AnalysisState(cv_raw=cv_content)
        
        # Parse CV
        result_state = self.cv_parser.run(state)
        
        # Verify parsing results
        self.assertIsNotNone(result_state.cv_structured, "CV should be parsed successfully")
        self.assertIsInstance(result_state.cv_structured, StructuredCV)
        
        # Check personal info
        personal = result_state.cv_structured.personal
        self.assertIsNotNone(personal.name, "Name should be extracted")
        self.assertTrue(len(personal.name.strip()) > 0, "Name should not be empty")
        
        # Check skills
        skills = result_state.cv_structured.skills
        total_skills = len(skills.languages) + len(skills.frameworks) + len(skills.tools)
        self.assertGreater(total_skills, 0, "Should extract some technical skills")
        
        # Check experience
        self.assertGreater(len(result_state.cv_structured.experience), 0, "Should extract work experience")
        
        # Log results
        logger.info(f"PASS CV Parser Results:")
        logger.info(f"   Name: {personal.name}")
        logger.info(f"   Languages: {skills.languages}")
        logger.info(f"   Frameworks: {skills.frameworks}")
        logger.info(f"   Tools: {skills.tools}")
        logger.info(f"   Experience entries: {len(result_state.cv_structured.experience)}")
        logger.info(f"   Projects: {len(result_state.cv_structured.projects)}")
        logger.info(f"   Education: {len(result_state.cv_structured.education)}")
        
        return result_state
    
    def test_skill_analysis_with_parsed_cv(self):
        """Test Skill Analysis dengan hasil dari CV Parser."""
        logger.info("🧠 Testing Skill Analysis with parsed CV...")
        
        # Read CV content and create state
        cv_content = self.read_cv_file(self.cv_txt_path)
        state = AnalysisState(cv_raw=cv_content)
        
        # First parse the CV
        parsed_state = self.cv_parser.run(state)
        
        # Verify CV was parsed successfully
        self.assertIsNotNone(parsed_state.cv_structured)
        self.assertTrue(len(parsed_state.cv_structured.personal.name.strip()) > 0)
        
        # Run skill analysis
        analyzed_state = self.skill_analyst.run(parsed_state)
        
        # Verify skill analysis results
        self.assertIsNotNone(analyzed_state.skills_analysis, "Skills analysis should be completed")
        
        analysis = analyzed_state.skills_analysis
        
        # Check explicit skills
        self.assertIsNotNone(analysis.explicit_skills)
        self.assertIn('tech', analysis.explicit_skills)
        self.assertIn('domain', analysis.explicit_skills)
        self.assertIn('soft', analysis.explicit_skills)
        
        # Check implicit skills
        self.assertIsNotNone(analysis.implicit_skills)
        self.assertIsInstance(analysis.implicit_skills, list)
        
        # Check transferable skills
        self.assertIsNotNone(analysis.transferable_skills)
        self.assertIsInstance(analysis.transferable_skills, list)
        
        # Check seniority indicators
        self.assertIsNotNone(analysis.seniority_indicators)
        
        # Log detailed results
        logger.info(f"PASS Skill Analysis Results:")
        logger.info(f"   Technical Skills: {analysis.explicit_skills['tech']}")
        logger.info(f"   Domain Skills: {analysis.explicit_skills['domain']}")
        logger.info(f"   Soft Skills: {analysis.explicit_skills['soft']}")
        logger.info(f"   Implicit Skills Count: {len(analysis.implicit_skills)}")
        logger.info(f"   Transferable Skills Count: {len(analysis.transferable_skills)}")
        logger.info(f"   Years Experience: {analysis.seniority_indicators.years_exp}")
        logger.info(f"   Leadership: {analysis.seniority_indicators.leadership}")
        logger.info(f"   Architecture: {analysis.seniority_indicators.architecture}")
        
        # Log some implicit skills details
        if analysis.implicit_skills:
            logger.info("   Top Implicit Skills:")
            for skill in analysis.implicit_skills[:5]:  # Show first 5
                logger.info(f"     - {skill.skill} (confidence: {skill.confidence})")
        
        # Log some transferable skills
        if analysis.transferable_skills:
            logger.info("   Transferable Skills:")
            for skill in analysis.transferable_skills[:3]:  # Show first 3
                logger.info(f"     - {skill.skill} from {skill.from_domain}")
        
        return analyzed_state
    
    def test_full_pipeline_cv_to_skills(self):
        """Test pipeline lengkap: CV Text -> Parsed CV -> Skills Analysis."""
        logger.info("🚀 Testing Full Pipeline: CV Text -> Skills Analysis...")
        
        # Step 1: Parse CV
        logger.info("Step 1: Parsing CV text...")
        cv_content = self.read_cv_file(self.cv_txt_path)
        state = AnalysisState(cv_raw=cv_content)
        parsed_state = self.cv_parser.run(state)
        
        # Verify parsing
        self.assertIsNotNone(parsed_state.cv_structured)
        self.assertEqual(len(parsed_state.errors), 0, f"CV parsing should not have errors: {parsed_state.errors}")
        
        # Step 2: Analyze skills
        logger.info("Step 2: Analyzing skills...")
        final_state = self.skill_analyst.run(parsed_state)
        
        # Verify final results
        self.assertIsNotNone(final_state.skills_analysis)
        self.assertEqual(len(final_state.errors), 0, f"Skill analysis should not have errors: {final_state.errors}")
        
        # Comprehensive verification
        cv = final_state.cv_structured
        analysis = final_state.skills_analysis
        
        # CV should have meaningful data
        self.assertTrue(len(cv.personal.name.strip()) > 0, "Should have extracted name")
        total_skills = len(cv.skills.languages) + len(cv.skills.frameworks) + len(cv.skills.tools)
        self.assertGreater(total_skills, 0, "Should have extracted technical skills")
        
        # Analysis should have meaningful results
        total_explicit = len(analysis.explicit_skills.get('tech', [])) + len(analysis.explicit_skills.get('domain', [])) + len(analysis.explicit_skills.get('soft', []))
        self.assertGreater(total_explicit, 0, "Should have identified explicit skills")
        
        # Final summary
        logger.info("🎉 PIPELINE TEST RESULTS:")
        logger.info("=" * 60)
        logger.info(f"CV Candidate: {cv.personal.name}")
        logger.info(f"Total Technical Skills: {len(cv.skills.languages + cv.skills.frameworks + cv.skills.tools)}")
        logger.info(f"Work Experience Entries: {len(cv.experience)}")
        logger.info(f"Projects: {len(cv.projects)}")
        logger.info(f"Education: {len(cv.education)}")
        logger.info(f"Explicit Skills: {total_explicit}")
        logger.info(f"Implicit Skills: {len(analysis.implicit_skills)}")
        logger.info(f"Transferable Skills: {len(analysis.transferable_skills)}")
        logger.info(f"Years Experience: {analysis.seniority_indicators.years_exp}")
        logger.info(f"Leadership Indicators: {analysis.seniority_indicators.leadership}")
        logger.info(f"Architecture Experience: {analysis.seniority_indicators.architecture}")
        logger.info("=" * 60)
        
        return final_state
    
    @unittest.skipUnless(os.getenv('USE_SPACY_PARSER') == 'true', "spaCy mode not enabled")
    def test_pipeline_with_spacy_mode(self):
        """Test pipeline dengan spaCy parsing mode."""
        logger.info("🔬 Testing Pipeline with spaCy NER mode...")
        
        # Run full pipeline with spaCy mode
        cv_content = self.read_cv_file(self.cv_txt_path)
        state = AnalysisState(cv_raw=cv_content)
        parsed_state = self.cv_parser.run(state)
        final_state = self.skill_analyst.run(parsed_state)
        
        # Should work the same as regex mode
        self.assertIsNotNone(final_state.cv_structured)
        self.assertIsNotNone(final_state.skills_analysis)
        
        logger.info("PASS spaCy mode pipeline test completed")
    
    @unittest.skipUnless(os.getenv('USE_LLM_ANALYST') == 'true', "LLM mode not enabled")
    def test_pipeline_with_llm_analysis(self):
        """Test pipeline dengan LLM-powered skill analysis."""
        logger.info("Testing Pipeline with LLM Analysis mode...")
        
        # Run pipeline with LLM analysis
        cv_content = self.read_cv_file(self.cv_txt_path)
        state = AnalysisState(cv_raw=cv_content)
        parsed_state = self.cv_parser.run(state)
        final_state = self.skill_analyst.run(parsed_state)
        
        # Should work (or fallback gracefully)
        self.assertIsNotNone(final_state.skills_analysis)
        
        logger.info("PASS LLM analysis mode pipeline test completed")
    
    def test_error_handling_invalid_cv(self):
        """Test error handling dengan CV content yang tidak valid."""
        logger.info("Testing error handling with invalid CV content...")
        
        # Test with empty CV content
        state = AnalysisState(cv_raw="")
        result_state = self.cv_parser.run(state)
        
        # Should handle gracefully
        self.assertGreater(len(result_state.errors), 0, "Should have error for invalid file")
        
        logger.info(f"PASS Error handling test completed. Errors: {result_state.errors}")


if __name__ == '__main__':
    print("Testing CV Parser -> Skill Analysis Pipeline")
    print("Using sample CV: data/sample_cv.txt")
    print("PDF support available with PyPDF2 or pdfplumber")
    print("=" * 70)
        
    # Run tests with high verbosity
    unittest.main(verbosity=2, exit=False)
        
    print("\n" + "=" * 70)
    print("Pipeline tests completed!")
    print("\nTo test with advanced modes:")
    print("USE_SPACY_PARSER=true python3 test_cv_to_skill_pipeline.py")
    print("USE_LLM_ANALYST=true python3 test_cv_to_skill_pipeline.py")
    print("\nTo test with PDF:")
    print("pip install pdfplumber  # or PyPDF2")
    print("# Then modify test to use self.cv_pdf_path")
