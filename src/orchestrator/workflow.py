"""
LangGraph Workflow Orchestrator for CV Skill Gap Analysis System

This module implements the LangGraph StateGraph for coordinating the multi-agent workflow.
Uses LangGraph's state machine pattern for advanced workflow management.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = None
    END = None
    MemorySaver = None

from ..schemas import AnalysisState, LangGraphState
from ..agents.cv_parser import cv_parser_node
from ..agents.skill_analyst import skill_analyst_node
from ..agents.market_intelligence import market_intelligence_node
from ..agents.report_generator import report_generator_node

logger = logging.getLogger(__name__)


# Shared state management
_shared_analysis_state: Optional[AnalysisState] = None

def _get_analysis_state(state: LangGraphState) -> AnalysisState:
    """Get or create shared analysis state."""
    global _shared_analysis_state
    if _shared_analysis_state is None:
        _shared_analysis_state = AnalysisState(
            cv_raw=state["cv_raw_content"],
            target_role=state["target_role"]
        )
    return _shared_analysis_state

def _update_langgraph_state(state: LangGraphState, analysis_state: AnalysisState, node_name: str) -> LangGraphState:
    """Update LangGraph state from analysis state."""
    state["cv_structured"] = asdict(analysis_state.cv_structured)
    state["skills_analysis"] = asdict(analysis_state.skills_analysis)
    state["market_intelligence"] = asdict(analysis_state.market_intelligence)
    state["final_report"] = analysis_state.final_report
    state["processing_errors"] = analysis_state.errors
    state["processing_log"].append(f"{node_name} completed at {datetime.now().isoformat()}")
    return state

# LangGraph Node Adapters
def cv_parser_langgraph_node(state: LangGraphState) -> LangGraphState:
    """LangGraph adapter for CV parser node."""
    logger.info("Executing CV Parser node")
    
    # Get shared analysis state
    analysis_state = _get_analysis_state(state)
    
    # Run the parser
    result_state = cv_parser_node(analysis_state)
    
    # Update shared state
    global _shared_analysis_state
    _shared_analysis_state = result_state
    
    # Update LangGraph state
    return _update_langgraph_state(state, result_state, "CV Parser")


def skill_analyst_langgraph_node(state: LangGraphState) -> LangGraphState:
    """LangGraph adapter for skill analyst node."""
    logger.info("Executing Skill Analyst node")
    
    # Get shared analysis state
    analysis_state = _get_analysis_state(state)
    
    # Run the analyst
    result_state = skill_analyst_node(analysis_state)
    
    # Update shared state
    global _shared_analysis_state
    _shared_analysis_state = result_state
    
    # Update LangGraph state
    return _update_langgraph_state(state, result_state, "Skill Analyst")


def market_intelligence_langgraph_node(state: LangGraphState) -> LangGraphState:
    """LangGraph adapter for market intelligence node."""
    logger.info("Executing Market Intelligence node")
    
    # Get shared analysis state
    analysis_state = _get_analysis_state(state)
    
    # Run the market intelligence
    result_state = market_intelligence_node(analysis_state)
    
    # Update shared state
    global _shared_analysis_state
    _shared_analysis_state = result_state
    
    # Update LangGraph state
    return _update_langgraph_state(state, result_state, "Market Intelligence")


def report_generator_langgraph_node(state: LangGraphState) -> LangGraphState:
    """LangGraph adapter for report generator node."""
    logger.info("Executing Report Generator node")
    
    # Get shared analysis state
    analysis_state = _get_analysis_state(state)
    
    # Run the report generator
    result_state = report_generator_node(analysis_state)
    
    # Update shared state
    global _shared_analysis_state
    _shared_analysis_state = result_state
    
    # Update LangGraph state
    return _update_langgraph_state(state, result_state, "Report Generator")


class LangGraphWorkflow:
    """
    LangGraph-based workflow orchestrator for CV Skill Gap Analysis.
    
    Uses LangGraph's StateGraph for advanced multi-agent orchestration
    with proper state management and error handling.
    """
    
    def __init__(self):
        """Initialize the LangGraph workflow."""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is not available. Please install it with: "
                "pip install langgraph>=0.0.40"
            )
        
        self.workflow = None
        self.compiled_app = None
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the LangGraph StateGraph."""
        logger.info("Building LangGraph workflow...")
        
        # Create the workflow graph
        workflow = StateGraph(LangGraphState)
        
        # Add nodes (one for each agent)
        workflow.add_node("parse_cv", cv_parser_langgraph_node)
        workflow.add_node("analyze_skills", skill_analyst_langgraph_node) 
        workflow.add_node("gather_market_intel", market_intelligence_langgraph_node)
        workflow.add_node("generate_report", report_generator_langgraph_node)
        
        # Define the execution flow
        workflow.add_edge(START, "parse_cv")
        workflow.add_edge("parse_cv", "analyze_skills")
        workflow.add_edge("analyze_skills", "gather_market_intel") 
        workflow.add_edge("gather_market_intel", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Set entry and exit points
        workflow.set_entry_point("parse_cv")
        workflow.set_finish_point("generate_report")
        
        # Compile the application with memory
        memory = MemorySaver()
        self.compiled_app = workflow.compile(checkpointer=memory)
        
        logger.info("LangGraph workflow built successfully")
    
    def run_analysis(self, cv_text: str, target_role: str) -> AnalysisState:
        """
        Run the complete CV analysis workflow using LangGraph.
        
        Args:
            cv_text: Raw CV text content
            target_role: Target job role for analysis
            
        Returns:
            Final analysis state with results
        """
        logger.info("Starting LangGraph CV analysis workflow")
        
        # Reset shared state for new analysis
        global _shared_analysis_state
        _shared_analysis_state = None
        
        # Initialize LangGraph state
        initial_state: LangGraphState = {
            "cv_raw_content": cv_text,
            "target_role": target_role,
            "cv_structured": {},
            "skills_analysis": {},
            "market_intelligence": {},
            "final_report": "",
            "processing_errors": [],
            "processing_log": [f"Workflow started at {datetime.now().isoformat()}"],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": "cv_analysis_thread"}}
            final_state = self.compiled_app.invoke(initial_state, config=config)
            
            # Convert back to AnalysisState for compatibility
            result_state = AnalysisState(
                cv_raw=final_state["cv_raw_content"],
                target_role=final_state["target_role"],
                final_report=final_state["final_report"],
                errors=final_state["processing_errors"]
            )
            
            logger.info("LangGraph workflow completed successfully")
            return result_state
            
        except Exception as e:
            logger.error(f"LangGraph workflow execution failed: {str(e)}")
            error_state = AnalysisState(
                cv_raw=cv_text,
                target_role=target_role,
                errors=[f"LangGraph workflow error: {str(e)}"]
            )
            return error_state


# Fallback simple orchestrator for compatibility
class SimpleWorkflowOrchestrator:
    """
    Simple fallback orchestrator when LangGraph is not available.
    
    Maintains compatibility with existing code while providing
    a path to migrate to LangGraph.
    """
    
    def __init__(self):
        logger.warning("Using fallback simple orchestrator. Install LangGraph for full functionality.")
    
    def run_analysis(self, cv_text: str, target_role: str) -> AnalysisState:
        """
        Run analysis using simple sequential execution.
        
        Args:
            cv_text: Raw CV text content
            target_role: Target job role for analysis
            
        Returns:
            Final analysis state with results
        """
        logger.info("Starting simple workflow analysis")
        
        # Initialize state
        state = AnalysisState(cv_raw=cv_text, target_role=target_role)
        
        try:
            # Sequential execution
            state = cv_parser_node(state)
            state = skill_analyst_node(state)
            state = market_intelligence_node(state)
            state = report_generator_node(state)
            
            logger.info("Simple workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Simple workflow execution failed: {str(e)}")
            state.add_error(f"Workflow execution error: {str(e)}")
        
        return state


def create_workflow(use_langgraph: bool = True):
    """
    Factory function to create workflow orchestrator.
    
    Args:
        use_langgraph: Whether to use LangGraph implementation (default: True)
        
    Returns:
        Workflow orchestrator instance
    """
    if use_langgraph and LANGGRAPH_AVAILABLE:
        try:
            logger.info("Creating LangGraph workflow orchestrator")
            return LangGraphWorkflow()
        except Exception as e:
            logger.warning(f"Failed to create LangGraph workflow: {str(e)}")
            logger.warning("Falling back to simple orchestrator")
    
    if not LANGGRAPH_AVAILABLE:
        logger.warning(
            "LangGraph not available. Install with: pip install langgraph>=0.0.40"
        )
    
    return SimpleWorkflowOrchestrator()
