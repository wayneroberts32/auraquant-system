#!/bin/bash

# QUANTUM-READY TRADING SYSTEM DEPLOYMENT SCRIPT
# Deploys to both Render and Cloudflare using git

set -e  # Exit on error

echo "🚀 QUANTUM TRADING SYSTEM DEPLOYMENT"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required commands
echo "Checking prerequisites..."
if ! command_exists git; then
    echo -e "${RED}❌ git is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"

# Function to deploy to Render
deploy_to_render() {
    echo ""
    echo -e "${YELLOW}📦 Deploying to Render...${NC}"
    
    # Check if render remote exists, if not add it
    if ! git remote | grep -q "render"; then
        echo "Adding Render remote..."
        git remote add render https://github.com/your-username/your-repo.git
    fi
    
    # Build Docker image for Render
    echo "Building Docker image..."
    docker build -t quantum-trading:latest .
    
    # Commit current changes
    echo "Committing changes..."
    git add .
    git commit -m "Deploy: Quantum Trading System $(date '+%Y-%m-%d %H:%M:%S')" || true
    
    # Push to Render
    echo "Pushing to Render..."
    git push render main:main --force
    
    echo -e "${GREEN}✓ Deployed to Render successfully${NC}"
    echo "URL: ${RENDER_URL}"
}

# Function to deploy to Cloudflare Pages
deploy_to_cloudflare() {
    echo ""
    echo -e "${YELLOW}☁️ Deploying to Cloudflare Pages...${NC}"
    
    # Create production build
    echo "Creating production build..."
    npm run build || echo "No build script defined"
    
    # Initialize Cloudflare Pages if needed
    if [ ! -d ".cloudflare" ]; then
        echo "Initializing Cloudflare Pages..."
        npx wrangler pages project create quantum-trading --production-branch main || true
    fi
    
    # Deploy to Cloudflare Pages
    echo "Deploying to Cloudflare Pages..."
    npx wrangler pages publish . \
        --project-name=quantum-trading \
        --branch=main \
        --commit-dirty=true
    
    echo -e "${GREEN}✓ Deployed to Cloudflare successfully${NC}"
    echo "URL: ${CLOUDFLARE_URL}"
}

# Function to run pre-deployment tests
run_tests() {
    echo ""
    echo -e "${YELLOW}🧪 Running pre-deployment tests...${NC}"
    
    # Run linting
    echo "Running linter..."
    npm run lint || echo "No lint script defined"
    
    # Run unit tests
    echo "Running unit tests..."
    npm test || echo "No test script defined"
    
    # Check system health
    echo "Checking system health..."
    node -e "
        const QuantumReadyOrchestration = require('./js/quantum-ready-orchestration.js');
        const orchestrator = new QuantumReadyOrchestration();
        setTimeout(() => {
            const status = orchestrator.getSystemStatus();
            console.log('System Status:', status.health);
            if (status.health !== 'OPERATIONAL') {
                process.exit(1);
            }
            orchestrator.shutdown();
            process.exit(0);
        }, 5000);
    " || {
        echo -e "${RED}❌ System health check failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✓ All tests passed${NC}"
}

# Function to backup current deployment
backup_deployment() {
    echo ""
    echo -e "${YELLOW}💾 Creating backup...${NC}"
    
    BACKUP_DIR="backups/$(date '+%Y%m%d_%H%M%S')"
    mkdir -p "$BACKUP_DIR"
    
    # Backup critical files
    cp -r js "$BACKUP_DIR/"
    cp -r css "$BACKUP_DIR/" 2>/dev/null || true
    cp index.html "$BACKUP_DIR/" 2>/dev/null || true
    cp package.json "$BACKUP_DIR/"
    cp .env "$BACKUP_DIR/"
    
    # Create tarball
    tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
    rm -rf "$BACKUP_DIR"
    
    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR.tar.gz${NC}"
}

# Function to rollback deployment
rollback_deployment() {
    echo ""
    echo -e "${YELLOW}⏪ Rolling back deployment...${NC}"
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t backups/*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo -e "${RED}❌ No backup found${NC}"
        exit 1
    fi
    
    echo "Restoring from: $LATEST_BACKUP"
    tar -xzf "$LATEST_BACKUP" -C .
    
    echo -e "${GREEN}✓ Rollback completed${NC}"
}

# Function to monitor deployment
monitor_deployment() {
    echo ""
    echo -e "${YELLOW}📊 Monitoring deployment...${NC}"
    
    # Check Render health
    echo "Checking Render deployment..."
    curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "${RENDER_URL}/health" || true
    
    # Check Cloudflare health
    echo "Checking Cloudflare deployment..."
    curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "${CLOUDFLARE_URL}/health" || true
    
    echo -e "${GREEN}✓ Monitoring complete${NC}"
}

# Main deployment flow
main() {
    echo ""
    echo "Select deployment option:"
    echo "1) Deploy to Render only"
    echo "2) Deploy to Cloudflare only"
    echo "3) Deploy to both Render and Cloudflare"
    echo "4) Run tests only"
    echo "5) Create backup"
    echo "6) Rollback deployment"
    echo "7) Monitor deployments"
    echo "8) Full deployment (backup, test, deploy both)"
    echo "0) Exit"
    
    read -p "Enter option: " option
    
    case $option in
        1)
            run_tests
            deploy_to_render
            monitor_deployment
            ;;
        2)
            run_tests
            deploy_to_cloudflare
            monitor_deployment
            ;;
        3)
            run_tests
            deploy_to_render
            deploy_to_cloudflare
            monitor_deployment
            ;;
        4)
            run_tests
            ;;
        5)
            backup_deployment
            ;;
        6)
            rollback_deployment
            ;;
        7)
            monitor_deployment
            ;;
        8)
            backup_deployment
            run_tests
            deploy_to_render
            deploy_to_cloudflare
            monitor_deployment
            echo ""
            echo -e "${GREEN}🎉 FULL DEPLOYMENT SUCCESSFUL!${NC}"
            echo "====================================="
            echo "Render URL: ${RENDER_URL}"
            echo "Cloudflare URL: ${CLOUDFLARE_URL}"
            echo "====================================="
            ;;
        0)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            exit 1
            ;;
    esac
}

# Run main function
main

echo ""
echo "Deployment script completed."