# Check network adapter status and test connectivity
try {
    Write-Output "--- Network Adapters ---"
    Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name, InterfaceDescription, Status, LinkSpeed | Format-Table -AutoSize
    
    Write-Output "`n--- Internet Connectivity ---"
    $checkIp = if ($env:DIAGNOSTIC_CHECK_IP) { $env:DIAGNOSTIC_CHECK_IP } else { "8.8.8.8" }
    if (Test-Connection -ComputerName $checkIp -Count 1 -Quiet) {
        Write-Output "Internet is REACHABLE."
    } else {
        Write-Output "Internet is UNREACHABLE."
    }
} catch {
    Write-Error "Failed to check network status: $($_.Exception.Message)"
}
