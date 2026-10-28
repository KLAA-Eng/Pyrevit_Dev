# Review-only rendering of attributed SVG candidates; no production resources change.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase
$reviewCulture = [Globalization.CultureInfo]::InvariantCulture
$reviewBrushes = @{}
function Brush([string]$color) {
    if (-not $reviewBrushes.ContainsKey($color)) {
        $reviewBrushes[$color] = [Windows.Media.BrushConverter]::new().ConvertFromString($color)
    }
    return $reviewBrushes[$color]
}
function Number([string]$value) { return [double]::Parse($value, $reviewCulture) }
function Label([string]$value, [double]$x, [double]$y, [double]$size=12, [string]$color='#E5E4E2') {
    $text = [Windows.Media.FormattedText]::new($value, $reviewCulture,
        [Windows.FlowDirection]::LeftToRight, [Windows.Media.Typeface]::new('Segoe UI'), $size, (Brush $color))
    $reviewContext.DrawText($text, [Windows.Point]::new($x,$y))
}
function SvgIcon([string]$name, [double]$x, [double]$y, [double]$size, [string]$color='#E5E4E2') {
    [xml]$svg = Get-Content -LiteralPath (Join-Path $PSScriptRoot ($name + '.svg')) -Raw
    $pen = [Windows.Media.Pen]::new((Brush $color), 1.5)
    $pen.StartLineCap = $pen.EndLineCap = [Windows.Media.PenLineCap]::Round
    $pen.LineJoin = [Windows.Media.PenLineJoin]::Round
    $reviewContext.PushTransform([Windows.Media.TranslateTransform]::new($x,$y))
    $reviewContext.PushTransform([Windows.Media.ScaleTransform]::new($size/24,$size/24))
    foreach ($element in $svg.DocumentElement.ChildNodes) {
        if ($element.NodeType -ne [Xml.XmlNodeType]::Element) { continue }
        $geometry = switch ($element.LocalName) {
            'path' { [Windows.Media.Geometry]::Parse($element.GetAttribute('d')) }
            'circle' { [Windows.Media.EllipseGeometry]::new([Windows.Point]::new((Number $element.cx),(Number $element.cy)),(Number $element.r),(Number $element.r)) }
            'rect' {
                $radius = if ($element.HasAttribute('rx')) { Number $element.rx } else { 0 }
                [Windows.Media.RectangleGeometry]::new([Windows.Rect]::new((Number $element.x),(Number $element.y),(Number $element.width),(Number $element.height)),$radius,$radius)
            }
            'line' { [Windows.Media.LineGeometry]::new([Windows.Point]::new((Number $element.x1),(Number $element.y1)),[Windows.Point]::new((Number $element.x2),(Number $element.y2))) }
            'polyline' { [Windows.Media.Geometry]::Parse('M' + $element.points) }
            default { throw "Unsupported SVG element: $($element.LocalName)" }
        }
        $fill = if ($element.GetAttribute('fill') -eq 'currentColor') { Brush $color } else { $null }
        $reviewContext.DrawGeometry($fill,$pen,$geometry)
    }
    $reviewContext.Pop()
    $reviewContext.Pop()
}
$reviewCards = @(
    @('Search','search','Current search role'),
    @('Text / filter mode','list-filter','Recall mode toggle candidate'),
    @('Regular expressions','regex','Recall regex mode'),
    @('Clear search','x','Recall clear field'),
    @('Read element parameters','tags','Recall source action'),
    @('Read view filters','eye','Recall source action'),
    @('Filter + element','funnel','Recall source action'),
    @('Paste to picked element','mouse-pointer-2','Recall target action'),
    @('Paste by rectangle','scan','Recall target action'),
    @('Paste to selection','check-check','Recall target action'),
    @('List view','list','Family Studio view mode'),
    @('Grid view','layout-grid','Family Studio view mode'),
    @('Favorite','star','Family Studio favorite action'),
    @('Information','info','Optional message symbol'),
    @('Warning','triangle-alert','Optional message symbol'),
    @('Error / blocking','circle-x','Optional message symbol'),
    @('Success / ready','circle-check','Optional feedback symbol'),
    @('Existing search PNG','search_16px_light.png','Current repository asset'),
    @('Existing information PNG','about_16px_light.png','Current repository asset')
)
$reviewVisual = [Windows.Media.DrawingVisual]::new()
$reviewContext = $reviewVisual.RenderOpen()
$reviewContext.DrawRectangle((Brush '#1A252B'),$null,[Windows.Rect]::new(0,0,1000,760))
Label 'KLCode in-window icon candidates' 16 12 20
Label 'Review only. Outline candidates at 32 and 16 units; no ribbon or production GUI changes.' 16 41 12 '#B5C2BD'
$reviewBorder = [Windows.Media.Pen]::new((Brush '#407058'),1)
for ($index=0; $index -lt $reviewCards.Count; $index++) {
    $card = $reviewCards[$index]
    $x = 16 + ($index % 4)*246
    $y = 80 + [Math]::Floor($index/4)*130
    $reviewContext.DrawRoundedRectangle((Brush '#22303A'),$reviewBorder,[Windows.Rect]::new($x,$y,232,118),8,8)
    Label $card[0] ($x+12) ($y+10) 12
    if ($card[1].EndsWith('.png')) {
        $imagePath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('../../../../../lib/_icons/' + $card[1])))
        $bitmap = [Windows.Media.Imaging.BitmapImage]::new([Uri]::new($imagePath))
        $reviewContext.DrawImage($bitmap,[Windows.Rect]::new($x+16,$y+39,32,32))
        $reviewContext.DrawImage($bitmap,[Windows.Rect]::new($x+70,$y+47,16,16))
    } else {
        SvgIcon $card[1] ($x+16) ($y+39) 32
        SvgIcon $card[1] ($x+70) ($y+47) 16
    }
    Label '32' ($x+24) ($y+75) 10 '#B5C2BD'
    Label '16' ($x+72) ($y+75) 10 '#B5C2BD'
    Label $card[1].Replace('_16px_light.png','') ($x+104) ($y+48) 11
    Label $card[2] ($x+12) ($y+96) 10 '#B5C2BD'
}
Label 'Lucide candidates: stroke 1.5 on a 24-unit grid; source commit and license retained beside this sheet.' 16 739 10 '#B5C2BD'
$reviewContext.Close()
$reviewBitmap = [Windows.Media.Imaging.RenderTargetBitmap]::new(1000,760,96,96,[Windows.Media.PixelFormats]::Pbgra32)
$reviewBitmap.Render($reviewVisual)
$reviewEncoder = [Windows.Media.Imaging.PngBitmapEncoder]::new()
$reviewEncoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($reviewBitmap))
$reviewStream = [IO.File]::Open((Join-Path $PSScriptRoot 'contact-sheet.png'),[IO.FileMode]::Create)
try { $reviewEncoder.Save($reviewStream) } finally { $reviewStream.Dispose() }
Write-Output 'Rendered 17 SVG candidates and 2 existing PNG references.'
