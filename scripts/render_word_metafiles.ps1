$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$report=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../submission/BAO_CAO_NHOM_1.docx'))
$dest=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../outputs/word_pages'))
New-Item -ItemType Directory -Force $dest | Out-Null
$word=New-Object -ComObject Word.Application
$count=$word.Documents.Count
$doc=$null
try {
    $word.DisplayAlerts=0
    $doc=$word.Documents.Open($report,$false,$true,$false)
    $doc.ActiveWindow.View.Type=3
    $doc.Repaginate()
    $n=$doc.ComputeStatistics(2)
    $pageInfo=@()
    for($i=1;$i -le $n;$i++) {
        $start=$doc.GoTo(1,1,$i).Start
        $end=if($i -lt $n){$doc.GoTo(1,1,($i+1)).Start}else{$doc.Content.End}
        $range=$doc.Range($start,$end)
        $pageInfo += [PSCustomObject]@{page=$i;text=$range.Text}
        $bytes=$doc.ActiveWindow.Panes.Item(1).Pages.Item($i).EnhMetaFileBits
        $stream=New-Object IO.MemoryStream(,$bytes)
        $meta=[Drawing.Image]::FromStream($stream)
        $bitmap=New-Object Drawing.Bitmap(1786,2526)
        $graphics=[Drawing.Graphics]::FromImage($bitmap)
        $graphics.Clear([Drawing.Color]::White)
        $graphics.DrawImage($meta,0,0,1786,2526)
        $bitmap.Save((Join-Path $dest ('page-{0:d2}.png' -f $i)),[Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose();$bitmap.Dispose();$meta.Dispose();$stream.Dispose()
        Write-Output "Rendered page $i/$n"
    }
    $pageInfo | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $dest 'pages.json') -Encoding utf8
} finally {
    if($null -ne $doc){$doc.Close(0)}
    if($count -eq 0){$word.Quit()}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
