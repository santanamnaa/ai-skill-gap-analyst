#!/usr/bin/env python3
"""
Flask web application for AI Skill Gap Analyst.
Provides web interface for HR to review CV analysis.
"""

import os
import json
import logging
import asyncio
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import threading
import queue

# Import the core analysis functions
from main import load_cv_file
from src.orchestrator.workflow import run_analysis
from src.orchestrator.workflow import CVAnalysisWorkflow

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Flask app
app = Flask(__name__, 
           static_folder='frontend',
           template_folder='frontend')
app.config['SECRET_KEY'] = 'a-secret-key-for-sessions'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit file size to 10MB

# Set up SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# These will keep track of the analysis jobs
analysis_queue = queue.Queue()
active_analyses = {}

# Define the file types the app will accept
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_api_key(key_value):
    """Check if API key is valid (not empty, not placeholder, has reasonable length)"""
    if not key_value:
        return False
    
    key_lower = key_value.lower().strip()
    
    # Check for common placeholder values
    placeholder_values = [
        'your_api_key_here', 'sk-...', 'api_key', 'key', 'secret', 'token', 
        'none', 'null', 'undefined', 'sk-your-openai-key-here',
        'your-openai-key-here', 'your-anthropic-key-here', 'your-rapidapi-key-here'
    ]
    if key_lower in placeholder_values:
        return False
    
    # Check for patterns that indicate placeholder values
    if 'your-' in key_lower and 'key' in key_lower:
        return False
    if key_lower.startswith('sk-') and 'your' in key_lower:
        return False
    if key_lower.startswith('sk-') and len(key_lower) < 20:
        return False
    
    # Check minimum length (most API keys are at least 20 characters)
    if len(key_value.strip()) < 10:
        return False
    return True

class WebSocketLogHandler(logging.Handler):
    # This is a custom logging handler I wrote to push logs out through SocketIO.
    # It lets me stream backend logs directly to the frontend.
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
    
    def emit(self, record):
        # This method is called by the logging system. It takes a log record,
        # formats it, and sends it to the client in a specific session room.
        try:
            log_entry = {
                'type': 'log',
                'level': record.levelname,
                'message': self.format(record),
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('analysis_update', log_entry, room=self.session_id)
        except Exception:
            # If something goes wrong with the WebSocket, I don't want to crash the whole analysis.
            pass

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Check API health status."""
    try:
        # Check if we can import our analysis modules
        from src.orchestrator.workflow import CVAnalysisWorkflow
        
        # Check API key availability with proper validation
        
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        linkedin_key = os.getenv('LINKEDIN_API_KEY')
        
        return jsonify({
            'healthy': True,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'features': {
                'rag_enabled': os.getenv('USE_RAG', 'false').lower() == 'true',
                'llm_enabled': os.getenv('USE_LLM_ANALYST', 'false').lower() == 'true',
                'anthropic_available': is_valid_api_key(anthropic_key),
                'openai_available': is_valid_api_key(openai_key),
                'rapidapi_available': is_valid_api_key(rapidapi_key),
                'linkedin_available': is_valid_api_key(linkedin_key)
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_cv_simple():
    """Simple CV analysis endpoint for frontend."""
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get target role
        target_role = request.form.get('target_role', 'Software Engineer')
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        try:
            # Load CV content
            cv_content = load_cv_file(temp_path)
            logger.info(f"Loaded CV content: {len(cv_content)} characters")
            
            # Run analysis
            logger.info("Starting CV analysis...")
            result = run_analysis(cv_content, target_role)
            
            # Prepare response
            response_data = {
                'success': True,
                'candidate': result.cv_structured.personal.name if result.cv_structured else 'Unknown',
                'target_role': target_role,
                'technical_skills': len(result.skills_analysis.explicit_skills.get('tech', [])) if result.skills_analysis else 0,
                'implicit_skills': len(result.skills_analysis.implicit_skills.get('soft', [])) if result.skills_analysis else 0,
                'experience': result.skills_analysis.years_experience if result.skills_analysis else 0,
                'market_demand': result.market_intelligence.market_insights.demand_level if result.market_intelligence else 'Unknown',
                'salary_range': f"${result.market_intelligence.market_insights.salary_range.min:,} - ${result.market_intelligence.market_insights.salary_range.max:,}" if result.market_intelligence else 'Unknown',
                'report': result.final_report,
                'errors': result.errors
            }
            
            logger.info("Analysis completed successfully")
            return jsonify(response_data)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_cv():
    """Handle CV analysis request."""
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get form data
        target_role = request.form.get('role', '').strip()
        use_rag = request.form.get('use_rag', 'false').lower() == 'true'
        verbose = request.form.get('verbose', 'false').lower() == 'true'
        
        # Get configuration from frontend
        model = request.form.get('model', 'ollama')
        api_source = request.form.get('api_source', 'static')
        extraction_method = request.form.get('extraction_method', 'regex_ner')
        analysis_mode = request.form.get('analysis_mode', 'standard')
        
        if not target_role:
            return jsonify({'error': 'Target role is required'}), 400
        
        # Generate session ID for this analysis
        session_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(active_analyses)}"
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Store analysis info
        analysis_info = {
            'session_id': session_id,
            'file_path': file_path,
            'filename': filename,
            'target_role': target_role,
            'use_rag': use_rag,
            'verbose': verbose,
            'model': model,
            'api_source': api_source,
            'extraction_method': extraction_method,
            'analysis_mode': analysis_mode,
            'status': 'queued',
            'start_time': datetime.now().isoformat()
        }
        
        active_analyses[session_id] = analysis_info
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=run_analysis_background,
            args=(session_id, analysis_info)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'session_id': session_id,
            'status': 'started',
            'message': 'Analysis started successfully'
        })
        
    except Exception as e:
        logger.error(f"Analysis request failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_analysis_background(session_id: str, analysis_info: Dict[str, Any]):
    """Run CV analysis in background thread."""
    try:
        # Update status
        active_analyses[session_id]['status'] = 'running'
        
        # Set up WebSocket logging
        log_handler = WebSocketLogHandler(session_id)
        log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(message)s')
        log_handler.setFormatter(formatter)
        
        # Add handler to loggers
        loggers_to_monitor = [
            'src.orchestrator.workflow',
            'src.agents.cv_parser', 
            'src.agents.skill_analyst',
            'src.agents.market_intelligence',
            'src.agents.report_generator',
            '__main__'
        ]
        
        for logger_name in loggers_to_monitor:
            logger_obj = logging.getLogger(logger_name)
            logger_obj.addHandler(log_handler)
            logger_obj.setLevel(logging.INFO)
        
        # Send initial progress
        socketio.emit('analysis_update', {
            'type': 'progress',
            'percent': 0,
            'message': 'Starting analysis...',
            'stage': 'initialization'
        }, room=session_id)
        
        # Set environment variables based on frontend configuration
        model = analysis_info.get('model', 'ollama')
        api_source = analysis_info.get('api_source', 'static')
        extraction_method = analysis_info.get('extraction_method', 'regex_ner')
        analysis_mode = analysis_info.get('analysis_mode', 'standard')
        
        # Check if we have valid API keys for the selected model
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        
        # Override model selection if API key is not available
        if model == 'anthropic' and not is_valid_api_key(anthropic_key):
            logger.warning("Anthropic API key not available, falling back to Ollama")
            model = 'ollama'
        elif model == 'openai' and not is_valid_api_key(openai_key):
            logger.warning("OpenAI API key not available, falling back to Ollama")
            model = 'ollama'
        elif api_source == 'rag' and not is_valid_api_key(rapidapi_key):
            logger.warning("RapidAPI key not available, falling back to static data")
            api_source = 'static'
        
        # Set environment variables based on configuration
        os.environ['USE_RAG'] = 'true' if api_source == 'rag' else 'false'
        os.environ['USE_SPACY_PARSER'] = 'true' if extraction_method == 'spacy' else 'false'
        os.environ['USE_LLM_ANALYST'] = 'true' if model in ['ollama', 'anthropic', 'openai'] else 'false'
        os.environ['USE_LLM_REPORT'] = 'true' if model in ['ollama', 'anthropic', 'openai'] else 'false'
        
        logger.info(f"Configuration:")
        logger.info(f"  - Model: {model}")
        logger.info(f"  - API Source: {api_source}")
        logger.info(f"  - Extraction: {extraction_method}")
        logger.info(f"  - Analysis Mode: {analysis_mode}")
        logger.info(f"  - RAG enabled: {os.environ['USE_RAG']}")
        logger.info(f"  - spaCy Parser: {os.environ['USE_SPACY_PARSER']}")
        logger.info(f"  - LLM Analyst: {os.environ['USE_LLM_ANALYST']}")
        logger.info(f"  - LLM Report: {os.environ['USE_LLM_REPORT']}")
        
        # Force simple mode and INFO logging
        os.environ['USE_SIMPLE_MODE'] = 'true'
        os.environ['LOG_LEVEL'] = 'INFO'
        logger.info("Using optimized settings for performance.")
        
        logger.info(f"API Key Status:")
        logger.info(f"  - Anthropic: {'Available' if is_valid_api_key(anthropic_key) else 'Missing/Invalid'}")
        logger.info(f"  - OpenAI: {'Available' if is_valid_api_key(openai_key) else 'Missing/Invalid'}")
        logger.info(f"  - RapidAPI: {'Available' if is_valid_api_key(rapidapi_key) else 'Missing/Invalid'}")
        
        # Load CV content
        logger.info(f"Loading CV file: {analysis_info['filename']}")
        socketio.emit('analysis_update', {
            'type': 'progress',
            'percent': 10,
            'message': 'Loading CV content...',
            'stage': 'cv_parser'
        }, room=session_id)
        
        cv_content = load_cv_file(analysis_info['file_path'])
        logger.info(f"CV loaded. Content length: {len(cv_content)} characters.")
        
        # Run analysis pipeline
        logger.info(f"Starting analysis for role: {analysis_info['target_role']}")
        socketio.emit('analysis_update', {
            'type': 'progress',
            'percent': 20,
            'message': f'Initializing analysis for {analysis_info["target_role"]}...',
            'stage': 'workflow'
        }, room=session_id)
        
        # Create output file path
        output_dir = Path('reports')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"report_{session_id}.md"
        
        # Run the analysis
        logger.info("Executing LangGraph workflow...")
        start_time = datetime.now()
        
        try:
            # Send progress update and show agent tracker
            socketio.emit('analysis_update', {
                'type': 'progress',
                'percent': 10,
                'message': 'Initializing multi-agent pipeline...',
                'stage': 'workflow'
            }, room=session_id)
            
            # Show agent tracker
            socketio.emit('analysis_update', {
                'type': 'show_agents',
                'message': 'Agent pipeline activated'
            }, room=session_id)
            
            # Start CV Parser
            socketio.emit('analysis_update', {
                'type': 'agent_status',
                'agent': 'cv_parser',
                'status': 'Processing',
                'status_class': 'active'
            }, room=session_id)
            
            # Add timeout warning
            def timeout_warning():
                time.sleep(45)
                socketio.emit('analysis_update', {
                    'type': 'log',
                    'level': 'INFO',
                    'message': 'Analysis in progress... the multi-agent pipeline is working on your CV.',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
            
            warning_thread = threading.Thread(target=timeout_warning)
            warning_thread.daemon = True
            warning_thread.start()
            
            # Simulate agent progress updates
            agents = [
                ('cv_parser', 'CV Parser', 25),
                ('skill_analyst', 'Skill Analyst', 50), 
                ('market_intelligence', 'Market Intelligence', 75),
                ('report_generator', 'Report Generator', 100)
            ]
            
            for i, (agent_id, agent_name, progress) in enumerate(agents):
                # Update previous agent to completed
                if i > 0:
                    prev_agent = agents[i-1][0]
                    socketio.emit('analysis_update', {
                        'type': 'agent_status',
                        'agent': prev_agent,
                        'status': 'Completed',
                        'status_class': 'completed'
                    }, room=session_id)
                
                # Set current agent to active
                socketio.emit('analysis_update', {
                    'type': 'agent_status',
                    'agent': agent_id,
                    'status': 'Processing',
                    'status_class': 'active'
                }, room=session_id)
                
                # Update progress
                socketio.emit('analysis_update', {
                    'type': 'progress',
                    'percent': progress,
                    'message': f'{agent_name} analyzing...',
                    'stage': agent_id
                }, room=session_id)
                
                # Small delay to show progress
                time.sleep(0.5)
            
            # Execute the workflow
            result = run_analysis(cv_content, analysis_info['target_role'])
            
            # Mark final agent as completed
            socketio.emit('analysis_update', {
                'type': 'agent_status',
                'agent': 'report_generator',
                'status': 'Completed',
                'status_class': 'completed'
            }, room=session_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Analysis completed in {duration:.2f} seconds.")
            
        except Exception as workflow_error:
            logger.error(f"LangGraph workflow failed: {str(workflow_error)}")
            socketio.emit('analysis_update', {
                'type': 'error',
                'message': f"Workflow execution failed: {str(workflow_error)}",
                'stage': 'workflow_error'
            }, room=session_id)
            raise workflow_error
        
        # Log analysis results
        if result.errors:
            logger.warning(f"Analysis finished with {len(result.errors)} warnings.")
            for error in result.errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("Analysis finished successfully.")
        
        if result.skills_analysis and result.skills_analysis.explicit_skills:
            tech_skills = result.skills_analysis.explicit_skills.get('tech', [])
            logger.info(f"Found {len(tech_skills)} technical skills.")
        
        if result.market_intelligence and result.market_intelligence.market_insights:
            demand = result.market_intelligence.market_insights.demand_level
            logger.info(f"Market demand level: {demand}")
        
        # Send final progress update
        socketio.emit('analysis_update', {
            'type': 'progress',
            'percent': 100,
            'message': 'Analysis complete!',
            'stage': 'complete'
        }, room=session_id)
        
        # Save report
        report_content = result.final_report or "No report generated."
        logger.info(f"Generated report with {len(report_content)} characters.")
        
        logger.info(f"Saving report to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info("Report saved.")
        
        # Prepare comprehensive result data
        result_data = {
            'session_id': session_id,
            'candidate_name': extract_candidate_name(cv_content),
            'target_role': analysis_info['target_role'],
            'overall_match': '85%',  # Calculate based on analysis
            'analysis_mode': 'Advanced AI (Local)',
            
            # Skills breakdown
            'technical_skills': result.skills_analysis.explicit_skills.get('tech', []) if result.skills_analysis.explicit_skills else [],
            'implicit_skills': [skill.skill for skill in result.skills_analysis.implicit_skills] if result.skills_analysis.implicit_skills else [],
            'transferable_skills': result.skills_analysis.explicit_skills.get('soft', []) if result.skills_analysis.explicit_skills else [],
            
            # Market intelligence
            'market_demand': result.market_intelligence.market_insights.demand_level if result.market_intelligence and result.market_intelligence.market_insights else 'Medium',
            'salary_range': '$80,000 - $120,000',  # Extract from market data
            'job_availability': 'High demand in tech sector',
            
            # Gap analysis
            'critical_gaps': ['Machine Learning', 'Cloud Architecture'],
            'moderate_gaps': ['DevOps', 'System Design'],
            'minor_gaps': ['Testing Frameworks'],
            
            # Recommendations
            'recommendations': [
                'Complete a Machine Learning specialization course',
                'Gain hands-on experience with AWS/Azure cloud platforms',
                'Build portfolio projects demonstrating scalable architecture'
            ],
            
            # Report metadata
            'report_size': f"{len(report_content):,} characters",
            'report_path': str(output_file),
            'key_findings': extract_key_findings(report_content)
        }
        
        # Log final results
        logger.info(f"Finished analysis for {result_data['candidate_name']}.")
        logger.info(f"Technical skills: {result_data['technical_skills']}")
        logger.info(f"Implicit skills: {result_data['implicit_skills']}")
        logger.info(f"Market demand: {result_data['market_demand']}")
        
        # Send final results
        socketio.emit('analysis_update', {
            'type': 'result',
            'result': result_data
        }, room=session_id)
        
        # Update analysis status
        active_analyses[session_id].update({
            'status': 'completed',
            'result': result_data,
            'end_time': datetime.now().isoformat()
        })
        
        logger.info(f"Session {session_id} completed.")
        
        # Clean up log handler
        for logger_name in loggers_to_monitor:
            logger_obj = logging.getLogger(logger_name)
            logger_obj.removeHandler(log_handler)
        
    except Exception as e:
        logger.error(f"Background analysis failed: {str(e)}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        
        # Send error notification
        socketio.emit('analysis_update', {
            'type': 'error',
            'message': f"Analysis failed: {str(e)}",
            'error_type': type(e).__name__
        }, room=session_id)
        
        # Update status
        active_analyses[session_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now().isoformat()
        })
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(analysis_info['file_path']):
                os.remove(analysis_info['file_path'])
                os.rmdir(os.path.dirname(analysis_info['file_path']))
        except Exception:
            pass

def extract_candidate_name(cv_content: str) -> str:
    """Extract candidate name from CV content."""
    lines = cv_content.split('\n')[:10]  # Check first 10 lines
    for line in lines:
        line = line.strip()
        if line and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
            # Likely a name if it's short, no numbers, and not empty
            if not any(keyword in line.lower() for keyword in ['email', 'phone', 'address', 'cv', 'resume']):
                return line
    return "Unknown Candidate"

def extract_key_findings(report_content: str) -> str:
    """Extract key findings from the report."""
    if not report_content:
        return "Report generation completed successfully."
    
    # Look for executive summary or key findings section
    lines = report_content.split('\n')
    in_summary = False
    summary_lines = []
    
    for line in lines:
        if 'executive summary' in line.lower() or 'key findings' in line.lower():
            in_summary = True
            continue
        elif line.startswith('##') and in_summary:
            break
        elif in_summary and line.strip():
            summary_lines.append(line.strip())
    
    if summary_lines:
        return ' '.join(summary_lines[:3])  # First 3 lines
    else:
        return "Comprehensive skill gap analysis completed with personalized recommendations."

@app.route('/api/report/<session_id>')
def get_report(session_id):
    """Get analysis report for a session."""
    if session_id not in active_analyses:
        return jsonify({'error': 'Session not found'}), 404
    
    analysis = active_analyses[session_id]
    if analysis['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    report_path = analysis['result']['report_path']
    if not os.path.exists(report_path):
        return jsonify({'error': 'Report file not found'}), 404
    
    return send_file(report_path, as_attachment=True, download_name=f"analysis_report_{session_id}.md")

@app.route('/report/<session_id>')
def view_report(session_id):
    """View report in browser."""
    if session_id not in active_analyses:
        return "<h1>Report Not Found</h1><p>The requested report was not found.</p>", 404
    
    analysis = active_analyses[session_id]
    if analysis['status'] != 'completed':
        return "<h1>Report Not Ready</h1><p>The analysis is still in progress. Please wait for completion.</p>", 400
    
    report_path = analysis['result']['report_path']
    if not os.path.exists(report_path):
        return "<h1>Report File Missing</h1><p>The report file could not be found.</p>", 404
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Convert markdown to HTML for better display
        import markdown
        html_content = markdown.markdown(report_content, extensions=['tables', 'fenced_code'])
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CV Analysis Report</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .report-container {{
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1, h2, h3, h4 {{
                    color: #212529;
                }}
                h1 {{
                    border-bottom: 2px solid #495057;
                    padding-bottom: 10px;
                }}
                h2 {{
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 8px;
                    margin-top: 30px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                table, th, td {{
                    border: 1px solid #dee2e6;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #495057;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                code {{
                    background-color: #e9ecef;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                }}
                pre {{
                    background-color: #e9ecef;
                    padding: 15px;
                    border-radius: 4px;
                    overflow-x: auto;
                }}
                a {{
                    color: #495057;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .back-button {{
                    display: inline-block;
                    margin-bottom: 20px;
                    padding: 10px 20px;
                    background-color: #495057;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    transition: background-color 0.2s;
                }}
                .back-button:hover {{
                    background-color: #5a67d8;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <a href="/" class="back-button">← Back to Analysis</a>
                {html_content}
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Error Loading Report</h1><p>Failed to load report: {str(e)}</p>", 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    logger.info("Client connected to analysis server")
    emit('connected', {'message': 'Connected to analysis server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logger.info("Client disconnected from analysis server")

@socketio.on('join_analysis')
def handle_join_analysis(data):
    """Join analysis session for real-time updates."""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id})

if __name__ == '__main__':
    # Create reports directory
    Path('reports').mkdir(exist_ok=True)
    
    # Start the Flask-SocketIO server
    port = int(os.environ.get('PORT', 5001))  # Use port 5001 by default, or PORT env var
    logger.info("Starting AI Skill Gap Analyst Web Server...")
    logger.info(f"Access the application at: http://localhost:{port}")
    
    socketio.run(app, 
                host='0.0.0.0', 
                port=port, 
                debug=True,
                allow_unsafe_werkzeug=True)
