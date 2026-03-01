# Fetch the last 10 critical/error events from the System Event Log
try {
    $events = Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2,3} -MaxEvents 10 -ErrorAction SilentlyContinue
    if ($events) {
        $events | Select-Object TimeCreated, LevelDisplayName, Message | Format-Table -Wrap -AutoSize
    } else {
        Write-Output "No critical or error events found in the recent System log."
    }
} catch {
    Write-Error "Failed to retrieve event logs: $($_.Exception.Message). Note: This query may require Administrator privileges depending on the log."
}
