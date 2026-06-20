Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c uvicorn main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 600", 0, False
