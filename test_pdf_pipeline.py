"""
Test Pipeline dengan CV PDF Asli
Memerlukan pdfplumber atau PyPDF2 untuk membaca PDF.

Install: pip install pdfplumber
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
    import pdfplumber
    PDF_AVAILABLE = True
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        PDF_AVAILABLE = True
        PDF_LIBRARY = "PyPDF2"
    except ImportError:
        PDF_AVAILABLE = False
        PDF_LIBRARY = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestPDFPipeline(unittest.TestCase):
    """Test pipeline menggunakan CV PDF asli Santana Mena."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cv_parser = CVParserAgent()
        self.skill_analyst = SkillAnalystAgent()
        self.cv_pdf_path = "/Users/santana_mena/Desktop/langgraph/ai-skill-gap-analyst/data/CV_ATS_SantanaMena.pdf"
        
        # Skip tests if PDF library not available
        if not PDF_AVAILABLE:
            self.skipTest("PDF reading library not available. Install pdfplumber or PyPDF2.")
        
        # Verify PDF file exists
        if not Path(self.cv_pdf_path).exists():
            self.skipTest(f"PDF file not found: {self.cv_pdf_path}")
    
    def read_pdf(self, pdf_path: str) -> str:
        """Read text content from PDF file."""
        if PDF_LIBRARY == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text.strip()
        else:  # PyPDF2
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text.strip()
    
    def test_pdf_reading(self):
        """Test membaca PDF CV Santana Mena."""
        logger.info(f"📄 Testing PDF reading with {PDF_LIBRARY}...")
        
        # Read PDF content
        pdf_content = self.read_pdf(self.cv_pdf_path)
        
        # Verify content was extracted
        self.assertIsNotNone(pdf_content)
        self.assertTrue(len(pdf_content.strip()) > 0, "PDF should contain text")
        self.assertGreater(len(pdf_content), 100, "PDF should contain substantial text")
        
        # Log first few lines for verification
        lines = pdf_content.split('\n')[:10]
        logger.info("First 10 lines from PDF:")
        for i, line in enumerate(lines, 1):
            if line.strip():
                logger.info(f"   {i}: {line.strip()}")
        
        logger.info(f"PASS PDF reading successful. Total characters: {len(pdf_content)}")
        return pdf_content
    
    def test_pdf_cv_parsing(self):
        """Test parsing CV PDF Santana Mena."""
        logger.info("Testing CV Parser with Santana Mena PDF...")
        
        # Read PDF content
        pdf_content = self.read_pdf(self.cv_pdf_path)
        
        # Create state with PDF content
        state = AnalysisState(cv_raw=pdf_content)
        
        # Parse CV
        result_state = self.cv_parser.run(state)
        
        # Verify parsing results
        self.assertIsNotNone(result_state.cv_structured, "CV should be parsed successfully")
        self.assertIsInstance(result_state.cv_structured, StructuredCV)
        
        # Check personal info
        personal = result_state.cv_structured.personal
        self.assertIsNotNone(personal.name, "Name should be extracted")
        
        # Check skills
        skills = result_state.cv_structured.skills
        total_skills = len(skills.languages) + len(skills.frameworks) + len(skills.tools)
        
        # Log detailed results
        logger.info(f"PASS PDF CV Parser Results:")
        logger.info(f"   Name: {personal.name}")
        logger.info(f"   Contact Info: {personal.contact}")
        logger.info(f"   Languages: {skills.languages}")
        logger.info(f"   Frameworks: {skills.frameworks}")
        logger.info(f"   Tools: {skills.tools}")
        logger.info(f"   Total Skills: {total_skills}")
        logger.info(f"   Experience entries: {len(result_state.cv_structured.experience)}")
        logger.info(f"   Projects: {len(result_state.cv_structured.projects)}")
        logger.info(f"   Education: {len(result_state.cv_structured.education)}")
        logger.info(f"   Parsing errors: {len(result_state.errors)}")
        
        if result_state.errors:
            logger.warning(f"   Errors: {result_state.errors}")
        
        return result_state
    
    def test_full_pdf_pipeline(self):
        """Test pipeline lengkap: PDF -> CV Parser -> Skill Analysis."""
        logger.info("🚀 Testing Full PDF Pipeline: Santana Mena CV...")
        
        # Step 1: Read PDF
        logger.info("Step 1: Reading PDF...")
        pdf_content = self.read_pdf(self.cv_pdf_path)
        
        # Step 2: Parse CV
        logger.info("Step 2: Parsing CV...")
        state = AnalysisState(cv_raw=pdf_content)
        parsed_state = self.cv_parser.run(state)
        
        # Verify parsing
        self.assertIsNotNone(parsed_state.cv_structured)
        
        # Step 3: Analyze skills
        logger.info("Step 3: Analyzing skills...")
        final_state = self.skill_analyst.run(parsed_state)
        
        # Verify final results
        self.assertIsNotNone(final_state.skills_analysis)
        
        # Comprehensive results
        cv = final_state.cv_structured
        analysis = final_state.skills_analysis
        
        # Final summary
        logger.info("🎉 SANTANA MENA CV ANALYSIS RESULTS:")
        logger.info("=" * 70)
        logger.info(f"Candidate: {cv.personal.name}")
        logger.info(f"Contact: {cv.personal.contact}")
        logger.info(f"Total Technical Skills: {len(cv.skills.languages + cv.skills.frameworks + cv.skills.tools)}")
        logger.info(f"Work Experience Entries: {len(cv.experience)}")
        logger.info(f"Projects: {len(cv.projects)}")
        logger.info(f"Education: {len(cv.education)}")
        
        if analysis.explicit_skills:
            total_explicit = len(analysis.explicit_skills.get('tech', [])) + len(analysis.explicit_skills.get('domain', [])) + len(analysis.explicit_skills.get('soft', []))
            logger.info(f"Explicit Skills: {total_explicit}")
            logger.info(f"  - Technical: {analysis.explicit_skills.get('tech', [])}")
            logger.info(f"  - Domain: {analysis.explicit_skills.get('domain', [])}")
            logger.info(f"  - Soft: {analysis.explicit_skills.get('soft', [])}")
        
        logger.info(f"Implicit Skills: {len(analysis.implicit_skills)}")
        if analysis.implicit_skills:
            logger.info("  Top Implicit Skills:")
            for skill in analysis.implicit_skills[:5]:
                logger.info(f"    - {skill.skill} (confidence: {skill.confidence})")
        
        logger.info(f"Transferable Skills: {len(analysis.transferable_skills)}")
        if analysis.transferable_skills:
            logger.info("  Transferable Skills:")
            for skill in analysis.transferable_skills[:3]:
                logger.info(f"    - {skill.skill} from {skill.from_domain}")
        
        if analysis.seniority_indicators:
            logger.info(f"Years Experience: {analysis.seniority_indicators.years_exp}")
            logger.info(f"Leadership Indicators: {analysis.seniority_indicators.leadership}")
            logger.info(f"Architecture Experience: {analysis.seniority_indicators.architecture}")
        
        logger.info(f"Processing Errors: {len(final_state.errors)}")
        if final_state.errors:
            for error in final_state.errors:
                logger.warning(f"  - {error}")
        
        logger.info("=" * 70)
        
        return final_state
    
    @unittest.skipUnless(os.getenv('USE_SPACY_PARSER') == 'true', "spaCy mode not enabled")
    def test_pdf_with_spacy_mode(self):
        """Test PDF parsing dengan spaCy NER mode."""
        logger.info("Testing PDF with spaCy NER mode...")
        
        pdf_content = self.read_pdf(self.cv_pdf_path)
        state = AnalysisState(cv_raw=pdf_content)
        parsed_state = self.cv_parser.run(state)
        final_state = self.skill_analyst.run(parsed_state)
        
        self.assertIsNotNone(final_state.cv_structured)
        self.assertIsNotNone(final_state.skills_analysis)
        
        logger.info("PASS spaCy mode PDF test completed")
    
    @unittest.skipUnless(os.getenv('USE_LLM_ANALYST') == 'true', "LLM mode not enabled")
    def test_pdf_with_llm_analysis(self):
        """Test PDF dengan LLM-powered skill analysis."""
        logger.info("Testing PDF with LLM Analysis mode...")
        
        pdf_content = self.read_pdf(self.cv_pdf_path)
        state = AnalysisState(cv_raw=pdf_content)
        parsed_state = self.cv_parser.run(state)
        final_state = self.skill_analyst.run(parsed_state)
        
        self.assertIsNotNone(final_state.skills_analysis)
        
        logger.info("PASS LLM analysis mode PDF test completed")


if __name__ == '__main__':
    print("Testing CV Pipeline with Santana Mena PDF")
    print(f"PDF Library: {PDF_LIBRARY if PDF_AVAILABLE else 'Not Available'}")
    print("=" * 70)
    
    if not PDF_AVAILABLE:
        print("PDF reading library not available!")
        print("Install with: pip install pdfplumber")
        print("Or: pip install PyPDF2")
        exit(1)
    
    # Run tests with high verbosity
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 70)
    print("PDF Pipeline tests completed!")
    print("\nTo test with advanced modes:")
    print("USE_SPACY_PARSER=true python3 test_pdf_pipeline.py")
    print("USE_LLM_ANALYST=true python3 test_pdf_pipeline.py")
