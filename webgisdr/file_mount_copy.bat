REM Batch file to mount an Azure file share on the portal machine
REM and then copy the webgisdr backup files (full and incremental)
REM to the Azure files location
REM
REM Date: April 2019
REM Version: 1.0

REM First remove the mapping
net use z:/delete

REM now mount the Azure file as the 'z' drive.
net use Z: \\sdmsstorage1.file.core.windows.net\webgisdrbackups /u:AZURE\sdmsstorage1 [API KEY]

REM Use robocopy to copy the files and folders to the Azure file location.
robocopy c:\webgisdr_backups Z:\dev1_webgisdr_backups /COPYALL