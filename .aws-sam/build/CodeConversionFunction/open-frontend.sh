#!/bin/bash

# Simple script to open frontend - just like localhost:8000/docs experience
# Usage: ./open-frontend.sh

echo "🌐 Opening Code Conversion Interface..."

# Get API URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name codeconversion-server \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null)

if [ -n "$API_URL" ]; then
    echo "✅ Found API URL: $API_URL"
    
    # First try to open /docs (FastAPI Swagger UI)
    echo "🔍 Checking if FastAPI docs are available..."
    
    if command -v curl &> /dev/null; then
        DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs" 2>/dev/null)
        
        if [ "$DOCS_STATUS" -eq 200 ]; then
            echo "🎉 FastAPI docs available! Opening Swagger UI..."
            
            if command -v open &> /dev/null; then
                open "$API_URL/docs"
            else
                echo "📋 Open this URL in your browser for full API docs:"
                echo "$API_URL/docs"
            fi
            
            echo ""
            echo "💡 You can test all endpoints directly in the Swagger UI!"
            echo "   Just like localhost:8000/docs but on AWS! 🚀"
            exit 0
        fi
    fi
    
    echo "📱 FastAPI docs not available, opening custom frontend..."
    
    # Fallback to custom frontend with auto-configured API URL
    if command -v open &> /dev/null; then
        # macOS
        open "file://$(pwd)/frontend-example.html?api=$API_URL"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "file://$(pwd)/frontend-example.html?api=$API_URL"
    else
        echo "📋 Open this URL in your browser:"
        echo "file://$(pwd)/frontend-example.html?api=$API_URL"
    fi
    
    echo ""
    echo "🎯 Quick test URLs:"
    echo "   Health: $API_URL/health"
    echo "   Docs:   $API_URL/docs"
    echo "   API:    $API_URL"
    
else
    echo "❌ Could not get API URL. Make sure your stack is deployed:"
    echo "   ./deploy-aws.sh deploy"
    echo ""
    echo "🔧 For local development:"
    echo "   docker-compose up"
    echo "   open http://localhost:8000/docs"
fi
