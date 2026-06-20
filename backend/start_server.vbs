Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\My_Web_Tools\video-transcriber\backend && uvicorn main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 600", 0, False
