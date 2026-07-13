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

$repoRoot  = (git rev-parse --show-toplevel).Trim()
$configPath = Join-Path $repoRoot 'tools/coherence/coherence.config.json'

if (-not (Test-Path $configPath)) {
    Write-Host "Coherence audit: no config at $configPath — skipping." -ForegroundColor Yellow
    exit 0
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json

function Get-CandidateFiles {
    if ($Staged) {
        $files = git diff --cached --name-only --diff-filter=ACMR |
                 Where-Object { $_ -like '*.cs' }
    }
    else {
        $files = git ls-files '*.cs'
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

$enforced = @($config.concepts | Where-Object { $_.canonical_file -and $_.store_patterns.Count -gt 0 }).Count
$frag     = @($config.concepts | Where-Object { -not $_.canonical_file }).Count

Write-Host ("Coherence audit passed. Concepts enforced={0}; tracked debt={1}; fragmented (no canonical yet)={2}." -f $enforced, $debtCount, $frag) -ForegroundColor Green
exit 0
