param([Parameter(Mandatory=$true)][string]$DocPath)

$src = (Resolve-Path $DocPath).Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($src, $false, $true, $false)
$doc.Fields.Update() | Out-Null
Write-Output "file=$([System.IO.Path]::GetFileName($src))"
Write-Output "pages=$($doc.ComputeStatistics(2)) words=$($doc.ComputeStatistics(0)) characters=$($doc.ComputeStatistics(3))"
$doc.Close($false)
$word.Quit()
