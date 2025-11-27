#!/bin/bash
#
# Development environment setup script
#

set -e  # Exit on error

echo "🚀 Setting up app-builder development environment..."
echo ""

# Check Python version
echo "📦 Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.10"

if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Error: Python 3.10+ required (found $python_version)"
    exit 1
fi
echo "✅ Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "📦 Activating virtual environment..."
source .venv/bin/activate || .venv/Scripts/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -e .

echo "✅ Dependencies installed"

# Setup PostgreSQL with Docker
echo ""
echo "🗄️  Starting PostgreSQL with Docker..."
if command -v docker &> /dev/null; then
    docker-compose up -d postgres
    echo "✅ PostgreSQL started"
    echo "   Connection: postgresql://langgraph:langgraph_dev_pass@localhost:5432/app_builder"
else
    echo "⚠️  Docker not found - skipping PostgreSQL setup"
    echo "   Please install Docker and run: docker-compose up -d postgres"
fi

# Setup environment file
echo ""
echo "📝 Checking environment configuration..."
if [ ! -f ".env.development" ]; then
    echo "⚠️  .env.development not found"
    echo "   Please create it based on .env.production.example"
else
    echo "✅ .env.development exists"
fi

# Install Playwright
echo ""
echo "🎭 Installing Playwright browsers..."
if command -v npx &> /dev/null; then
    playwright install
    echo "✅ Playwright browsers installed"
else
    echo "⚠️  npm/npx not found - skipping Playwright setup"
    echo "   Install Node.js and run: playwright install"
fi

# Final instructions
echo ""
echo "=" * 80
echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Configure API keys in .env.development"
echo "  2. Run the application:"
echo "     python src/main.py my-project \"Build a chatbot\""
echo ""
echo "Useful commands:"
echo "  - Start PostgreSQL: docker-compose up -d postgres"
echo "  - Stop PostgreSQL: docker-compose down"
echo "  - View checkpoints: python scripts/inspect_checkpoints.py list"
echo "  - Run tests: pytest tests/"
echo ""
echo "=" * 80
