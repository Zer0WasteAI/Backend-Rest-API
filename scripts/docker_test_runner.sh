#!/bin/bash
"""
🐳 DOCKER + TEST RUNNER - ZeroWasteAI API
Start Docker services and run comprehensive tests
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${CYAN}=====================================================================${NC}"
    echo -e "${CYAN}${BOLD}🐳 DOCKER + TEST RUNNER - ZeroWasteAI API${NC}"
    echo -e "${CYAN}=====================================================================${NC}\n"
}

check_docker() {
    echo -e "${BLUE}🔍 Checking Docker status...${NC}"
    
    # Check if Docker Desktop is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Docker is not running. Please start Docker Desktop first.${NC}"
        echo -e "${YELLOW}On macOS: Open Docker Desktop application${NC}"
        echo -e "${YELLOW}Then run this script again.${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Docker is running${NC}"
        return 0
    fi
}

start_services() {
    echo -e "\n${BLUE}🚀 Starting Docker services...${NC}"
    
    # Stop any existing containers to avoid conflicts
    echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
    docker-compose down --remove-orphans
    
    # Build and start services
    echo -e "${BLUE}🏗️  Building and starting services...${NC}"
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Services started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start services${NC}"
        return 1
    fi
}

wait_for_services() {
    echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
    
    # Wait for MySQL
    echo -e "${BLUE}📊 Waiting for MySQL...${NC}"
    for i in {1..30}; do
        if docker exec mysql_db mysql -u user -puserpass -e "SELECT 1" zwaidb > /dev/null 2>&1; then
            echo -e "${GREEN}✅ MySQL is ready${NC}"
            break
        fi
        echo -e "${YELLOW}   Attempt $i/30 - MySQL not ready yet...${NC}"
        sleep 2
    done
    
    # Wait for Redis
    echo -e "${BLUE}🔴 Waiting for Redis...${NC}"
    for i in {1..15}; do
        if docker exec redis_cache redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Redis is ready${NC}"
            break
        fi
        echo -e "${YELLOW}   Attempt $i/15 - Redis not ready yet...${NC}"
        sleep 1
    done
    
    # Wait for API
    echo -e "${BLUE}🌐 Waiting for API...${NC}"
    for i in {1..20}; do
        if curl -s http://localhost:3000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API is ready${NC}"
            break
        fi
        echo -e "${YELLOW}   Attempt $i/20 - API not ready yet...${NC}"
        sleep 3
    done
}

show_services_status() {
    echo -e "\n${BLUE}📊 Services Status:${NC}"
    docker-compose ps
    
    echo -e "\n${BLUE}📋 Service URLs:${NC}"
    echo -e "${GREEN}🌐 API: http://localhost:3000${NC}"
    echo -e "${GREEN}🔴 Redis: localhost:6379${NC}"
    echo -e "${GREEN}📊 MySQL: localhost:3306${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:3000/apidocs${NC}"
}

run_tests() {
    local test_type=${1:-"all"}
    
    echo -e "\n${CYAN}=====================================================================${NC}"
    echo -e "${CYAN}${BOLD}🧪 RUNNING TESTS${NC}"
    echo -e "${CYAN}=====================================================================${NC}\n"
    
    # Run tests inside the API container or locally
    if docker ps | grep -q "zerowasteai_api"; then
        echo -e "${BLUE}🐳 Running tests inside Docker container...${NC}"
        docker exec -it zerowasteai_api python3 quick_test.py $test_type
    else
        echo -e "${BLUE}💻 Running tests locally...${NC}"
        python3 quick_test.py $test_type
    fi
}

cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    docker-compose down
}

main() {
    print_header
    
    # Check command line arguments
    local command=${1:-"start-and-test"}
    local test_type=${2:-"all"}
    
    case $command in
        "start-and-test")
            if check_docker; then
                start_services
                wait_for_services
                show_services_status
                run_tests $test_type
            fi
            ;;
        "start")
            if check_docker; then
                start_services
                wait_for_services
                show_services_status
            fi
            ;;
        "test")
            run_tests $test_type
            ;;
        "stop")
            cleanup
            ;;
        "restart")
            cleanup
            if check_docker; then
                start_services
                wait_for_services
                show_services_status
            fi
            ;;
        "status")
            show_services_status
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 [start-and-test|start|test|stop|restart|status] [test_type]${NC}"
            echo -e "${YELLOW}Examples:${NC}"
            echo -e "${YELLOW}  $0 start-and-test unit    # Start services and run unit tests${NC}"
            echo -e "${YELLOW}  $0 start                  # Just start services${NC}"
            echo -e "${YELLOW}  $0 test integration       # Run integration tests${NC}"
            echo -e "${YELLOW}  $0 stop                   # Stop all services${NC}"
            echo -e "${YELLOW}  $0 status                 # Show services status${NC}"
            ;;
    esac
}

# Handle Ctrl+C
trap cleanup EXIT

# Run main function
main "$@"
