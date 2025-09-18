#!/bin/bash
# Installation script for AI Skill Gap Analyst dependencies

echo "🚀 Installing AI Skill Gap Analyst Dependencies"
echo "================================================"

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python version: $python_version"

# Function to install with uv (preferred)
install_with_uv() {
    echo "📦 Installing with uv (recommended)..."
    
    # Check if uv is installed
    if command -v uv &> /dev/null; then
        echo "✅ uv found, installing core dependencies..."
        uv sync
        
        echo "📋 Installation options:"
        echo "1. Core only (regex mode) - Already installed ✅"
        echo "2. With spaCy support"
        echo "3. With development tools"
        
        read -p "Choose option (1-3): " choice
        
        case $choice in
            2)
                echo "🧠 Installing spaCy support..."
                uv sync --extra spacy
                echo "📥 Downloading spaCy English model..."
                uv run python -m spacy download en_core_web_sm
                echo "✅ spaCy installation complete!"
                ;;
            3)
                echo "🛠️ Installing development tools..."
                uv sync --extra dev --extra test
                echo "✅ Development tools installed!"
                ;;
            *)
                echo "✅ Core installation complete!"
                ;;
        esac
        
        return 0
    else
        echo "❌ uv not found. Install uv first:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
}

# Function to install with pip (fallback)
install_with_pip() {
    echo "📦 Installing with pip (fallback)..."
    
    # Create virtual environment
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    echo "⬆️ Upgrading pip..."
    pip install --upgrade pip
    
    # Install core dependencies
    echo "📥 Installing core dependencies..."
    pip install langgraph langchain-core pydantic typer rich
    
    echo "📋 Installation options:"
    echo "1. Core only (regex mode) - Already installed ✅"
    echo "2. With spaCy support"
    echo "3. With development tools"
    
    read -p "Choose option (1-3): " choice
    
    case $choice in
        2)
            echo "🧠 Installing spaCy support..."
            pip install "spacy>=3.4.0" "numpy>=1.19.0"
            echo "📥 Downloading spaCy English model..."
            python -m spacy download en_core_web_sm
            echo "✅ spaCy installation complete!"
            ;;
        3)
            echo "🛠️ Installing development tools..."
            pip install pytest pytest-asyncio pytest-cov black ruff mypy isort
            echo "✅ Development tools installed!"
            ;;
        *)
            echo "✅ Core installation complete!"
            ;;
    esac
    
    echo "📝 To activate virtual environment in future:"
    echo "   source venv/bin/activate"
}

# Main installation logic
echo "📋 Choose installation method:"
echo "1. uv (recommended)"
echo "2. pip + virtual environment"
echo "3. Check current installation"

read -p "Choose method (1-3): " method

case $method in
    1)
        install_with_uv
        ;;
    2)
        install_with_pip
        ;;
    3)
        echo "🔍 Checking current installation..."
        echo "Core dependencies:"
        python3 -c "
import sys
packages = ['langgraph', 'langchain_core', 'pydantic', 'typer', 'rich']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✅ {pkg}')
    except ImportError:
        print(f'  ❌ {pkg} - missing')

print('\\nOptional dependencies:')
try:
    import spacy
    print(f'  ✅ spacy ({spacy.__version__})')
    try:
        nlp = spacy.load('en_core_web_sm')
        print('  ✅ en_core_web_sm model')
    except OSError:
        print('  ❌ en_core_web_sm model - missing')
except ImportError:
    print('  ❌ spacy - missing')
"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🎉 Installation process complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test the installation:"
echo "   python3 test_cv_parser_simple.py"
echo ""
echo "2. Run the main application:"
echo "   python3 main.py analyze data/sample_cv.txt 'Senior AI Engineer'"
echo ""
echo "3. Enable spaCy mode (if installed):"
echo "   USE_SPACY_PARSER=true python3 main.py analyze data/sample_cv.txt 'Role'"
echo ""
echo "📚 For more information, see README.md"
