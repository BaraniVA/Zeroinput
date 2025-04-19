Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "taskkill /f /im pythonw.exe /fi ""WINDOWTITLE eq Zeroinput""", 0, True
WshShell.Popup "ZeroInput has been stopped.", 2, "ZeroInput Stopped", 64