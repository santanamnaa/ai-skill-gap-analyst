#!/usr/bin/env python3
"""
Main CLI interface for CV Skill Gap Analysis System using Typer

Usage:
    python main.py analyze path/to/cv.txt "Senior AI Engineer" --output report.md
    uv run python main.py analyze data/sample_cv.txt "Senior AI Engineer"
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Load environment variables from .env file
load_dotenv()

from src.orchestrator.workflow import run_analysis
from src.schemas import AnalysisState

# I'm using Typer to create a command-line interface and Rich to display nice console output.
app = typer.Typer(
    name="ai-skill-gap-analyst",
    help="A CV skill gap analysis system I built using LangGraph.",
    add_completion=False
)
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('analysis.log')
        ]
    )


def load_cv_file(cv_path: str) -> str:
    # This function handles loading the CV content. It can take both text and PDF files.
    cv_file = Path(cv_path)
    
    if not cv_file.exists():
        raise FileNotFoundError(f"CV file not found: {cv_path}")
    
    if not cv_file.is_file():
        raise ValueError(f"The path provided is not a file: {cv_path}")
    
    # I check the file extension to decide how to process it.
    file_extension = cv_file.suffix.lower()
    
    if file_extension == '.pdf':
        # For PDFs, I'm trying pdfplumber first as it's generally better.
        try:
            import pdfplumber
            
            with pdfplumber.open(cv_file) as pdf:
                content = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
                
                content = content.strip()
                
                if not content:
                    raise ValueError("This PDF seems to be empty or has no text.")
                
                return content
                
        except ImportError:
            # If pdfplumber isn't installed, I'll try PyPDF2 as a fallback.
            try:
                import PyPDF2
                
                with open(cv_file, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    content = ""
                    
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            content += page_text + "\n"
                    
                    content = content.strip()
                    
                    if not content:
                        raise ValueError("This PDF seems to be empty or has no text.")
                    
                    return content
                    
            except ImportError:
                raise ValueError("To process PDFs, you need to install either 'pdfplumber' or 'PyPDF2'.")
        except Exception as e:
            raise ValueError(f"Failed to get text from the PDF: {str(e)}")
    
    else:
        # For other file types, I'll just treat them as plain text.
        try:
            with open(cv_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError("The CV file is empty.")
            
            return content
            
        except UnicodeDecodeError:
            raise ValueError("The file seems to have some invalid characters. Make sure it's a plain text file.")


def save_report(report_content: str, output_path: str) -> None:
    # A simple helper function to save the final report to a file.
    output_file = Path(output_path)
    
    # I'm making sure the directory exists before I try to write the file.
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"Report saved to: {output_file.absolute()}")
        
    except Exception as e:
        print(f"Couldn't save the report: {str(e)}")
        sys.exit(1)


def print_analysis_summary(state: AnalysisState) -> None:
    """Print a summary of the analysis results."""
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    
    # Basic info
    candidate_name = state.cv_structured.personal.name or "Unknown"
    print(f"Candidate: {candidate_name}")
    print(f"Target Role: {state.target_role}")
    
    # Parsing results
    sections_found = 0
    if state.cv_structured.personal.name:
        sections_found += 1
    if state.cv_structured.experience:
        sections_found += 1
    if any([state.cv_structured.skills.languages, state.cv_structured.skills.frameworks, state.cv_structured.skills.tools]):
        sections_found += 1
    if state.cv_structured.education:
        sections_found += 1
    if state.cv_structured.projects:
        sections_found += 1
    
    print(f"CV Sections Parsed: {sections_found}/5")
    
    # Skills analysis
    tech_skills = len(state.skills_analysis.explicit_skills.get('tech', []))
    implicit_skills = len(state.skills_analysis.implicit_skills)
    years_exp = state.skills_analysis.seniority_indicators.years_exp
    
    print(f"Technical Skills: {tech_skills}")
    print(f"Implicit Skills: {implicit_skills}")
    print(f"Experience: {years_exp} years")
    
    # Market intelligence
    demand_level = state.market_intelligence.market_insights.demand_level
    salary_range = state.market_intelligence.market_insights.salary_range
    
    print(f"Market Demand: {demand_level}")
    print(f"Salary Range: {salary_range}")
    
    # Report status
    report_length = len(state.final_report) if state.final_report else 0
    print(f"Report Generated: {report_length:,} characters")
    
    # Errors
    if state.errors:
        print(f"Warnings/Errors: {len(state.errors)}")
        for error in state.errors[:3]:  # Show first 3 errors
            print(f"   • {error}")
        if len(state.errors) > 3:
            print(f"   • ... and {len(state.errors) - 3} more")
    else:
        print("No errors detected")
    
    print("="*60)


@app.command()
def analyze(
    cv_path: Path = typer.Argument(..., help="Path to the CV file.", exists=True, file_okay=True, dir_okay=False),
    role: str = typer.Argument(..., help="The target role, like 'Senior AI Engineer'."),
    output: Path = typer.Option("report.md", "--output", "-o", help="Where to save the report."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable more detailed logging."),
    use_simple: bool = typer.Option(False, "--simple", help="Use a simpler, non-LangGraph orchestrator.")
):
    # This is the main command for the CLI.
    
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    console.print("Starting CV Skill Gap Analysis...", style="bold green")
    console.print(f"CV File: {cv_path}")
    console.print(f"Target Role: {role}")
    console.print(f"Output: {output}")
    
    try:
        # First, load the CV content from the file.
        console.print("\nLoading CV content...")
        cv_content = load_cv_file(str(cv_path))
        logger.info(f"Loaded a CV with {len(cv_content)} characters.")
        
        # Then, run the analysis workflow.
        console.print("Running the analysis workflow...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running the analysis pipeline...", total=None)
            result_state = run_analysis(cv_content, role)
            progress.update(task, completed=True)
        
        # Show a summary in the console.
        print_analysis_summary(result_state)
        
        # And save the full report to a file.
        if result_state.final_report:
            console.print(f"\nSaving report to {output}...")
            save_report(result_state.final_report, str(output))
        else:
            console.print("No report was generated, likely due to errors.", style="bold red")
            if result_state.errors:
                console.print("Errors found:")
                for error in result_state.errors:
                    console.print(f"  - {error}")
            raise typer.Exit(1)
        
        console.print("\nAnalysis complete!", style="bold green")
        console.print(f"You can find the report in: {output}")
        
    except FileNotFoundError as e:
        console.print(f"Error: {str(e)}", style="bold red")
        raise typer.Exit(1)
    
    except ValueError as e:
        console.print(f"Error: {str(e)}", style="bold red")
        raise typer.Exit(1)
    
    except KeyboardInterrupt:
        console.print("\nAnalysis stopped by user.")
        raise typer.Exit(1)
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        console.print(f"An unexpected error occurred: {str(e)}", style="bold red")
        console.print("Check the analysis.log file for more details.")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    console.print("AI Skill Gap Analyst v0.1.0")
    console.print("LangGraph-based multi-agent CV analysis system")


@app.command()
def demo():
    """Run a demo analysis with sample data."""
    sample_cv = Path("data/sample_cv.txt")
    if not sample_cv.exists():
        console.print("Sample CV not found at data/sample_cv.txt", style="bold red")
        console.print("Please ensure the sample data exists or use the analyze command with your own CV.")
        raise typer.Exit(1)
    
    console.print("Running demo analysis with sample CV...")
    analyze(
        cv_path=sample_cv,
        role="Senior AI Engineer",
        output=Path("demo_report.md"),
        verbose=False,
        use_simple=False
    )


if __name__ == "__main__":
    app()
