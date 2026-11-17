param(
    [Parameter(Mandatory=$true)][string]$DocPath,
    [Parameter(Mandatory=$true)][string]$HeadingFile
)

$src = (Resolve-Path $DocPath).Path
$headings = Get-Content -LiteralPath $HeadingFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($src, $false, $true, $false)

foreach ($h in $headings) {
    $want = $h.Trim()
    $page = 0
    foreach ($p in $doc.Paragraphs) {
        $t = $p.Range.Text
        if ($t) { $t = $t.TrimEnd([char]13, [char]10, [char]7).Trim() }
        if ($t -eq $want) {
            $page = $p.Range.Information(3)   # wdActiveEndPageNumber, last match wins
        }
    }
    Write-Output "$want|$page"
}

$doc.Close($false)
$word.Quit()
