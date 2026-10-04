# Launches run_htl.bat in a hidden console window so it cannot be closed accidentally.
# Progress: watch htl_run.log in the _Htl_Ex study folder, or count instance-out.sql files under runs\.
Start-Process -FilePath "c:\dev\SWHC062-03\commercial measures\SWHC062-03 Occupancy Fan Controller\run_htl.bat" -WindowStyle Hidden
