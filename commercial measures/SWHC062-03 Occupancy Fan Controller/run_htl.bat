@echo off
rem Launches the SWHC062-03 Htl study (640 runs, ~2 days). Log: htl_run.log in the study folder.
cd /d "c:\dev\SWHC062-03\commercial measures\SWHC062-03 Occupancy Fan Controller\SWHC062-03 Occupancy Fan Controller_Htl_Ex"
call "C:\Program Files (x86)\Modelkit Caboodle\bin\modelkit.bat" rake > htl_run.log 2>&1
