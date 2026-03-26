@echo off
:loop
python run.py
echo Bot crashed or stopped. Restarting in 5 seconds...
timeout /t 5
goto loop