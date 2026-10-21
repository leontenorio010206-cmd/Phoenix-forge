# PhœnixForge optional components: verified and isolated per-user installation.
# Run ONLY from the signed/verified project installer after consent in the NSIS page.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateSet("digital", "java")][string]$Component,
  [Parameter(Mandatory=$true)][string]$InstallDir
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Assert-TrustedZip($File, $Spec) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $archive = [System.IO.Compression.ZipFile]::OpenRead($File)
  try {
    if ($archive.Entries.Count -gt [int]$Spec.max_entries) { throw "Demasiados archivos en el ZIP" }
    $sum = [long]0
    foreach ($entry in $archive.Entries) {
      $n = $entry.FullName.Replace("\", "/")
      $parts = @($n.Split("/") | Where-Object { $_ -ne "" })
      if ([string]::IsNullOrWhiteSpace($n) -or $n.StartsWith("/") -or
          $n.StartsWith("//") -or $n -match "^[A-Za-z]:" -or
          $n.Contains([char]0) -or $parts -contains ".." -or $parts -contains "." -or
          $n.Contains(":") -or $n.Contains("\") -or
          $entry.Length -gt [long]$Spec.max_expanded_bytes) {
        throw "Ruta insegura o archivo demasiado grande dentro del ZIP"
      }
      $sum += [long]$entry.Length
      if ($sum -gt [long]$Spec.max_expanded_bytes) { throw "ZIP excesivamente grande al expandirse" }
      # Unix symlink bit type 0120000, detectable in the ZIP mode.
      $mode = ([int]$entry.ExternalAttributes -shr 16) -band 0xF000
      if ($mode -eq 0xA000) { throw "Los enlaces simbólicos no están permitidos" }
    }
  } finally { $archive.Dispose() }
}

$manifestPath = Join-Path $PSScriptRoot "optional-components.json"
$manifest = Get-Content -LiteralPath $manifestPath -Encoding UTF8 -Raw | ConvertFrom-Json
if ($manifest.schema_version -ne 1) { throw "Manifiesto de descargas incompatible" }
$spec = $manifest.components.$Component
if ($null -eq $spec) { throw "Componente no reconocido" }
if ($spec.url -notlike "https://github.com/*") { throw "Dominio de descarga incorrecto" }
if ($spec.sha256 -notmatch "^[0-9a-f]{64}$") { throw "SHA256 ausente en manifiesto" }

$root = [System.IO.Path]::GetFullPath($InstallDir)
$integrations = Join-Path $root "Integrations"
$destination = Join-Path $integrations ([string]$spec.folder)
$receiptPath = Join-Path $destination "phoenixforge-component.json"
[System.IO.Directory]::CreateDirectory($integrations) | Out-Null

# Never overwrite an unrelated folder. Confirm existing executable matches its receipt.
if (Test-Path -LiteralPath $destination) {
  if (-not (Test-Path -LiteralPath $receiptPath)) {
    throw "Ya existe una carpeta ajena: $destination"
  }
  $old = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $oldFile = Join-Path $destination ([string]$old.relative_path)
  if ($old.component -ne $Component -or $old.archive_sha256 -ne $spec.sha256 -or
      -not (Test-Path -LiteralPath $oldFile -PathType Leaf) -or
      (Get-FileHash -LiteralPath $oldFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $old.file_sha256) {
    throw "Instalación previa alterada; no se sobrescribirá automáticamente"
  }
  Write-Host "$Component ya está instalado y coincide con el recibo."
  exit 0
}

$stage = Join-Path $integrations (".pf-" + $Component + "-" + [guid]::NewGuid().ToString("N"))
$archivePath = Join-Path $env:TEMP ("PhoenixForge-" + $Component + "-" + [guid]::NewGuid().ToString("N") + ".zip")
try {
  Write-Host "Descargando $Component desde origen oficial..."
  Invoke-WebRequest -Uri ([string]$spec.url) -MaximumRedirection 6 -OutFile $archivePath
  $file = Get-Item -LiteralPath $archivePath
  if ($file.Length -ne [long]$spec.bytes) { throw "Tamaño inesperado de descarga" }
  $hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $spec.sha256) { throw "La verificación SHA256 falló: descarga rechazada" }
  Assert-TrustedZip $archivePath $spec

  [System.IO.Directory]::CreateDirectory($stage) | Out-Null
  $payload = Join-Path $stage "runtime"
  [System.IO.Directory]::CreateDirectory($payload) | Out-Null
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::ExtractToDirectory($archivePath, $payload)
  $candidates = @(Get-ChildItem -LiteralPath $payload -Recurse -File |
    Where-Object { $_.Name -ieq $spec.expected })
  if ($Component -eq "java") {
    $candidates = @($candidates | Where-Object { $_.DirectoryName -match "[\\/]bin$" })
  }
  if ($candidates.Count -ne 1) { throw "El archivo esperado no aparece exactamente una vez" }
  $expectedFile = $candidates[0]
  # Receipts use portable forward slashes; Python rejects Windows-only separators.
  $relative = $expectedFile.FullName.Substring($stage.Length + 1).Replace('\', '/')
  $receipt = @{
    schema_version = 1
    component = $Component
    version = $spec.version
    source = $spec.source
    archive_sha256 = $hash
    relative_path = $relative
    file_sha256 = (Get-FileHash -LiteralPath $expectedFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    installed_utc = [datetime]::UtcNow.ToString("o")
  }
  $receipt | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $stage "phoenixforge-component.json") -Encoding UTF8
  if (Test-Path -LiteralPath $destination) { throw "Otra instalación apareció durante la descarga" }
  Move-Item -LiteralPath $stage -Destination $destination
  Write-Host "Instalación finalizada: $destination"
} finally {
  if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath -Force }
  if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
