# -----------------------------------------------------------
#  Pomponio Ranch Labeling System -- Nightly Reboot Scheduler
#
#  Run once with elevated privileges (Run as Administrator):
#    powershell -ExecutionPolicy Bypass -File setup_nightly_reboot.ps1
#
#  Creates a Windows Task Scheduler task that reboots the
#  machine at 11:59 PM every day. The reboot is forced (/f)
#  so open applications will not block shutdown.
#
#  To remove the scheduled task later:
#    Unregister-ScheduledTask -TaskName "PomponioNightlyReboot" -Confirm:$false
# -----------------------------------------------------------

$TaskName = "PomponioNightlyReboot"
$Description = "Reboot the kiosk machine nightly at 11:59 PM for stability"

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "ERROR: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as administrator', then re-run this script."
    Write-Host ""
    exit 1
}

# Remove existing task if present (idempotent re-runs)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Define the action: forced reboot with zero delay
$action = New-ScheduledTaskAction -Execute "shutdown.exe" -Argument "/r /f /t 0"

# Define the trigger: daily at 11:59 PM
$trigger = New-ScheduledTaskTrigger -Daily -At "11:59PM"

# Define the principal: run as SYSTEM with highest privileges
# SYSTEM account ensures the task runs even if no user is logged in
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

# Task settings: allow start if on batteries, do not stop on battery switch,
# wake the machine if sleeping, no execution time limit
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $Description `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings

Write-Host ""
Write-Host "SUCCESS: Scheduled task '$TaskName' created." -ForegroundColor Green
Write-Host "The machine will reboot every day at 11:59 PM."
Write-Host ""
Write-Host "To verify:  Get-ScheduledTask -TaskName '$TaskName' | Format-List"
Write-Host "To remove:  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host ""
