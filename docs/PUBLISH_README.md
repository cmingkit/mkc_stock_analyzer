# Stock Analyzer - Report Publishing Guide

This document explains how to publish and share your HTML reports using various methods.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Publishing Methods](#publishing-methods)
   - [Local HTTP Server](#method-1-local-http-server)
   - [ngrok Public Tunnel](#method-2-ngrok-public-tunnel)
   - [GitHub Pages](#method-3-github-pages)
3. [Command Line Integration](#command-line-integration)
4. [Security Considerations](#security-considerations)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Generate and Serve Locally
```bash
# Generate report and serve locally
python src/main.py --mode daily --publish local

# Or use the standalone script
./scripts/serve_reports.sh
```

### Generate and Create Public URL
```bash
# Using ngrok (requires ngrok installation)
python src/main.py --mode daily --publish ngrok

# Or use the standalone script
./scripts/public_reports.sh
```

### Publish to GitHub Pages
```bash
# First time setup
python src/main.py --mode daily --publish github --repo-url git@github.com:username/stock-reports.git

# Subsequent publishes (repo URL remembered)
python src/main.py --mode daily --publish github
```

---

## Publishing Methods

### Method 1: Local HTTP Server

**Best for:** Quick viewing on the same machine or LAN

**Script:** `scripts/serve_reports.sh`

```bash
# Default port 8080
./scripts/serve_reports.sh

# Custom port
./scripts/serve_reports.sh 3000
```

**Features:**
- ✅ No external dependencies
- ✅ Works offline
- ✅ Auto-detects latest report
- ⚠️ Only accessible from local machine or LAN
- ⚠️ Server must stay running

**Access URLs:**
- All reports: `http://localhost:8080`
- Latest report: `http://localhost:8080/report_YYYYMMDD_HHMMSS.html`

---

### Method 2: ngrok Public Tunnel

**Best for:** Temporary public sharing, demos, quick collaboration

**Script:** `scripts/public_reports.sh`

**Prerequisites:**
1. Install ngrok: https://ngrok.com/download
2. Authenticate: `ngrok config add-authtoken YOUR_TOKEN`

```bash
# Default port 8080
./scripts/public_reports.sh

# Custom port
./scripts/public_reports.sh 3000
```

**Features:**
- ✅ Creates public HTTPS URL
- ✅ No firewall configuration needed
- ✅ Great for demos and quick sharing
- ⚠️ URL changes each time (unless you have paid ngrok)
- ⚠️ Requires ngrok account (free tier available)
- ⚠️ Server must stay running

**Output Example:**
```
🌐 Public URL Ready!
============================================

  Public URL:
  https://abc123.ngrok.io

  Latest Report:
  https://abc123.ngrok.io/report_20260302_141121.html

  Local URL:
  http://localhost:8080

  Ngrok Dashboard:
  http://127.0.0.1:4040
```

---

### Method 3: GitHub Pages

**Best for:** Permanent hosting, sharing with team, version history

**Script:** `scripts/publish_to_github.sh`

**Prerequisites:**
1. Git installed and configured
2. GitHub account
3. SSH key or personal access token configured

```bash
# First time - specify repository
./scripts/publish_to_github.sh --repo git@github.com:username/stock-reports.git

# Publish only latest report
./scripts/publish_to_github.sh --latest-only

# Custom commit message
./scripts/publish_to_github.sh --message "Weekly analysis update"

# Dry run (preview changes)
./scripts/publish_to_github.sh --dry-run

# Show help
./scripts/publish_to_github.sh --help
```

**Options:**
| Option | Description |
|--------|-------------|
| `--repo URL` | GitHub repository URL (required first time) |
| `--branch NAME` | Branch to publish to (default: gh-pages) |
| `--message MSG` | Custom commit message |
| `--latest-only` | Only publish latest report as index.html |
| `--dry-run` | Preview without making changes |
| `--help` | Show usage information |

**Features:**
- ✅ Permanent HTTPS URL
- ✅ Version history via Git
- ✅ Custom domain support
- ✅ Auto-generates index page with all reports
- ⚠️ Requires GitHub repository
- ⚠️ Reports are public (unless using private repo + GitHub Enterprise)

**After Publishing:**
1. Go to repository Settings → Pages
2. Select source branch (gh-pages)
3. Access at: `https://username.github.io/repo-name/`

---

## Command Line Integration

All publishing methods are integrated into `main.py`:

```bash
# Local server with auto-browser
python src/main.py --mode daily --publish local

# Local server without opening browser
python src/main.py --mode daily --publish local --no-browser

# Local server on custom port
python src/main.py --mode daily --publish local --publish-port 3000

# ngrok tunnel
python src/main.py --mode daily --publish ngrok

# GitHub Pages (first time)
python src/main.py --mode daily --publish github --repo-url git@github.com:user/repo.git

# GitHub Pages (subsequent)
python src/main.py --mode daily --publish github

# GitHub Pages - latest only
python src/main.py --mode daily --publish github --latest-only
```

### All Publish-Related Options

| Option | Default | Description |
|--------|---------|-------------|
| `--publish` | - | Publishing method (local/ngrok/github) |
| `--publish-port` | 8080 | Port for local/ngrok server |
| `--repo-url` | - | GitHub repository URL |
| `--publish-branch` | gh-pages | GitHub branch to publish to |
| `--latest-only` | false | Only publish latest report |
| `--no-browser` | false | Don't auto-open browser |

---

## Security Considerations

### ⚠️ Sensitive Data Warning

Stock analysis reports may contain:
- Investment recommendations
- Personal watchlists
- API usage patterns
- Analysis algorithms

**Best Practices:**

1. **Local Server (safest)**
   - Only accessible from your machine
   - Use for personal review

2. **ngrok (temporary)**
   - URL is public but temporary
   - Good for demos, disable when done
   - Consider password protection for sensitive reports

3. **GitHub Pages (permanent)**
   - **Use a private repository for sensitive reports**
   - Or sanitize reports before publishing
   - Consider adding password protection via GitHub Pages settings

### Sanitizing Reports

Before publishing publicly, consider removing:
- Personal stock positions
- Specific investment amounts
- Custom algorithm parameters
- Internal notes

You can create a sanitized version:
```bash
# Copy and edit HTML to remove sensitive info
cp reports/html/latest.html reports/html/latest_public.html
# Edit the file, then publish
```

### Access Control

For GitHub Pages with access control:
1. Use a private repository
2. Enable GitHub Pages for the repository
3. Only repository members can access

---

## Troubleshooting

### Local Server Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8080

# Use different port
./scripts/serve_reports.sh 3000
```

**No reports found:**
```bash
# Run analyzer first
python src/main.py --mode daily

# Check reports directory
ls -la reports/html/
```

### ngrok Issues

**ngrok not found:**
```bash
# Install ngrok
brew install ngrok  # macOS
# Or download from https://ngrok.com/download
```

**Not authenticated:**
```bash
# Get token from https://dashboard.ngrok.com
ngrok config add-authtoken YOUR_TOKEN
```

**Tunnel fails to start:**
```bash
# Check ngrok status
ngrok config check

# Kill existing ngrok processes
pkill -x ngrok
```

### GitHub Pages Issues

**Permission denied:**
```bash
# Check SSH key
ssh -T git@github.com

# Or use HTTPS with token
git remote set-url origin https://TOKEN@github.com/user/repo.git
```

**Branch not found:**
```bash
# The script creates gh-pages automatically
# First run requires --repo-url
./scripts/publish_to_github.sh --repo git@github.com:user/repo.git
```

**GitHub Pages not loading:**
1. Check repository Settings → Pages
2. Ensure source branch is `gh-pages`
3. Wait a few minutes for deployment
4. Check Actions tab for build errors

---

## Examples

### Daily Workflow

```bash
# Morning analysis with local viewing
python src/main.py --mode daily --publish local

# Share with team via GitHub
python src/main.py --mode daily --publish github
```

### Demo / Presentation

```bash
# Create public URL for demo
./scripts/public_reports.sh
# Share the ngrok URL with audience
```

### Automated Publishing

Add to crontab for daily publishing:
```bash
# Daily analysis and GitHub publish at 9 AM
0 9 * * * cd /path/to/stock_analyzer && python src/main.py --mode daily --publish github --no-telegram
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/serve_reports.sh` | Local HTTP server |
| `scripts/public_reports.sh` | ngrok public tunnel |
| `scripts/publish_to_github.sh` | GitHub Pages publisher |
| `src/utils/publisher.py` | Python publisher module |
| `src/main.py` | Main entry with --publish option |
| `docs/PUBLISH_README.md` | This documentation |

---

## Support

For issues or feature requests, please check:
1. This documentation
2. Project README.md
3. Open an issue in the project repository
