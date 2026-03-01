# Reset the DNS client cache
try {
    Clear-DnsClientCache
    Write-Output "DNS Client Cache has been successfully cleared."
} catch {
    Write-Error "Failed to clear DNS cache: $($_.Exception.Message). Note: This may require Administrator privileges."
}
