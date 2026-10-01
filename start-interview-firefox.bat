@echo off
REM Launches a Firefox that Live Interview Assistant can read over WebDriver BiDi.
REM
REM   start-interview-firefox.bat            -> normal run, remote agent ON  (Path A works)
REM   start-interview-firefox.bat login      -> remote agent OFF, for SIGNING IN
REM
REM WHY THE LOGIN MODE EXISTS: --remote-debugging-port makes Firefox set navigator.webdriver=true
REM permanently (measured -- it stays true even between our reads, unlike Chrome, which leaves it
REM false because we never pass --enable-automation). Google refuses to sign you in when it sees
REM that flag: "This browser or app may not be secure". Firefox also shows a robot icon in the URL
REM bar while the agent is on.
REM
REM So: run `login` once, sign in to Google / the interview platform, close the window. The cookies
REM live in this profile, so the normal run afterwards is already signed in and never has to show
REM Google the flag.
REM
REM Firefox does NOT speak CDP (Mozilla removed it) -- it speaks WebDriver BiDi on the same
REM --remote-debugging-port. The app probes the port and picks the protocol itself, so
REM interview.screen_cdp_url stays http://127.0.0.1:9223 for BOTH browsers. Use this launcher OR
REM start-interview-chrome.bat, never both at once: two browsers cannot share one port, and the
REM second one fails SILENTLY.
REM
REM -no-remote -new-instance is required. Without them, a Firefox that is already running just
REM opens a tab in the EXISTING process and the remote agent never starts -- the app then sees
REM nothing on 9223 and Path A looks broken for no visible reason.

if /I "%~1"=="login" goto :login

start "" "C:\Program Files\Mozilla Firefox\firefox.exe" ^
  -no-remote -new-instance ^
  -profile "%LOCALAPPDATA%\InterviewAssistantFirefox" ^
  --remote-debugging-port=9223 %*
goto :eof

:login
echo.
echo   Sign-in mode: the remote agent is OFF, so Google will accept this window.
echo   Sign in, then CLOSE it and run this script again with no argument.
echo.
start "" "C:\Program Files\Mozilla Firefox\firefox.exe" ^
  -no-remote -new-instance ^
  -profile "%LOCALAPPDATA%\InterviewAssistantFirefox"
