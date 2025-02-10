@echo off
REM This script is used to delete all .blend1 files in the current directory, then use blend2bam to convert all .blend files to .bam files

REM Usage: multi.bat

REM Change to the directory where the script is located
cd /d "%~dp0"
echo Current directory: %cd%
REM Delete all .blend1 files in the current directory
del /q *.blend1
echo Deleted all .blend1 files
REM Create bam directory if it doesn't exist
if not exist bam mkdir bam
REM create a list of all .blend files
setlocal enabledelayedexpansion
set "blendFiles="
for %%f in (*.blend) do (
  set "blendFiles=!blendFiles! %%f"
)

if not defined blendFiles (
  echo No .blend files found to convert.
  pause
  exit /b
)

REM Convert all .blend files to .bam files
for %%f in (*.blend) do (
  echo Converting %%f to %%~nf.bam
  blend2bam "%%f" "bam\%%~nf.bam" --blender-dir "C:\Program Files\Blender Foundation\Blender 3.6" --textures copy
  if errorlevel 1 (
    echo Failed to convert %%f
    echo Deleting incomplete BAM file "bam\%%~nf.bam"
    del "bam\%%~nf.bam"
    ) else (
    echo Successfully converted %%f
  )
)

REM print the contents of the bam directory
echo Contents of bam directory:
dir bam

set "successCount=0"
set "failCount=0"
for %%f in (bam\*.bam) do (
  echo Processed: %%f
  if exist "bam\%%~nf.bam" (
    set /a successCount+=1
    ) else (
    set /a failCount+=1
  )
)

echo Summary of conversions:
echo Successful conversions: !successCount!
echo Failed conversions: !failCount!

pause
REM End of script
