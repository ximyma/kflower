# 备份所有Vue文件
$basePath = Get-Location
$backupDir = Join-Path $basePath "backup-vue-files"

# 创建备份目录
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force
}

# 查找所有Vue文件
$vueFiles = Get-ChildItem -Path $basePath -Recurse -Filter "*.vue"

Write-Host "找到 $($vueFiles.Count) 个Vue文件，开始备份..."

foreach ($file in $vueFiles) {
    # 计算相对路径
    $relativePath = $file.FullName.Substring($basePath.Path.Length + 1)
    $backupPath = Join-Path $backupDir $relativePath
    
    # 创建目标目录
    $backupDirPath = [System.IO.Path]::GetDirectoryName($backupPath)
    if (!(Test-Path $backupDirPath)) {
        New-Item -ItemType Directory -Path $backupDirPath -Force | Out-Null
    }
    
    # 复制文件
    Copy-Item -Path $file.FullName -Destination $backupPath -Force
    Write-Host "备份: $relativePath"
}

Write-Host "备份完成！所有Vue文件已备份到: $backupDir"