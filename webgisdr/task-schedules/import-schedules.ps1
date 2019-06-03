param (
    [Parameter(Mandatory=$true)]
    [string]$username,
    [Parameter(Mandatory=$true)]
    [string]$password
 )

Register-ScheduledTask -Xml (get-content 'C:\Program Files\ArcGIS\Portal\tools\webgisdr\task-schedules\Webgisdr_incremental.xml' | out-string) -TaskName "webgisdr partial backup" -User $username -Password $password –Force
Register-ScheduledTask -Xml (get-content 'C:\Program Files\ArcGIS\Portal\tools\webgisdr\task-schedules\Webgisdr_full.xml' | out-string) -TaskName "webgisdr full backup" -User $username -Password $password –Force