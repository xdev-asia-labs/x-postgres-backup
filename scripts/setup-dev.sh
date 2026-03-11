#!/bin/bash
# Demo script showing pre-commit hooks in action

set -e

echo "🔧 Setting up development environment..."
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run: make install"
    exit 1
fi

# Check if pre-commit is installed
if [ ! -f ".git/hooks/pre-commit" ]; then
    echo "⚙️  Installing git hooks..."
    make setup-hooks
fi

echo "✅ Git hooks installed!"
echo ""
echo "📝 Hooks configured:"
echo "  • pre-commit: Format code automatically"
echo "  • pre-push: Run fast tests before pushing"
echo ""

# Show current git status
echo "📊 Git status:"
git status -s
echo ""

echo "💡 Try making a commit to see hooks in action:"
echo "   git add ."
echo "   git commit -m 'Your message'"
echo ""
echo "🚀 Before push, tests will run automatically!"
echo "   To skip (not recommended): git push --no-verify"
