#!/bin/bash
# Script to push Scholar Query Splitter to GitHub

echo "Scholar Query Splitter - GitHub Push Script"
echo "=========================================="
echo ""
echo "This script will help you push the project to GitHub."
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git branch -m main
fi

# Add all files
echo "Adding files to git..."
git add .

# Create initial commit
echo "Creating initial commit..."
git commit -m "Initial commit: Scholar Query Splitter

A modular Python tool for splitting large Google Scholar queries into manageable subqueries using semantic keyword and entity extraction from OpenAlex metadata.

Features:
- OpenAlex metadata downloader using REST API
- KeyBERT keyword extraction
- spaCy named entity recognition
- Intelligent query generation with temporal splitting
- Google Scholar hit counting
- Progress tracking and comprehensive logging
- Results analysis and CSV export"

echo ""
echo "Now you need to:"
echo "1. Create a new repository on GitHub (https://github.com/new)"
echo "2. Name it: scholar-query-splitter"
echo "3. Don't initialize with README, .gitignore or license"
echo "4. After creating, run these commands:"
echo ""
echo "git remote add origin https://github.com/YOUR_USERNAME/scholar-query-splitter.git"
echo "git push -u origin main"
echo ""
echo "Replace YOUR_USERNAME with your GitHub username."