"""
LLM Client for Skill Analysis System

Supports multiple LLM providers: OpenAI, Anthropic, and local models.
Automatically falls back to stub mode if no API keys are provided.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Production LLM client with multiple provider support.
    
    Supports:
    - OpenAI GPT models (gpt-4, gpt-3.5-turbo)
    - Anthropic Claude models (claude-3-sonnet, claude-3-haiku)
    - Local models via Ollama
    - Automatic fallback to stub mode
    """
    
    def __init__(self, provider: str = "auto", model: Optional[str] = None):
        """
        Initialize LLM client with provider selection.
        
        Args:
            provider: "openai", "anthropic", "ollama", or "auto" (default)
            model: Specific model name (optional, uses provider defaults)
        """
        self.provider = provider
        self.model = model
        self.client = None
        self.is_stub_mode = False
        
        # Initialize based on provider preference and available API keys
        if provider == "auto":
            self._auto_detect_provider()
        else:
            self._initialize_provider(provider)
        
        if self.is_stub_mode:
            logger.warning("LLM Client running in stub mode - no API keys found")
        else:
            logger.info(f"LLM Client initialized with {self.provider} provider")
    
    def _auto_detect_provider(self):
        """Auto-detect available LLM provider based on environment variables."""
        if os.getenv("OPENAI_API_KEY"):
            self._initialize_provider("openai")
        elif os.getenv("ANTHROPIC_API_KEY"):
            self._initialize_provider("anthropic")
        elif self._check_ollama_available():
            self._initialize_provider("ollama")
        else:
            self.is_stub_mode = True
            self.provider = "stub"
    
    def _initialize_provider(self, provider: str):
        """Initialize specific LLM provider."""
        try:
            if provider == "openai":
                self._init_openai()
            elif provider == "anthropic":
                self._init_anthropic()
            elif provider == "ollama":
                self._init_ollama()
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as e:
            logger.warning(f"Failed to initialize {provider}: {e}")
            self.is_stub_mode = True
            self.provider = "stub"
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.client = openai.OpenAI(api_key=api_key)
            self.provider = "openai"
            self.model = self.model or "gpt-3.5-turbo"
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: uv add openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
            self.client = anthropic.Anthropic(api_key=api_key)
            self.provider = "anthropic"
            self.model = self.model or "claude-3-haiku-20240307"
            
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: uv add anthropic")
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            import ollama
            self.client = ollama.Client()
            self.provider = "ollama"
            self.model = self.model or "qwen2:1.5b"
            
        except ImportError:
            raise ImportError("Ollama package not installed. Run: uv add ollama")
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str) -> str:
        """Generate response from LLM."""
        if self.is_stub_mode:
            return self._generate_stub_response()
        
        try:
            if self.provider == "openai":
                return self._generate_openai(prompt)
            elif self.provider == "anthropic":
                return self._generate_anthropic(prompt)
            elif self.provider == "ollama":
                return self._generate_ollama(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            logger.warning("Falling back to stub response")
            return self._generate_stub_response()
    
    def _generate_openai(self, prompt: str) -> str:
        """Generate response using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert CV analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _generate_anthropic(self, prompt: str) -> str:
        """Generate response using Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            system="You are an expert CV analyst. Return only valid JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate response using Ollama."""
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert CV analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.3}
        )
        return response['message']['content']
    
    def _generate_stub_response(self) -> str:
        """Generate placeholder response when in stub mode."""
        logger.warning("LLM Client in stub mode - returning placeholder response")
        return '''
        {
            "explicit_skills": {
                "tech": ["python", "javascript"],
                "domain": ["web development"],
                "soft": ["communication"]
            },
            "implicit_skills": [
                {
                    "skill": "problem_solving",
                    "evidence": "Demonstrated through project work",
                    "confidence": 0.7
                }
            ],
            "transferable_skills": [
                {
                    "skill": "analytical_thinking",
                    "from_domain": "general",
                    "relevance": "Applicable to technical roles"
                }
            ],
            "seniority_indicators": {
                "years_exp": 3,
                "leadership": false,
                "architecture": false
            }
        }
        '''
    
    def analyze_skills(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze skills using LLM (stub implementation).
        
        Args:
            cv_data: Structured CV data
            
        Returns:
            Skills analysis results (placeholder)
            
        Raises:
            NotImplementedError: This is a stub implementation
        """
        logger.warning("LLM Skills analysis stub called - no actual LLM integration available")
        raise NotImplementedError(
            "LLM Skills analysis is a stub implementation. "
            "Please implement actual LLM integration or use rule-based analysis."
        )