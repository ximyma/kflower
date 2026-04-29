Get-NetTCPConnection -LocalPort 8788 | ForEach-Object {
    $pid = $_.OwningProcess
    Get-Process -Id $pid | Select-Object Id, ProcessName, Path
}
