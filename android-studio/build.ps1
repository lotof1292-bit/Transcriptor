param(
    [ValidateSet('all','free','premium')]
    [string]$Edition = 'all',
    [string]$AndroidSdk = $env:ANDROID_HOME
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path $PSScriptRoot).Path
if (-not $AndroidSdk) { throw 'Define ANDROID_HOME o pasa -AndroidSdk.' }
$sdkRoot = (Resolve-Path $AndroidSdk).Path
$buildTools = Join-Path $sdkRoot 'build-tools\35.0.0'
$androidJar = Join-Path $sdkRoot 'platforms\android-35\android.jar'
$aapt = Join-Path $buildTools 'aapt.exe'
$d8 = Join-Path $buildTools 'd8.bat'
$zipalign = Join-Path $buildTools 'zipalign.exe'
$apksigner = Join-Path $buildTools 'apksigner.bat'
foreach ($required in @($androidJar,$aapt,$d8,$zipalign,$apksigner)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Falta herramienta: $required" }
}

$workRoot = Join-Path $projectRoot 'build\windows'
$distRoot = Join-Path $projectRoot 'dist'
$resolvedWork = [IO.Path]::GetFullPath($workRoot)
if (-not $resolvedWork.StartsWith($projectRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta de build inválida.' }
if (Test-Path -LiteralPath $workRoot) { Remove-Item -LiteralPath $workRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $workRoot,$distRoot | Out-Null

$sourceArchive = Join-Path $projectRoot 'assets\sources.zip'
if (Test-Path -LiteralPath $sourceArchive) { Remove-Item -LiteralPath $sourceArchive -Force }
$sourceItems = @('src','server','tests','res','assets\index.html','README.md','AndroidManifest.xml','AndroidManifest.free.xml','AndroidManifest.premium.xml','build.sh','build.ps1','package.json') | ForEach-Object { Join-Path $projectRoot $_ }
Compress-Archive -LiteralPath $sourceItems -DestinationPath $sourceArchive -CompressionLevel Optimal

$classes = Join-Path $workRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$javaSources = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'src\mx\transcriptor\studio') -Filter '*.java' | Select-Object -ExpandProperty FullName
& javac -encoding UTF-8 -source 8 -target 8 -classpath $androidJar -d $classes $javaSources
if ($LASTEXITCODE -ne 0) { throw 'Falló javac.' }
$classJar = Join-Path $workRoot 'classes.jar'
Push-Location $classes
try { & jar cf $classJar . } finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw 'Falló jar.' }

$dex = Join-Path $workRoot 'dex'
New-Item -ItemType Directory -Force -Path $dex | Out-Null
& $d8 --lib $androidJar --min-api 26 --output $dex $classJar
if ($LASTEXITCODE -ne 0) { throw 'Falló d8.' }

$signingRoot = Join-Path $projectRoot '.signing'
New-Item -ItemType Directory -Force -Path $signingRoot | Out-Null
$keystore = Join-Path $signingRoot 'transcriptor-development.keystore'
if (-not (Test-Path -LiteralPath $keystore)) {
    & keytool -genkeypair -noprompt -keystore $keystore -storepass android -keypass android -alias transcriptor -dname 'CN=Transcriptor Development,O=Local Development,C=MX' -keyalg RSA -keysize 2048 -validity 3650 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear la firma de desarrollo.' }
}

function Build-Edition([string]$name,[string]$manifestName) {
    $manifest = Join-Path $projectRoot $manifestName
    $editionWork = Join-Path $workRoot $name
    New-Item -ItemType Directory -Force -Path $editionWork | Out-Null
    $workingManifest = Join-Path $editionWork 'AndroidManifest.xml'
    Copy-Item -LiteralPath $manifest -Destination $workingManifest
    $unsigned = Join-Path $workRoot "$name-unsigned.apk"
    $aligned = Join-Path $workRoot "$name-aligned.apk"
    $output = Join-Path $distRoot "Transcriptor-Studio-1.1-$name.apk"
    & $aapt package -f -M $workingManifest -I $androidJar -S (Join-Path $projectRoot 'res') -A (Join-Path $projectRoot 'assets') -F $unsigned
    if ($LASTEXITCODE -ne 0) { throw "Falló aapt para $name." }
    Push-Location $dex
    try { & jar uf $unsigned 'classes.dex' } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "Falló el empaquetado DEX para $name." }
    & $zipalign -f 4 $unsigned $aligned
    if ($LASTEXITCODE -ne 0) { throw "Falló zipalign para $name." }
    & $apksigner sign --ks $keystore --ks-key-alias transcriptor --ks-pass pass:android --key-pass pass:android --out $output $aligned
    if ($LASTEXITCODE -ne 0) { throw "Falló la firma para $name." }
    & $apksigner verify --verbose $output | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "La firma no verificó para $name." }
    Get-Item -LiteralPath $output
}

$outputs = @()
if ($Edition -in @('all','free')) { $outputs += Build-Edition 'free' 'AndroidManifest.free.xml' }
if ($Edition -in @('all','premium')) { $outputs += Build-Edition 'premium' 'AndroidManifest.premium.xml' }
$outputs | Select-Object FullName,Length,LastWriteTime
