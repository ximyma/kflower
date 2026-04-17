# 转换所有Vue文件为UTF-8编码
$basePath = Get-Location

# 查找所有Vue文件
$vueFiles = Get-ChildItem -Path $basePath -Recurse -Filter "*.vue"

Write-Host "找到 $($vueFiles.Count) 个Vue文件，开始转换编码..."

$successCount = 0
$skipCount = 0
$errorCount = 0

foreach ($file in $vueFiles) {
    $filePath = $file.FullName
    $relativePath = $file.FullName.Substring($basePath.Path.Length + 1)
    
    try {
        # 尝试用UTF-8读取文件
        $content = Get-Content -Path $filePath -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
        
        # 如果UTF-8读取失败（可能文件是GBK编码），尝试用Default编码（系统默认，通常是GBK）
        if ($null -eq $content) {
            $content = Get-Content -Path $filePath -Encoding Default -Raw
            Write-Host "检测到GBK编码: $relativePath"
        } else {
            Write-Host "已经是UTF-8编码: $relativePath"
            $skipCount++
            continue
        }
        
        # 将内容转换为UTF-8并保存
        # 使用UTF-8 with BOM确保兼容性
        $utf8WithBOM = [System.Text.Encoding]::UTF8
        $bytes = $utf8WithBOM.GetBytes($content)
        
        # 添加BOM
        $bom = [System.Text.Encoding]::UTF8.GetPreamble()
        $bytesWithBOM = $bom + $bytes
        
        [System.IO.File]::WriteAllBytes($filePath, $bytesWithBOM)
        
        Write-Host "转换成功: $relativePath"
        $successCount++
        
    } catch {
        Write-Host "转换失败: $relativePath - $_" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host "`n转换完成！"
Write-Host "成功: $successCount 个文件"
Write-Host "跳过: $skipCount 个文件（已经是UTF-8）"
Write-Host "失败: $errorCount 个文件"