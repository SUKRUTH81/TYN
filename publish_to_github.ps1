$ErrorActionPreference = 'Stop'

# Run this script from the extracted TYN project root.
$repo = 'SUKRUTH81/jira-release-evidence-agent'
$description = 'AI-powered Jira Release Evidence Agent using Python, Gemini, tool calling, and deterministic evidence validation.'

if (-not (Test-Path 'README.md') -or -not (Test-Path 'release_agent')) {
    throw 'Run this script from the TYN project root (the folder containing README.md and release_agent/).'
}
if (Test-Path '.env') {
    throw 'A populated .env file exists. Remove it before publishing; never commit credentials.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is not installed or not available on PATH.'
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is not installed. Install it, then run: gh auth login'
}

Write-Host 'Checking GitHub CLI authentication...'
gh auth status
$login = gh api user --jq '.login'
if ($login -ne 'SUKRUTH81') {
    throw "GitHub CLI is authenticated as '$login', not SUKRUTH81. Run 'gh auth login' with the intended account."
}

# Use the GitHub-provided noreply address if local Git identity is not configured.
if (-not (git config user.name)) { git config user.name 'K SUKRUTH' }
if (-not (git config user.email)) {
    $userId = gh api user --jq '.id'
    git config user.email "$userId+$login@users.noreply.github.com"
}

Write-Host 'Running project tests...'
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.11 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Test suite failed; nothing was published.' }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Test suite failed; nothing was published.' }
} else {
    throw 'Python 3.11+ is required to run the test suite before publishing.'
}

if (-not (Test-Path '.git')) {
    git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init failed.' }
} else {
    $currentRemote = git remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0 -and $currentRemote -notmatch 'github\.com:SUKRUTH81/jira-release-evidence-agent\.git|github\.com/SUKRUTH81/jira-release-evidence-agent\.git') {
        throw "An origin remote already exists ($currentRemote). Refusing to push to an unexpected repository."
    }
}

# Fail closed if a local environment file or recognizable API key is staged.
git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
$staged = @(git diff --cached --name-only)
if ($staged -contains '.env' -or ($staged | Where-Object { $_ -match '(^|/)\.env($|\.)' })) {
    throw 'A .env file is staged. Remove it and try again.'
}
$secretMatch = git grep --cached -I -n -E '(gsk_[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|ATATT[A-Za-z0-9_-]{20,})' -- .
if ($LASTEXITCODE -eq 0) {
    throw "Possible credential pattern found in staged content:`n$secretMatch"
} elseif ($LASTEXITCODE -gt 1) {
    throw 'Secret scan could not be completed safely.'
}

if (-not (git rev-parse --verify HEAD 2>$null)) {
    git commit -m 'Initial release: Jira AI Release Evidence Agent'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }
} elseif (-not (git diff --cached --quiet)) {
    git commit -m 'Add Jira release evidence agent source and run history'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }
}

# Do not overwrite an existing remote repository.
$existingRepo = gh repo view $repo --json name --jq '.name' 2>$null
if ($LASTEXITCODE -eq 0 -and $existingRepo) {
    throw "The repository $repo already exists. Refusing to overwrite it."
}

Write-Host "Creating public repository $repo and pushing main..."
gh repo create $repo --public --description $description --source . --remote origin --push
if ($LASTEXITCODE -ne 0) { throw 'Repository creation or push failed. Review the GitHub CLI output.' }

Write-Host ''
Write-Host 'Published successfully:' -ForegroundColor Green
Write-Host 'https://github.com/SUKRUTH81/jira-release-evidence-agent'
Write-Host 'Historical runs are preserved with their original PARTIAL/FAILED/OFFLINE statuses.'
Write-Host 'No completed live Jira assessment is claimed by this package.'
