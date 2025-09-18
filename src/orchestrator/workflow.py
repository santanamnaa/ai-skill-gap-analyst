"""
## Updated by AI Agent on September 18, 2025
LangGraph-based workflow orchestrator for CV Skill Gap Analysis.
Coordinates CV Parser → Skill Analyst → Market Intelligence → Report Generator pipeline.
"""

import os
import logging
import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from ..schemas import AnalysisState
from ..agents.cv_parser import CVParserAgent
from ..agents.skill_analyst import SkillAnalystAgent  
from ..agents.market_intelligence import MarketIntelligenceAgent
from ..agents.report_generator import ReportGeneratorAgent

logger = logging.getLogger(__name__)


# Environment Configuration
def _log_environment_config() -> None:
    """Log active environment configuration at startup."""
    config = {
        'USE_SPACY_PARSER': os.getenv('USE_SPACY_PARSER', 'false'),
        'USE_LLM_ANALYST': os.getenv('USE_LLM_ANALYST', 'false'),
        'USE_RAG': os.getenv('USE_RAG', 'false'),
        'USE_LLM_REPORT': os.getenv('USE_LLM_REPORT', 'false')
    }
    
    logger.info("Active Environment Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")


# Node Functions with Error Handling and Validation
def parse_cv(state: AnalysisState) -> AnalysisState:
    """
    CV Parser node with error handling and state validation.
    
    Args:
        state: Analysis state with CV raw content
        
    Returns:
        Updated state with structured CV data
    """
    start_time = time.time()
    logger.info("Starting CV Parser node")
    
    try:
        # State validation
        if not state.cv_raw.strip():
            logger.warning("No CV content provided to parser")
            state.add_error("Empty CV content provided")
            return state
        
        # Execute CV parser
        parser = CVParserAgent()
        result_state = parser.run(state)
        
        # Log execution time
        execution_time = time.time() - start_time
        logger.info(f"CV Parser completed in {execution_time:.2f}s")
        
        # Validation check
        if not result_state.cv_structured.personal.name:
            logger.warning("CV Parser did not extract candidate name")
        
        return result_state
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"CV Parser failed after {execution_time:.2f}s: {str(e)}"
        logger.error(f"{error_msg}")
        state.add_error(error_msg)
        return state


def analyze_skills(state: AnalysisState) -> AnalysisState:
    """
    Skill Analyst node with error handling and state validation.
    
    Args:
        state: Analysis state with structured CV data
        
    Returns:
        Updated state with skills analysis
    """
    start_time = time.time()
    logger.info("Starting Skill Analyst node")
    
    try:
        # State validation
        if not state.cv_structured.personal.name:
            logger.warning("No structured CV data available for skill analysis")
            state.add_error("Prerequisites missing: structured CV data required")
            return state
        
        # Execute skill analyst
        analyst = SkillAnalystAgent()
        result_state = analyst.run(state)
        
        # Log execution time
        execution_time = time.time() - start_time
        logger.info(f"Skill Analyst completed in {execution_time:.2f}s")
        
        # Validation check
        if result_state.skills_analysis and result_state.skills_analysis.explicit_skills:
            skill_count = len(result_state.skills_analysis.explicit_skills.get('tech', []))
            logger.info(f"   Identified {skill_count} technical skills")
        
        return result_state
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Skill Analyst failed after {execution_time:.2f}s: {str(e)}"
        logger.error(f"{error_msg}")
        state.add_error(error_msg)
        return state


def gather_market_intel(state: AnalysisState) -> AnalysisState:
    """
    Market Intelligence node with error handling and state validation.
    
    Args:
        state: Analysis state with target role
        
    Returns:
        Updated state with market intelligence data
    """
    start_time = time.time()
    logger.info("Starting Market Intelligence node")
    
    try:
        # State validation
        if not state.target_role.strip():
            logger.warning("No target role specified for market intelligence")
            state.add_error("Prerequisites missing: target role required")
            return state
        
        # Execute market intelligence
        market_agent = MarketIntelligenceAgent()
        result_state = market_agent.run(state)
        
        # Log execution time
        execution_time = time.time() - start_time
        logger.info(f"Market Intelligence completed in {execution_time:.2f}s")
        
        # Validation check
        if result_state.market_intelligence:
            demand_level = result_state.market_intelligence.market_insights.demand_level
            logger.info(f"   Market demand level: {demand_level}")
        
        return result_state
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Market Intelligence failed after {execution_time:.2f}s: {str(e)}"
        logger.error(f"{error_msg}")
        state.add_error(error_msg)
        return state


def generate_report(state: AnalysisState) -> AnalysisState:
    """
    Report Generator node with error handling and state validation.
    
    Args:
        state: Analysis state with all collected data
        
    Returns:
        Updated state with final report
    """
    start_time = time.time()
    logger.info("Starting Report Generator node")
    
    try:
        # State validation
        if not state.cv_structured.personal.name:
            logger.warning("No candidate data available for report generation")
            state.add_error("Prerequisites missing: candidate data required")
            return state
        
        if not state.target_role:
            logger.warning("No target role specified for report generation")
            state.add_error("Prerequisites missing: target role required")
            return state
        
        # Execute report generator
        report_agent = ReportGeneratorAgent()
        result_state = report_agent.run(state)
        
        # Log execution time
        execution_time = time.time() - start_time
        logger.info(f"Report Generator completed in {execution_time:.2f}s")
        
        # Validation check
        if result_state.final_report:
            report_length = len(result_state.final_report)
            logger.info(f"   Generated report: {report_length} characters")
        
        return result_state
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Report Generator failed after {execution_time:.2f}s: {str(e)}"
        logger.error(f"{error_msg}")
        state.add_error(error_msg)
        return state


# Graph Construction
def create_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow.
    
    Returns:
        Configured StateGraph for CV analysis pipeline
    """
    logger.info("Building LangGraph workflow...")
    
    # Log environment configuration
    _log_environment_config()
    
    # Create workflow graph
    workflow = StateGraph(AnalysisState)
    
    # Add nodes for each agent
    workflow.add_node("parse_cv", parse_cv)
    workflow.add_node("analyze_skills", analyze_skills)
    workflow.add_node("gather_market_intel", gather_market_intel)
    workflow.add_node("generate_report", generate_report)
    
    # Define execution flow
    workflow.add_edge("parse_cv", "analyze_skills")
    workflow.add_edge("analyze_skills", "gather_market_intel") 
    workflow.add_edge("gather_market_intel", "generate_report")
    workflow.add_edge("generate_report", END)
    
    # Set entry point
    workflow.set_entry_point("parse_cv")
    
    logger.info("LangGraph workflow built successfully")
    return workflow


# Main Execution Function
def run_analysis(cv_text: str, target_role: str) -> AnalysisState:
    """
    Main entry point for CV analysis pipeline.
    
    Args:
        cv_text: Raw CV text content
        target_role: Target job role for analysis
        
    Returns:
        Final analysis state with complete results
    """
    pipeline_start_time = time.time()
    logger.info("Starting CV Analysis Pipeline")
    logger.info(f"   Target Role: {target_role}")
    logger.info(f"   CV Content Length: {len(cv_text)} characters")
    
    try:
        # Create and compile workflow
        workflow = create_workflow()
        app = workflow.compile()
        
        # Initialize state
        initial_state = AnalysisState(
            cv_raw=cv_text,
            target_role=target_role
        )
        
        # Execute pipeline
        logger.info("Executing pipeline...")
        result_dict = app.invoke(initial_state)
        
        # Convert result dict back to AnalysisState object
        result = AnalysisState(**result_dict)
        
        # Log final pipeline status
        pipeline_time = time.time() - pipeline_start_time
        logger.info(f"Pipeline completed in {pipeline_time:.2f}s")
        
        # Log final status
        if result.errors:
            logger.warning(f"Pipeline completed with {len(result.errors)} errors:")
            for error in result.errors:
                logger.warning(f"     - {error}")
        else:
            logger.info("Pipeline completed successfully with no errors")
        
        # Log result summary
        if result.final_report:
            logger.info(f"Final report generated: {len(result.final_report)} characters")
        
        return result
        
    except Exception as e:
        pipeline_time = time.time() - pipeline_start_time
        error_msg = f"Pipeline execution failed after {pipeline_time:.2f}s: {str(e)}"
        logger.error(f"{error_msg}")
        
        # Return error state
        error_state = AnalysisState(
            cv_raw=cv_text,
            target_role=target_role,
            errors=[error_msg]
        )
        return error_state
