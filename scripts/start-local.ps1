$ErrorActionPreference = 'Stop'

docker compose up --build -d

$url = 'http://localhost:4200'
$chromeCandidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chrome) {
    Start-Process -FilePath $chrome -ArgumentList $url
} else {
    Start-Process $url
}
