Set WshShell = CreateObject("WScript.Shell")
PythonPath = "pythonw.exe"
ScriptPath = """C:\Users\baran\OneDrive\Desktop\side projects\Zeroinput\main.py"""
WshShell.Run PythonPath & " " & ScriptPath, 0, False
WshShell.Popup "ZeroInput is now running in the background.", 2, "ZeroInput Started", 64