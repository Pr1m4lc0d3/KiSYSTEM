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

# PowerShell 7+ only, and this is a correctness gate rather than a style preference. Under Windows
# PowerShell 5.1 this config parsed into an object MISSING its properties: `concepts` came back null
# while the surrounding object stayed truthy, so the audit enforced nothing, silently fell back to
# the default globs, and printed "passed". A guard whose behaviour cannot be verified on an engine
# must refuse to run there rather than report green on it.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host ''
    # ASCII only in this block: it is the one message 5.1 will ever print, and 5.1 mangles UTF-8 dashes.
    Write-Host 'COHERENCE AUDIT NOT RUN - requires PowerShell 7+ (pwsh).' -ForegroundColor Red
    Write-Host ("This is Windows PowerShell {0}." -f $PSVersionTable.PSVersion) -ForegroundColor Yellow
    Write-Host 'Install pwsh, or invoke as:  pwsh -NoProfile -File tools/coherence/run_coherence_audit.ps1'
    Write-Host 'Refusing to print a result this engine cannot be trusted to produce.'
    Write-Host ''
    exit 1
}

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

$config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

# Refuse to run on a config the audit cannot understand. Silently treating an unreadable config as
# "no concepts" is how a guard ends up reporting green while enforcing nothing.
if (-not $config -or -not $config.concepts -or @($config.concepts).Count -eq 0) {
    Write-Host ''
    Write-Host "COHERENCE CONFIG UNUSABLE — no concepts found in $configPath" -ForegroundColor Red
    Write-Host 'Declare at least one concept, or delete the config if this repo genuinely has none.'
    Write-Host ''
    exit 1
}

# Default spread wide on purpose: a missing "file_globs" must not silently narrow the audit to one
# language. Narrow it deliberately in config, never by omission. This set is also reused at the end
# to tell "no source yet" apart from "globs pointed at the wrong stack".
$wideDefaultGlobs = @(
    '*.cs','*.ts','*.tsx','*.js','*.jsx','*.mjs','*.py','*.go','*.rs','*.rb','*.php',
    '*.java','*.kt','*.swift','*.cpp','*.c','*.h','*.hpp',
    '*.xaml','*.html','*.htm','*.css','*.scss','*.vue','*.svelte'
)

$globs = $config.file_globs
if (-not $globs -or @($globs).Count -eq 0) { $globs = $wideDefaultGlobs }

function Get-CandidateFiles {
    param([string[]]$Globs)

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
        foreach ($g in $Globs) { if ($name -like $g) { $hit = $true; break } }
        $hit
    }

    $excluded = $config.exclude_directories
    $files | Where-Object {
        $rel = $_
        -not ($excluded | Where-Object { $rel -like "$_/*" -or $rel -like "*/$_/*" })
    }
}

$candidates = @(Get-CandidateFiles -Globs $globs)
$violations = @()
$debtCount  = 0

# Tallied in the SAME pass that does the checking. An earlier version re-derived "is this concept
# enforced?" a second time with Where-Object after the loop — the coherence guard committing a
# coherence violation, and the two answers disagreed across PowerShell editions, producing a false
# green on 5.1. One question, one answer, counted once.
$enforced = 0
$open     = 0
$frag     = 0

foreach ($concept in $config.concepts) {
    if (-not $concept.canonical_file) { $frag++; continue }        # FRAGMENTED — nothing to enforce yet
    if ($concept.canonical_file -eq 'UNDECIDED') { $open++; continue }  # OPEN — owner not chosen; see design.md
    if (-not $concept.store_patterns -or @($concept.store_patterns).Count -eq 0) { $frag++; continue }
    $enforced++

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

# Zero candidates has TWO very different causes and they must not be conflated:
#   - the repo has no source files yet (greenfield) — legitimate, and blocking every commit until
#     the first file lands would just teach people to bypass the hook;
#   - the globs do not match this repo's stack — the built-then-ignored failure in its purest form,
#     a green guard that inspected nothing.
# Tell them apart by re-scanning with the wide default set. Files found there but not here means
# the config is pointed at the wrong extensions.
if ($candidates.Count -eq 0 -and $enforced -gt 0) {
    # Same function, wider globs — so exclude_directories applies identically and the repo's own
    # tooling cannot masquerade as "source you forgot to configure".
    $anySource = @(Get-CandidateFiles -Globs $wideDefaultGlobs)

    if ($anySource.Count -gt 0) {
        Write-Host ''
        Write-Host 'COHERENCE AUDIT INCONCLUSIVE — it scanned ZERO files, but this repo HAS source.' -ForegroundColor Red
        Write-Host ("Globs tried : {0}" -f ($globs -join ' ')) -ForegroundColor Yellow
        Write-Host ("Found anyway: {0}" -f ((@($anySource) | Select-Object -First 5) -join ', ')) -ForegroundColor Yellow
        Write-Host 'Set "file_globs" in tools/coherence/coherence.config.json to match this stack.'
        Write-Host 'A guard that inspects nothing and prints green is worse than no guard at all.'
        Write-Host ''
        exit 1
    }

    Write-Host ("Coherence audit: no source files yet; {0} concept(s) armed and waiting. Nothing to check." -f $enforced) -ForegroundColor Yellow
    exit 0
}

Write-Host ("Coherence audit passed. Files scanned={0}; concepts enforced={1}; tracked debt={2}; open (undecided)={3}; fragmented (no canonical yet)={4}." -f $candidates.Count, $enforced, $debtCount, $open, $frag) -ForegroundColor Green
exit 0
