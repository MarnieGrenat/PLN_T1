<#
.SYNOPSIS
    Runs the PCI Concursos scraper end to end: setup -> listar -> baixar -> extrair.

.DESCRIPTION
    1. Creates a virtual environment in scraper\.venv (if missing).
    2. Installs requirements.txt and the Playwright Chromium browser.
    3. Runs the three stages of scraper_pci.py in order.

    Output is written to scraper\dados\ (questoes.csv, questoes_completo.csv,
    descartes.csv, provas.csv and pdfs\).

    The "baixar" stage opens a visible browser window. Click the
    "Confirme que e humano" check on each exam page when it appears; the
    script continues by itself. Exams already downloaded are skipped, so the
    script can be re-run safely after an interruption.

    If the check keeps failing in that window, use -Manual: each exam opens in
    your normal default browser, you download the files yourself, and the
    script moves the new PDFs from your Downloads folder (or -Downloads <path>)
    into dados\pdfs\<slug>\.

.EXAMPLE
    .\run_scraper.ps1
.EXAMPLE
    .\run_scraper.ps1 -Limite 5 -SkipInstall
.EXAMPLE
    .\run_scraper.ps1 -Manual -SkipInstall -SkipListar
.EXAMPLE
    .\run_scraper.ps1 -SkipListar -SkipBaixar   # only re-extract from existing PDFs
#>
[CmdletBinding()]
param(
    [int]$AnoMin = 2020,
    [int]$Limite = 0,
    [int]$Espera = 180,
    [switch]$ManterSobrepostas,
    [switch]$ManterSemSecao,
    [switch]$Manual,
    [string]$Downloads,
    [switch]$SkipInstall,
    [switch]$SkipListar,
    [switch]$SkipBaixar,
    [switch]$SkipExtrair
)

$ErrorActionPreference = 'Stop'

# scraper_pci.py uses relative paths (dados/...), so always run from this folder
Push-Location $PSScriptRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'

    function Invoke-Step {
        param([string]$Name, [string]$Exe, [string[]]$Arguments)
        Write-Host ""
        Write-Host "==> $Name" -ForegroundColor Cyan
        & $Exe @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Step '$Name' failed (exit code $LASTEXITCODE)."
        }
    }

    # ---------------------------------------------------------------- setup
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPython)) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            Invoke-Step 'Create virtual environment' 'py' @('-3', '-m', 'venv', '.venv')
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            Invoke-Step 'Create virtual environment' 'python' @('-m', 'venv', '.venv')
        } else {
            throw 'Python 3 not found. Install it from https://www.python.org/ and try again.'
        }
        $SkipInstall = $false   # a fresh venv always needs the dependencies
    }

    if (-not $SkipInstall) {
        Invoke-Step 'Install Python dependencies' $venvPython @('-m', 'pip', 'install', '--upgrade', 'pip', '-q')
        Invoke-Step 'Install requirements.txt' $venvPython @('-m', 'pip', 'install', '-r', 'requirements.txt', '-q')
        Invoke-Step 'Install Playwright Chromium' $venvPython @('-m', 'playwright', 'install', 'chromium')
    }

    # ---------------------------------------------------------------- stages
    $common = @('--ano-min', "$AnoMin")
    if ($ManterSobrepostas) { $common += '--manter-sobrepostas' }
    if ($Limite -gt 0)      { $common += @('--limite', "$Limite") }

    if (-not $SkipListar) {
        Invoke-Step 'listar (exam listings -> dados\provas.csv)' $venvPython @('scraper_pci.py', 'listar', '--ano-min', "$AnoMin")
    }
    if (-not $SkipBaixar) {
        if ($Manual) {
            $manualArgs = @('scraper_pci.py', 'manual') + $common
            if ($Downloads) { $manualArgs += @('--downloads', $Downloads) }
            Invoke-Step 'manual (download each exam in your own browser)' $venvPython $manualArgs
        } else {
            Invoke-Step 'baixar (download exams + answer keys; browser window opens)' $venvPython (@('scraper_pci.py', 'baixar') + $common + @('--espera', "$Espera"))
        }
    }
    if (-not $SkipExtrair) {
        $extrairArgs = @('scraper_pci.py', 'extrair') + $common
        if ($ManterSemSecao) { $extrairArgs += '--manter-sem-secao' }
        Invoke-Step 'extrair (PDFs -> dados\questoes.csv)' $venvPython $extrairArgs
    }

    Write-Host ""
    Write-Host "Done. Results in $(Join-Path $PSScriptRoot 'dados')" -ForegroundColor Green
}
finally {
    Pop-Location
}
