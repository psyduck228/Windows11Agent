# Check network adapter status and test connectivity
try {
    Write-Output "--- Network Adapters ---"
    Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name, InterfaceDescription, Status, LinkSpeed | Format-Table -AutoSize
    
    Write-Output "`n--- Internet Connectivity ---"
    if (Test-Connection -ComputerName "8.8.8.8" -Count 1 -Quiet) {
        Write-Output "Internet is REACHABLE."
    } else {
        Write-Output "Internet is UNREACHABLE."
    }
} catch {
    Write-Error "Failed to check network status: $($_.Exception.Message)"
}
