REM file organiser
REM
@Echo off

rem for each file in your folder
for%%a in (".\*") do (
REM check if the file has an extension and if it is not our script
if "%%~xa" NEQ "" if "%%~dpxa" NEQ "%~dpx0" (
    REM check if extension folder exists, if not it is created
    if not exist "%%~xa" mkdir "%%~xa"
    REM move the file to directory
    move "%%a" "%%~dpa%%~xa\"
)
)