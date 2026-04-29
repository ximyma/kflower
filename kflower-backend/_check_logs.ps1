Get-ChildItem E:\kkflower\kflower-backend\*.log -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output "=== $($_.FullName) ==="
    Get-Content $_.FullName -Tail 30
}
