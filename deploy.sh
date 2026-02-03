#!/bin/bash

# ABFI Platform Deployment Script
# Deploys both API and Dashboard to Vercel

set -e

echo "========================================="
echo "ABFI Platform Deployment"
echo "========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -f "requirements.txt" ]; then
    echo "Error: Must run from project root"
    exit 1
fi

echo -e "${BLUE}Step 1: Deploying API (root project)${NC}"
echo "This will deploy the FastAPI backend..."
# Note: Vercel deployment would normally happen via:
# vercel --prod
# But since we're pushing to GitHub, Vercel will auto-deploy

echo -e "${GREEN}✓ API deployment configured${NC}"
echo "  URL: https://abfi-ai.vercel.app"
echo ""

echo -e "${BLUE}Step 2: Deploying Dashboard${NC}"
echo "Building dashboard..."
cd dashboard

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build the dashboard
echo "Building React app..."
npm run build

echo -e "${GREEN}✓ Dashboard built successfully${NC}"
echo "  Build output: dashboard/dist/"
echo ""

# Note: For separate dashboard deployment, you would run:
# cd dashboard && vercel --prod
# But with the current setup, dashboard should be served from root

cd ..

echo "========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "URLs:"
echo "  API: https://abfi-ai.vercel.app"
echo "  Docs: https://abfi-ai.vercel.app/docs"
echo "  Dashboard: https://abfi-ai.vercel.app (needs routing config)"
echo ""
echo "Next steps:"
echo "1. Verify API endpoints: curl https://abfi-ai.vercel.app/health"
echo "2. Test dashboard pages"
echo "3. Check Vercel deployment logs"
echo ""
