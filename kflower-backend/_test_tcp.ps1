$s = New-Object System.Net.Sockets.TcpClient
$s.Connect("localhost", 8788)
$stream = $s.GetStream()
$sw = New-Object System.IO.StreamWriter($stream)
$sr = New-Object System.IO.StreamReader($stream)
$sw.Write("GET / HTTP/1.1`r`nHost: localhost`r`nConnection: close`r`n`r`n")
$sw.Flush()
Start-Sleep 3
$response = $sr.ReadToEnd()
$s.Close()
Write-Output $response
