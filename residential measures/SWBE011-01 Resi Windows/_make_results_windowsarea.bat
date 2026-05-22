@ECHO OFF
CALL modelkit-energyplus energyplus-sql --query=results_windowsarea.txt --output=results_windowsarea.csv **\*.sql
PAUSE
