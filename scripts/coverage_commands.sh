#!/bin/bash
# ZeroWasteAI API - Coverage Analysis Scripts
# Quick commands for different types of coverage analysis

echo "📊 ZeroWasteAI API - Coverage Analysis Commands"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run coverage command
run_coverage() {
    local test_type="$1"
    local description="$2"
    local command="$3"
    
    echo -e "${BLUE}📊 Running $description...${NC}"
    echo "Command: $command"
    echo "----------------------------------------"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $description completed successfully${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
    fi
    echo ""
}

# Check if pytest and coverage are available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 not found. Please install Python 3.${NC}"
    exit 1
fi

echo "🔍 Checking dependencies..."
python3 -c "import pytest, coverage" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Installing missing dependencies...${NC}"
    pip3 install pytest pytest-cov coverage
}

echo -e "${GREEN}✅ Dependencies available${NC}"
echo ""

# Menu system
while true; do
    echo -e "${BLUE}Choose coverage analysis type:${NC}"
    echo "1. 🧪 Unit Tests Coverage"
    echo "2. 🔧 Functional Tests Coverage" 
    echo "3. 🔗 Integration Tests Coverage"
    echo "4. 🚀 Production Validation Coverage"
    echo "5. ⚡ Performance Tests Coverage"
    echo "6. 📊 Complete Coverage (All Tests)"
    echo "7. 🎯 Quick Coverage Summary"
    echo "8. 📈 Coverage Report (HTML)"
    echo "9. 🔄 Run All Coverage Types"
    echo "10. 🚪 Exit"
    echo ""
    
    read -p "Enter your choice (1-10): " choice
    echo ""
    
    case $choice in
        1)
            run_coverage "unit" "Unit Tests Coverage" "python3 -m pytest test/unit/ --cov=src --cov-report=term-missing --cov-branch -v"
            ;;
        2)
            run_coverage "functional" "Functional Tests Coverage" "python3 -m pytest test/functional/ --cov=src --cov-report=term-missing --cov-branch -v"
            ;;
        3)
            run_coverage "integration" "Integration Tests Coverage" "python3 -m pytest test/integration/ --cov=src --cov-report=term-missing --cov-branch -v"
            ;;
        4)
            run_coverage "production" "Production Validation Coverage" "python3 -m pytest test/production_validation/ --cov=src --cov-report=term-missing --cov-branch -v"
            ;;
        5)
            run_coverage "performance" "Performance Tests Coverage" "python3 -m pytest test/performance/ --cov=src --cov-report=term-missing --cov-branch -v"
            ;;
        6)
            run_coverage "complete" "Complete Coverage Analysis" "python3 -m pytest test/ --cov=src --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-report=json:coverage.json --cov-report=term-missing --cov-branch --cov-fail-under=80 -v"
            ;;
        7)
            echo -e "${BLUE}📊 Quick Coverage Summary${NC}"
            echo "----------------------------------------"
            python3 -m pytest test/ --cov=src --cov-report=term --cov-branch --quiet
            ;;
        8)
            echo -e "${BLUE}📈 Generating HTML Coverage Report${NC}"
            echo "----------------------------------------"
            python3 -m pytest test/ --cov=src --cov-report=html:htmlcov --cov-branch --quiet
            echo -e "${GREEN}✅ HTML report generated: htmlcov/index.html${NC}"
            echo "To view the report, open: file://$(pwd)/htmlcov/index.html"
            ;;
        9)
            echo -e "${YELLOW}🔄 Running ALL coverage analysis types...${NC}"
            echo ""
            
            run_coverage "unit" "Unit Tests Coverage" "python3 -m pytest test/unit/ --cov=src --cov-report=html:htmlcov/unit --cov-branch"
            run_coverage "functional" "Functional Tests Coverage" "python3 -m pytest test/functional/ --cov=src --cov-report=html:htmlcov/functional --cov-branch"
            run_coverage "integration" "Integration Tests Coverage" "python3 -m pytest test/integration/ --cov=src --cov-report=html:htmlcov/integration --cov-branch"
            run_coverage "production" "Production Validation Coverage" "python3 -m pytest test/production_validation/ --cov=src --cov-report=html:htmlcov/production --cov-branch"
            run_coverage "performance" "Performance Tests Coverage" "python3 -m pytest test/performance/ --cov=src --cov-report=html:htmlcov/performance --cov-branch"
            run_coverage "complete" "Complete Coverage Analysis" "python3 -m pytest test/ --cov=src --cov-report=html:htmlcov/complete --cov-report=xml:coverage.xml --cov-report=json:coverage.json --cov-branch"
            
            echo -e "${GREEN}🎉 All coverage analysis completed!${NC}"
            echo -e "${BLUE}📁 Coverage reports available in:${NC}"
            echo "   • htmlcov/complete/index.html (Complete coverage)"
            echo "   • htmlcov/unit/index.html (Unit tests)"
            echo "   • htmlcov/functional/index.html (Functional tests)"
            echo "   • htmlcov/integration/index.html (Integration tests)"
            echo "   • htmlcov/production/index.html (Production tests)"
            echo "   • htmlcov/performance/index.html (Performance tests)"
            echo "   • coverage.xml (XML format)"
            echo "   • coverage.json (JSON format)"
            ;;
        10)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid choice. Please enter 1-10.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    echo ""
done