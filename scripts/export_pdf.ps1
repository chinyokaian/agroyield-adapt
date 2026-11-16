$ErrorActionPreference = "Continue"
$src = (Resolve-Path "FINISHED\Proposal_AGROYIELD-ADAPT_v2.docx").Path
$dst = Join-Path (Get-Location) "docs\render\proposal_v2.pdf"
$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0; $word.AutomationSecurity = 3
$doc = $word.Documents.Open($src, $false, $false, $false)
Write-Output "opened writable pages=$($doc.ComputeStatistics(2))"
$doc.ExportAsFixedFormat($dst, 17, $false)
Write-Output "export called"
Start-Sleep -Seconds 3
if (Test-Path $dst) { Write-Output "pdf exists size=$((Get-Item $dst).Length)" } else { Write-Output "pdf MISSING" }
$doc.Close($false); $word.Quit(); Write-Output "done"
