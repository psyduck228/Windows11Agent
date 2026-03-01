# Query WMI for startup programs
try {
    $startupApps = Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location
    if ($startupApps) {
        $startupApps | Format-Table -AutoSize
    } else {
        Write-Output "No startup programs found or permission denied."
    }
} catch {
    Write-Error "Failed to retrieve startup processes: $($_.Exception.Message)"
}
