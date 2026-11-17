param(
    [Parameter(Mandatory=$true)][string]$Deck,
    [Parameter(Mandatory=$true)][string]$OutDir
)

$src = (Resolve-Path $Deck).Path
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$out = (Resolve-Path $OutDir).Path

$app = New-Object -ComObject PowerPoint.Application
$app.Visible = $true
$pres = $app.Presentations.Open($src, $true, $false, $false)
$pres.Export($out, "PNG", 1280, 720)
$pres.Close()
$app.Quit()
Write-Output "exported to $out"
