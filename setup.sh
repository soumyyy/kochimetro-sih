#!/bin/bash

echo "🚂 Kochi Metro IBL Planner Setup Script"
echo "========================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo "📦 Setting up backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Backend setup complete"

# Setup Frontend
echo "🎨 Setting up frontend..."
cd ../frontend
npm install
echo "✅ Frontend setup complete"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo ""
echo "Backend:"
echo "  cd backend"
echo "  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "📚 Don't forget to:"
echo "1. Update your Supabase database URL in backend/app/settings.py"
echo "2. Set up your environment variables"
echo "3. Create the database schema (see docs for db.sql)"
echo ""
echo "Happy coding! 🚂✨"
