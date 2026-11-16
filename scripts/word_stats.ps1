$src = (Resolve-Path "FINISHED\Proposal_AGROYIELD-ADAPT_v2.docx").Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
$doc = $word.Documents.Open($src, $false, $true, $false)
$doc.Fields.Update() | Out-Null
Write-Output "pages=$($doc.ComputeStatistics(2)) words=$($doc.ComputeStatistics(0)) characters=$($doc.ComputeStatistics(3))"
Write-Output "firstCaption=$($doc.Tables.Item(1).Range.Paragraphs.Item(1).Range.Text.Trim())"
$doc.Close($false); $word.Quit()
