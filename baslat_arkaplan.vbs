Option Explicit

Dim shell, fso, appDir, pythonw, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = fso.BuildPath(appDir, ".venv\Scripts\pythonw.exe")
If Not fso.FileExists(pythonw) Then
    Dim hermesVenv
    hermesVenv = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\pythonw.exe")
    If fso.FileExists(hermesVenv) Then
        pythonw = hermesVenv
    Else
        pythonw = "pythonw.exe"
    End If
End If

shell.CurrentDirectory = appDir
command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & fso.BuildPath(appDir, "main.py") & Chr(34)
shell.Run command, 0, False
