# PhœnixForge 1.8.1 preview: verified official OSS CAD Suite, per-user only.
# The ~603 MB toolchain is downloaded ONLY if the user keeps the NSIS option.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$InstallDir)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$spec = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'osscad-181.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($spec.schema_version -ne 1 -or $spec.component -ne 'osscad' -or
    $spec.version -ne '2026-10-27' -or
    $spec.url -ne 'https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-10-27/oss-cad-suite-windows-x64-20261027.tgz' -or
    $spec.sha256 -ne 'aadcf3ff1b7cc8720509fde6c57ca84249f3beb45ddd14fd492c608241a12bb8' -or
    [long]$spec.bytes -ne 603362463) { throw 'Manifiesto OSS CAD no corresponde al release auditado' }
$root = [System.IO.Path]::GetFullPath($InstallDir)
$integrations = Join-Path $root 'Integrations'
$dest = Join-Path $integrations ([string]$spec.folder)
$receiptName = 'phoenixforge-component.json'
[System.IO.Directory]::CreateDirectory($integrations) | Out-Null

function Check-Installed($folder) {
  $receipt = Join-Path $folder $receiptName
  if (-not (Test-Path -LiteralPath $receipt -PathType Leaf)) { return $false }
  $data = Get-Content -LiteralPath $receipt -Encoding UTF8 -Raw | ConvertFrom-Json
  if ($data.component -ne 'osscad' -or $data.archive_sha256 -ne $spec.sha256 -or
      $data.version -ne $spec.version -or
      $data.relative_path -ne 'runtime/oss-cad-suite/bin/yosys.exe') { return $false }
  $path = Join-Path $folder 'runtime\oss-cad-suite\bin\yosys.exe'
  $loader = Join-Path $folder 'runtime\oss-cad-suite\bin\openFPGALoader.exe'
  if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
      -not (Test-Path -LiteralPath $loader -PathType Leaf)) { return $false }
  if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne
      $data.file_sha256) { return $false }
  if ((Get-FileHash -LiteralPath $loader -Algorithm SHA256).Hash.ToLowerInvariant() -ne
      $data.loader_sha256) { return $false }
  $next = Join-Path $folder 'runtime\oss-cad-suite\bin\nextpnr-generic.exe'
  if (Test-Path -LiteralPath $next -PathType Leaf) {
    if (-not $data.nextpnr_sha256 -or
        (Get-FileHash -LiteralPath $next -Algorithm SHA256).Hash.ToLowerInvariant() -ne
        $data.nextpnr_sha256) { return $false }
  }
  return $true
}
if (Test-Path -LiteralPath $dest) {
  if (-not (Check-Installed $dest)) {
    throw 'Existe instalación diferente o alterada; no se sobrescribe automáticamente'
  }
  Write-Host 'OSS CAD Suite ya está verificado y disponible para PhoenixForge'
  exit 0
}

$stage = Join-Path $integrations ('.pf-osscad-' + [guid]::NewGuid().ToString('N'))
$archive = Join-Path $env:TEMP ('PF-osscad-' + [guid]::NewGuid().ToString('N') + '.tgz')
try {
  Write-Host 'Descargando OSS CAD Suite oficial (~603 MB), sin instalar Quartus...'
  Invoke-WebRequest -Uri ([string]$spec.url) -MaximumRedirection 6 -OutFile $archive
  $length = (Get-Item -LiteralPath $archive).Length
  if ($length -ne [long]$spec.bytes) { throw 'Descarga incompleta: tamaño incorrecto' }
  $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $spec.sha256) { throw 'Checksum SHA-256 inválido: archivo rechazado' }

  $tar = Join-Path $env:WINDIR 'System32\tar.exe'
  if (-not (Test-Path -LiteralPath $tar -PathType Leaf)) {
    throw 'Windows tar.exe no disponible (Windows 10 build 1809+ necesario)'
  }
  # Never extract untrusted paths, absolute paths, traversal, or links.
  $names = @(& $tar -tzf $archive)
  if ($LASTEXITCODE -ne 0 -or $names.Count -lt 20 -or
      $names.Count -gt [int]$spec.max_entries) { throw 'Tarball incompatible o demasiados archivos' }
  foreach ($entry in $names) {
    $name = ([string]$entry).Replace('\', '/')
    if ($name.StartsWith('./')) { $name = $name.Substring(2) }
    $parts = @($name.TrimEnd('/').Split('/') | Where-Object { $_ -ne '' })
    if ($name.StartsWith('/') -or $name.Contains(':') -or
        $name.Contains([char]0) -or $name.Contains('\') -or
        $parts -contains '..' -or $parts -contains '.' -or
        $parts.Count -eq 0 -or $parts[0] -ne 'oss-cad-suite') {
      throw 'Ruta no autorizada en archivo OSS CAD: ' + $name
    }
  }
  # A SHA-256-pinned upstream archive is mandatory; inspect metadata as well.
  $types = @(& $tar -tvzf $archive)
  if ($LASTEXITCODE -ne 0 -or $types.Count -lt 20) {
    throw 'No se pudo comprobar tipo de entradas del tarball'
  }
  foreach ($line in $types) {
    $type = ([string]$line).Substring(0, 1)
    if ($type -ne '-' -and $type -ne 'd') {
      throw 'La distribución contiene enlaces o entradas especiales no aceptadas: ' + $type
    }
  }
  [System.IO.Directory]::CreateDirectory($stage) | Out-Null
  $payload = Join-Path $stage 'runtime'
  [System.IO.Directory]::CreateDirectory($payload) | Out-Null
  & $tar -xzf $archive -C $payload
  if ($LASTEXITCODE -ne 0) { throw 'Extracción OSS CAD fallida' }
  $bin = Join-Path $payload 'oss-cad-suite\bin'
  $yosys = Join-Path $bin 'yosys.exe'
  $loader = Join-Path $bin 'openFPGALoader.exe'
  if (-not (Test-Path -LiteralPath $yosys -PathType Leaf) -or
      -not (Test-Path -LiteralPath $loader -PathType Leaf)) {
    throw 'El paquete carece de Yosys o openFPGALoader: no se instalará parcialmente'
  }
  $receipt = @{
    schema_version = 1; component = 'osscad'; version = $spec.version
    source = $spec.source; archive_sha256 = $hash
    relative_path = 'runtime/oss-cad-suite/bin/yosys.exe'
    file_sha256 = (Get-FileHash -LiteralPath $yosys -Algorithm SHA256).Hash.ToLowerInvariant()
    loader_sha256 = (Get-FileHash -LiteralPath $loader -Algorithm SHA256).Hash.ToLowerInvariant()
    nextpnr_sha256 = $(if (Test-Path -LiteralPath (Join-Path $bin 'nextpnr-generic.exe') -PathType Leaf) {
      (Get-FileHash -LiteralPath (Join-Path $bin 'nextpnr-generic.exe') -Algorithm SHA256).Hash.ToLowerInvariant()
    } else { $null })
    installed_utc = [datetime]::UtcNow.ToString('o')
  }
  $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $stage $receiptName) -Encoding UTF8
  if (Test-Path -LiteralPath $dest) { throw 'La carpeta apareció durante la instalación' }
  Move-Item -LiteralPath $stage -Destination $dest
  Write-Host 'OSS CAD Suite instalado sin PATH global: ' $dest
} finally {
  if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive -Force }
  if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
