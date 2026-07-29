<#
.SYNOPSIS
    Coherence audit — "one question, one answer."

.DESCRIPTION
    For each concept declared in coherence.config.json that has a CANONICAL accessor, this fails if any
    source file derives that concept itself (matches a store_pattern) without being on the concept's
    allow-list.

    This dimension is ORTHOGONAL to anti-bloat. Anti-bloat asks "is this unit simple?"; coherence asks
    "does the system have ONE answer?" A codebase can pass every size/cohesion/dead-code check while N
    small, clean, single-responsibility functions independently derive the same concept from different
    stores and silently drift. That is exactly what happened to the agent roster (see CONCEPT-INDEX.md):
    eight answerers, four stores, and a Chairman that concluded an installed agent did not exist.

    Model consumers make this worse: code consumers fail loudly (schema mismatch throws), but an LLM
    reading a stale surface fails PLAUSIBLY — it reasons impeccably from bad data and proposes something
    reasonable-sounding. That is why the roster bug presented as "the Chairman is being difficult".

.PARAMETER Staged
    Only audit files staged for commit (used by the pre-commit hook).
#>
[CmdletBinding()]
param(
    [switch]$Staged
)

$ErrorActionPreference = 'Stop'

# Resolve the repo from the SCRIPT's location, not the caller's working directory — the hook and a
# human at a prompt invoke this from different places.
$repoRoot = (git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) { $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
$repoRoot = $repoRoot.Trim()

$configPath = Join-Path $repoRoot 'tools/coherence/coherence.config.json'

if (-not (Test-Path $configPath)) {
    Write-Host "Coherence audit: no config at $configPath — skipping." -ForegroundColor Yellow
    exit 0
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json

# Default spread wide on purpose: a missing "file_globs" must not silently narrow the audit to one
# language. Narrow it deliberately in config, never by omission.
$globs = $config.file_globs
if (-not $globs -or $globs.Count -eq 0) {
    $globs = @(
        '*.cs','*.ts','*.tsx','*.js','*.jsx','*.mjs','*.py','*.go','*.rs','*.rb','*.php',
        '*.java','*.kt','*.swift','*.cpp','*.c','*.h','*.hpp',
        '*.xaml','*.html','*.htm','*.css','*.scss','*.vue','*.svelte'
    )
}

function Get-CandidateFiles {
    if ($Staged) {
        $files = @(git -C $repoRoot diff --cached --name-only --diff-filter=ACMR)
    }
    else {
        # Tracked AND untracked-but-not-ignored. On a young repo everything is still untracked;
        # scanning only tracked files would pass a repo whose every file is a violation.
        $files  = @(git -C $repoRoot ls-files)
        $files += @(git -C $repoRoot ls-files --others --exclude-standard)
    }

    $files = $files | Sort-Object -Unique | Where-Object {
        $name = Split-Path $_ -Leaf
        $hit = $false
        foreach ($g in $globs) { if ($name -like $g) { $hit = $true; break } }
        $hit
    }

    $excluded = $config.exclude_directories
    $files | Where-Object {
        $rel = $_
        -not ($excluded | Where-Object { $rel -like "$_/*" -or $rel -like "*/$_/*" })
    }
}

$candidates = @(Get-CandidateFiles)
$violations = @()
$debtCount  = 0

foreach ($concept in $config.concepts) {
    if (-not $concept.canonical_file) { continue }                 # FRAGMENTED — nothing to enforce yet
    if ($concept.canonical_file -eq 'UNDECIDED') { continue }      # OPEN — owner not chosen yet; see design.md
    if (-not $concept.store_patterns -or $concept.store_patterns.Count -eq 0) { continue }

    # Allow-list keys are repo-relative, forward-slashed.
    $allowed = @{}
    if ($concept.allowed) {
        foreach ($p in $concept.allowed.PSObject.Properties) {
            $allowed[$p.Name] = $p.Value
            if ($p.Value -like 'DEBT*') { $debtCount++ }
        }
    }

    foreach ($rel in $candidates) {
        $full = Join-Path $repoRoot $rel
        if (-not (Test-Path $full)) { continue }
        $text = Get-Content $full -Raw -ErrorAction SilentlyContinue
        if (-not $text) { continue }

        foreach ($pattern in $concept.store_patterns) {
            if ($text -match $pattern) {
                if (-not $allowed.ContainsKey($rel)) {
                    $violations += [pscustomobject]@{
                        Concept   = $concept.id
                        Question  = $concept.question
                        Canonical = $concept.canonical_symbol
                        File      = $rel
                        Pattern   = $pattern
                    }
                }
                break
            }
        }
    }
}

if ($violations.Count -gt 0) {
    Write-Host ''
    Write-Host 'COHERENCE VIOLATION — one question, one answer.' -ForegroundColor Red
    Write-Host ''
    foreach ($v in $violations) {
        Write-Host ("  [{0}] {1}" -f $v.Concept, $v.File) -ForegroundColor Red
        Write-Host ("      question : {0}" -f $v.Question)
        Write-Host ("      canonical: {0}" -f $v.Canonical)
        Write-Host ("      matched  : {0}" -f $v.Pattern)
        Write-Host ''
    }
    Write-Host 'This file derives the concept itself instead of calling the canonical accessor.' -ForegroundColor Yellow
    Write-Host 'Independently re-deriving one concept from a primary store is how surfaces drift apart —'
    Write-Host 'and when an AI reads those surfaces, it fails PLAUSIBLY rather than loudly.'
    Write-Host ''
    Write-Host 'Fix by calling the canonical accessor. If this genuinely answers a DIFFERENT question,'
    Write-Host "add it to the concept's `"allowed`" map in tools/coherence/coherence.config.json WITH A REASON."
    Write-Host ''
    exit 1
}

$enforced = @($config.concepts | Where-Object { $_.canonical_file -and $_.canonical_file -ne 'UNDECIDED' -and $_.store_patterns.Count -gt 0 }).Count
$open     = @($config.concepts | Where-Object { $_.canonical_file -eq 'UNDECIDED' }).Count
$frag     = @($config.concepts | Where-Object { -not $_.canonical_file }).Count

# Zero candidates means the globs do not match this repo. Reporting "passed" here would be the
# built-then-ignored failure in its purest form: a green guard that inspected nothing.
if ($candidates.Count -eq 0 -and $enforced -gt 0) {
    Write-Host ''
    Write-Host 'COHERENCE AUDIT INCONCLUSIVE — it scanned ZERO files.' -ForegroundColor Red
    Write-Host ("Globs tried: {0}" -f ($globs -join ' ')) -ForegroundColor Yellow
    Write-Host 'Set "file_globs" in tools/coherence/coherence.config.json to match this stack.'
    Write-Host 'A guard that inspects nothing and prints green is worse than no guard at all.'
    Write-Host ''
    exit 1
}

Write-Host ("Coherence audit passed. Files scanned={0}; concepts enforced={1}; tracked debt={2}; open (undecided)={3}; fragmented (no canonical yet)={4}." -f $candidates.Count, $enforced, $debtCount, $open, $frag) -ForegroundColor Green
exit 0
