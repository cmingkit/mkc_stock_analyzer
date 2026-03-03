#!/bin/bash
#
# publish_to_github.sh - Publish HTML reports to GitHub Pages
#
# Usage:
#   ./scripts/publish_to_github.sh [options]
#
# Options:
#   --repo URL       GitHub repository URL (required for first run)
#   --branch NAME    Branch to publish to (default: gh-pages)
#   --message MSG    Commit message (default: auto-generated)
#   --latest-only    Only publish the latest report
#   --dry-run        Show what would be done without making changes
#   --help           Show this help message
#
# Prerequisites:
#   - Git installed and configured
#   - GitHub account with write access to the repository
#   - SSH key or token configured for GitHub access
#
# Examples:
#   ./scripts/publish_to_github.sh --repo git@github.com:user/stock-reports.git
#   ./scripts/publish_to_github.sh --latest-only
#   ./scripts/publish_to_github.sh --dry-run
#

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="${PROJECT_ROOT}/reports/html"
PUBLISH_DIR="/tmp/stock_analyzer_gh_pages"
DEFAULT_BRANCH="gh-pages"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
REPO_URL=""
BRANCH="$DEFAULT_BRANCH"
COMMIT_MESSAGE=""
LATEST_ONLY=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_URL="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --message)
            COMMIT_MESSAGE="$2"
            shift 2
            ;;
        --latest-only)
            LATEST_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information."
            exit 1
            ;;
    esac
done

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}   Stock Analyzer - GitHub Pages Publisher${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git found"

# Check reports directory
if [ ! -d "$REPORTS_DIR" ]; then
    echo -e "${RED}Error: Reports directory not found: ${REPORTS_DIR}${NC}"
    exit 1
fi

# Count reports
REPORT_COUNT=$(find "$REPORTS_DIR" -name "*.html" -type f | wc -l | tr -d ' ')
if [ "$REPORT_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No HTML reports found to publish.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Found ${REPORT_COUNT} HTML report(s)"

# Get latest report
LATEST_REPORT=$(ls -t "${REPORTS_DIR}"/*.html 2>/dev/null | head -1)
if [ -z "$LATEST_REPORT" ]; then
    echo -e "${RED}Error: Could not find latest report.${NC}"
    exit 1
fi
LATEST_NAME=$(basename "$LATEST_REPORT")
echo -e "  ${GREEN}✓${NC} Latest: ${LATEST_NAME}"

# Check or get repository URL
if [ -d "$PUBLISH_DIR/.git" ]; then
    # Existing repo
    EXISTING_REPO=$(cd "$PUBLISH_DIR" && git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$EXISTING_REPO" ] && [ -z "$REPO_URL" ]; then
        REPO_URL="$EXISTING_REPO"
        echo -e "  ${GREEN}✓${NC} Using existing repo: ${REPO_URL}"
    fi
fi

if [ -z "$REPO_URL" ]; then
    echo -e "${RED}Error: No repository URL specified.${NC}"
    echo -e "${YELLOW}Run with --repo <url> to specify the repository.${NC}"
    echo -e "${YELLOW}Example: --repo git@github.com:user/stock-reports.git${NC}"
    exit 1
fi

# Generate commit message
if [ -z "$COMMIT_MESSAGE" ]; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    COMMIT_MESSAGE="Update stock analysis report - ${TIMESTAMP}"
fi

echo ""

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}=== DRY RUN MODE ===${NC}"
    echo -e "Would perform the following actions:"
    echo ""
    echo -e "  Repository: ${CYAN}${REPO_URL}${NC}"
    echo -e "  Branch: ${CYAN}${BRANCH}${NC}"
    echo -e "  Commit: ${CYAN}${COMMIT_MESSAGE}${NC}"
    echo -e "  Latest only: ${CYAN}${LATEST_ONLY}${NC}"
    echo ""
    
    if [ "$LATEST_ONLY" = true ]; then
        echo -e "  Files to publish:"
        echo -e "    ${GREEN}${LATEST_NAME}${NC}"
        echo -e "    ${GREEN}index.html${NC} (auto-generated)"
    else
        echo -e "  Files to publish:"
        find "$REPORTS_DIR" -name "*.html" -type f -exec basename {} \; | \
            xargs -I {} echo -e "    ${GREEN}{}${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Dry run complete. No changes made.${NC}"
    exit 0
fi

# Prepare publish directory
echo -e "${BLUE}Preparing publish directory...${NC}"

if [ -d "$PUBLISH_DIR" ]; then
    # Update existing repo
    cd "$PUBLISH_DIR"
    echo -e "  ${GREEN}✓${NC} Fetching latest from ${BRANCH}..."
    git fetch origin "$BRANCH" 2>/dev/null || true
    git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH"
    git pull origin "$BRANCH" 2>/dev/null || true
else
    # Clone or create new repo
    echo -e "  ${GREEN}✓${NC} Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$PUBLISH_DIR" 2>/dev/null || {
        # Branch doesn't exist, create orphan branch
        mkdir -p "$PUBLISH_DIR"
        cd "$PUBLISH_DIR"
        git init
        git remote add origin "$REPO_URL"
        git checkout --orphan "$BRANCH"
        git rm -rf . 2>/dev/null || true
    }
fi

cd "$PUBLISH_DIR"

# Copy reports
echo -e "${BLUE}Copying reports...${NC}"

if [ "$LATEST_ONLY" = true ]; then
    cp "$LATEST_REPORT" "$PUBLISH_DIR/index.html"
    echo -e "  ${GREEN}✓${NC} Copied: index.html (from ${LATEST_NAME})"
else
    # Copy all reports
    cp "${REPORTS_DIR}"/*.html "$PUBLISH_DIR/" 2>/dev/null || true
    COPIED_COUNT=$(find "$PUBLISH_DIR" -name "*.html" -type f | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✓${NC} Copied ${COPIED_COUNT} report(s)"
    
    # Create index page with links
    cat > "$PUBLISH_DIR/index.html" << 'INDEXEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Analyzer Reports</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            background: white;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        a {
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }
        a:hover {
            text-decoration: underline;
        }
        .date {
            color: #666;
            font-size: 0.9em;
        }
        .latest {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
        }
    </style>
</head>
<body>
    <h1>📈 Stock Analyzer Reports</h1>
    <ul>
INDEXEOF

    # Add links to reports
    for report in $(ls -t "$PUBLISH_DIR"/*.html 2>/dev/null | grep -v index.html); do
        name=$(basename "$report")
        # Extract date from filename if possible
        date_str=$(echo "$name" | grep -oE '[0-9]{8}_[0-9]{6}' | sed 's/_/ /' || echo "")
        if [ -n "$date_str" ]; then
            formatted_date=$(date -j -f "%Y%m%d %H%M%S" "$date_str" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "$date_str")
            is_first=$(ls -t "$PUBLISH_DIR"/*.html 2>/dev/null | grep -v index.html | head -1)
            if [ "$report" = "$is_first" ]; then
                echo "        <li class=\"latest\">🌟 <a href=\"$name\">$name</a> <span class=\"date\">($formatted_date)</span> <strong>(Latest)</strong></li>" >> "$PUBLISH_DIR/index.html"
            else
                echo "        <li><a href=\"$name\">$name</a> <span class=\"date\">($formatted_date)</span></li>" >> "$PUBLISH_DIR/index.html"
            fi
        else
            echo "        <li><a href=\"$name\">$name</a></li>" >> "$PUBLISH_DIR/index.html"
        fi
    done

    cat >> "$PUBLISH_DIR/index.html" << 'INDEXEOF2'
    </ul>
    <p style="color: #999; font-size: 0.8em; text-align: center; margin-top: 40px;">
        Generated by Stock Analyzer
    </p>
</body>
</html>
INDEXEOF2

    echo -e "  ${GREEN}✓${NC} Created index.html"
fi

# Commit and push
echo -e "${BLUE}Committing changes...${NC}"

git add -A
git commit -m "$COMMIT_MESSAGE" --allow-empty
echo -e "  ${GREEN}✓${NC} Committed: ${COMMIT_MESSAGE}"

echo -e "${BLUE}Pushing to GitHub...${NC}"
git push -u origin "$BRANCH" --force
echo -e "  ${GREEN}✓${NC} Pushed to ${BRANCH}"

# Extract GitHub Pages URL
GITHUB_USER=$(echo "$REPO_URL" | sed -E 's|.*[:/]([^/]+)/[^/]+\.git|\1|')
GITHUB_REPO=$(echo "$REPO_URL" | sed -E 's|.*[:/][^/]+/([^/]+)\.git|\1|')

if [ "$BRANCH" = "gh-pages" ]; then
    PAGES_URL="https://${GITHUB_USER}.github.io/${GITHUB_REPO}/"
else
    PAGES_URL="https://${GITHUB_USER}.github.io/${GITHUB_REPO}/"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   ✅ Published Successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  ${CYAN}GitHub Pages URL:${NC}"
echo -e "  ${BLUE}${PAGES_URL}${NC}"
echo ""
echo -e "  ${CYAN}Repository:${NC}"
echo -e "  ${BLUE}https://github.com/${GITHUB_USER}/${GITHUB_REPO}${NC}"
echo ""
echo -e "${YELLOW}Note: It may take a few minutes for GitHub Pages to update.${NC}"
echo -e "${YELLOW}Enable GitHub Pages in repository settings if not already enabled.${NC}"
echo ""
