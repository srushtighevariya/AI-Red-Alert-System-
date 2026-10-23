# Stops whatever is serving this project on the given ports, including
# orphaned Python workers: on Windows a venv's python.exe is only a launcher
# and uvicorn's workers can outlive it while still holding the port.
param([int[]]$Ports = @(8000, 5173))

foreach ($port in $Ports) {
    for ($attempt = 0; $attempt -lt 6; $attempt++) {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $listener) { break }

        $ownerId = $listener.OwningProcess
        $owner = Get-Process -Id $ownerId -ErrorAction SilentlyContinue

        if ($owner) {
            Write-Host "Stopping old process on port $port (PID $ownerId)"
            taskkill /T /F /PID $ownerId 2>&1 | Out-Null
        }

        # Workers started by a (possibly already dead) owner keep its socket open.
        Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match "spawn_main\(parent_pid=$ownerId\b" } |
            ForEach-Object {
                Write-Host "Stopping leftover worker on port $port (PID $($_.ProcessId))"
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }

        Start-Sleep -Milliseconds 800
    }

    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "[WARNING] Port $port is still in use. Close the old server window or restart Windows."
    }
}
