@echo off
REM Launches a Chrome that Live Interview Assistant can read over CDP.
REM
REM Port 9223 on purpose: 9222 is already held by another Chrome on this machine (an extension-only
REM instance with no page tabs), and a second browser cannot bind a port that is taken -- it fails
REM SILENTLY and the app then sees no tabs. Keep this in step with interview.screen_cdp_url.
REM
REM Separate profile so it never disturbs your normal browsing session.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9223 ^
  --user-data-dir="%LOCALAPPDATA%\InterviewAssistantChrome" ^
  --no-first-run --no-default-browser-check %*
