$ErrorActionPreference = "Stop"

Write-Host "Starting API Server..."
$apiProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "main:app", "--port", "8000" -PassThru -NoNewWindow

Start-Sleep -Seconds 5

$tests = @(
    @{ users = 10; time = "15s" },
    @{ users = 25; time = "25s" },
    @{ users = 50; time = "40s" },
    @{ users = 100; time = "60s" }
)

foreach ($t in $tests) {
    $u = $t.users
    $time = $t.time
    Write-Host "=========================================="
    Write-Host "Running Load Test with EXACTLY $u requests..."
    Write-Host "=========================================="
    
    .\.venv\Scripts\locust.exe --headless -u $u -r $u -t $time --host http://127.0.0.1:8000
    
    Start-Sleep -Seconds 5
}

Write-Host "Stopping API Server..."
Stop-Process -Id $apiProcess.Id -Force
Write-Host "Load Tests Completed."
