#!/bin/bash

# Script to manage Git operations for TrumpTracker AI

set -e  # Exit on error

# Color codes for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to display usage information
function show_help {
    echo -e "${BLUE}TrumpTracker AI Git Operations${NC}\n"
    echo -e "Usage: $0 <command> [options]\n"
    echo -e "Available commands:"
    echo -e "  ${GREEN}branch${NC} <branch-name>        Create and switch to a new branch"
    echo -e "  ${GREEN}commit${NC} <message>           Commit changes with the specified message"
    echo -e "  ${GREEN}push${NC} [branch-name]         Push changes to remote (defaults to current branch)"
    echo -e "  ${GREEN}switch${NC} <branch-name>       Switch to an existing branch"
    echo -e "  ${GREEN}merge${NC} <branch-name>        Merge branch into current branch"
    echo -e "  ${GREEN}deploy${NC} <target>            Prepare and deploy to target (render/heroku)"
    echo -e "  ${GREEN}status${NC}                     Show current status\n"
    echo -e "Examples:"
    echo -e "  $0 branch feature/new-ui"
    echo -e "  $0 commit \"Fixed pagination issue\""
    echo -e "  $0 push"
    echo -e "  $0 deploy render"
}

# Function to check if Git is initialized
function check_git {
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}Git repository not found. Initializing new repository...${NC}"
        git init
        echo -e "${GREEN}Git repository initialized!${NC}"
    fi
}

# Function to create and switch to a new branch
function create_branch {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Branch name required${NC}"
        show_help
        exit 1
    fi

    branch_name=$1
    
    # Check if branch already exists
    if git rev-parse --verify --quiet "$branch_name" >/dev/null; then
        echo -e "${YELLOW}Branch '$branch_name' already exists. Switching to it...${NC}"
        git checkout "$branch_name"
    else
        echo -e "${BLUE}Creating new branch '$branch_name'...${NC}"
        git checkout -b "$branch_name"
    fi
    
    echo -e "${GREEN}Now on branch '$branch_name'${NC}"
}

# Function to commit changes
function commit_changes {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Commit message required${NC}"
        show_help
        exit 1
    fi

    message=$1
    current_branch=$(git branch --show-current)
    
    # Check if there are changes to commit
    if git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}No changes to commit on branch '$current_branch'${NC}"
        return
    fi
    
    # Add all changes
    echo -e "${BLUE}Adding changes...${NC}"
    git add .
    
    # Commit with message
    echo -e "${BLUE}Committing changes to branch '$current_branch'...${NC}"
    git commit -m "$message"
    
    echo -e "${GREEN}Changes committed to branch '$current_branch'${NC}"
}

# Function to push changes
function push_changes {
    branch=${1:-$(git branch --show-current)}
    
    # Check if remote exists
    if ! git remote -v | grep -q "origin"; then
        echo -e "${YELLOW}No remote 'origin' found. Please set up a remote:${NC}"
        echo "git remote add origin <your-repository-url>"
        exit 1
    fi
    
    echo -e "${BLUE}Pushing changes to '$branch'...${NC}"
    git push -u origin "$branch"
    
    echo -e "${GREEN}Changes pushed to '$branch'${NC}"
}

# Function to switch to an existing branch
function switch_branch {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Branch name required${NC}"
        show_help
        exit 1
    fi

    branch_name=$1
    
    # Check if branch exists
    if ! git rev-parse --verify --quiet "$branch_name" >/dev/null; then
        echo -e "${RED}Error: Branch '$branch_name' doesn't exist${NC}"
        echo -e "${YELLOW}Available branches:${NC}"
        git branch
        exit 1
    fi
    
    echo -e "${BLUE}Switching to branch '$branch_name'...${NC}"
    git checkout "$branch_name"
    
    echo -e "${GREEN}Now on branch '$branch_name'${NC}"
}

# Function to merge a branch into current branch
function merge_branch {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Branch name required${NC}"
        show_help
        exit 1
    fi

    branch_name=$1
    current_branch=$(git branch --show-current)
    
    # Check if branch exists
    if ! git rev-parse --verify --quiet "$branch_name" >/dev/null; then
        echo -e "${RED}Error: Branch '$branch_name' doesn't exist${NC}"
        echo -e "${YELLOW}Available branches:${NC}"
        git branch
        exit 1
    fi
    
    echo -e "${BLUE}Merging branch '$branch_name' into '$current_branch'...${NC}"
    git merge "$branch_name"
    
    echo -e "${GREEN}Merged '$branch_name' into '$current_branch'${NC}"
}

# Function to prepare and deploy
function deploy {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Deployment target required (render/heroku)${NC}"
        show_help
        exit 1
    fi

    target=$1
    current_branch=$(git branch --show-current)
    
    # Confirm before deploying
    echo -e "${YELLOW}You are about to deploy branch '$current_branch' to $target.${NC}"
    read -p "Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment canceled.${NC}"
        exit 1
    fi
    
    # Run specific deployment steps based on target
    case "$target" in
        render)
            echo -e "${BLUE}Deploying to Render...${NC}"
            # Ensure render.yaml exists
            if [ ! -f "render.yaml" ]; then
                echo -e "${RED}Error: render.yaml not found${NC}"
                exit 1
            fi
            
            # If render CLI is installed, use that, otherwise instruct for manual deployment
            if command -v render &> /dev/null; then
                render deploy
            else
                echo -e "${YELLOW}Render CLI not found. To deploy manually:${NC}"
                echo -e "1. Push your branch to GitHub"
                echo -e "2. Go to the Render dashboard: https://dashboard.render.com/"
                echo -e "3. Connect your repository and deploy"
            fi
            ;;
        heroku)
            echo -e "${BLUE}Deploying to Heroku...${NC}"
            # Check for heroku CLI
            if ! command -v heroku &> /dev/null; then
                echo -e "${RED}Error: Heroku CLI not found${NC}"
                echo -e "${YELLOW}Please install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli${NC}"
                exit 1
            fi
            
            # Deploy to Heroku
            git push heroku "$current_branch":main
            ;;
        *)
            echo -e "${RED}Error: Unknown deployment target '$target'${NC}"
            echo -e "${YELLOW}Supported targets: render, heroku${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}Deployment to $target initiated!${NC}"
}

# Function to show status
function show_status {
    current_branch=$(git branch --show-current)
    
    echo -e "${BLUE}Current branch:${NC} $current_branch"
    echo
    
    echo -e "${BLUE}Modified files:${NC}"
    git status -s
    echo
    
    echo -e "${BLUE}Local branches:${NC}"
    git branch
    echo
    
    echo -e "${BLUE}Last 5 commits:${NC}"
    git log --oneline -5
}

# Main script execution
check_git

# Process command line arguments
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

command=$1
shift

case "$command" in
    branch)
        create_branch "$1"
        ;;
    commit)
        commit_changes "$1"
        ;;
    push)
        push_changes "$1"
        ;;
    switch)
        switch_branch "$1"
        ;;
    merge)
        merge_branch "$1"
        ;;
    deploy)
        deploy "$1"
        ;;
    status)
        show_status
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$command'${NC}"
        show_help
        exit 1
        ;;
esac
