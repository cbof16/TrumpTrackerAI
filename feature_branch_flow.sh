#!/bin/bash

# Script to create a new feature branch, commit changes, and push to remote

set -e  # Exit on error

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <feature-name> <commit-message> [push:yes|no]"
    echo "Example: $0 ui-improvements \"Improved responsive design for mobile\" yes"
    exit 1
fi

FEATURE_NAME=$1
COMMIT_MESSAGE=$2
PUSH_CHANGES=${3:-"no"}

# Feature branch name with prefix
BRANCH_NAME="feature/${FEATURE_NAME}"

echo "===== TrumpTracker AI Feature Branch Workflow ====="
echo "Creating feature branch: $BRANCH_NAME"
echo "Commit message: $COMMIT_MESSAGE"
echo "Push changes: $PUSH_CHANGES"
echo "=================================================="

# Create branch
if git rev-parse --verify --quiet "$BRANCH_NAME" >/dev/null; then
    echo "Branch '$BRANCH_NAME' already exists. Switching to it..."
    git checkout "$BRANCH_NAME"
else
    echo "Creating new branch '$BRANCH_NAME'..."
    git checkout -b "$BRANCH_NAME"
fi

# Display current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check if there are changes
if git diff-index --quiet HEAD --; then
    echo "No changes to commit!"
    exit 1
fi

# Add all changes
echo "Adding changes..."
git add .

# Commit changes
echo "Committing changes with message: '$COMMIT_MESSAGE'..."
git commit -m "$COMMIT_MESSAGE"

# Push changes if requested
if [ "$PUSH_CHANGES" = "yes" ]; then
    echo "Pushing changes to origin/$BRANCH_NAME..."
    git push -u origin "$BRANCH_NAME"
fi

echo "===== Feature Branch Workflow Complete ====="
echo "Feature branch: $BRANCH_NAME"
echo "Changes committed with message: $COMMIT_MESSAGE"
if [ "$PUSH_CHANGES" = "yes" ]; then
    echo "Changes pushed to origin"
else
    echo "Changes not pushed. To push changes, run:"
    echo "git push -u origin $BRANCH_NAME"
fi
echo "============================================"
