# -*- coding: utf-8 -*-
"""生成两个纯 ASCII 的 .cmd 启动器（cmd.exe 按 OEM 代码页读文件，中文会乱码）。"""
import io
import os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CMD = (
    "@echo off\r\n"
    "setlocal\r\n"
    'cd /d "%~dp0"\r\n'
    'if not exist "%~dp0start.ps1" (\r\n'
    "  echo [ERR] start.ps1 is missing next to this file.\r\n"
    "  pause\r\n"
    "  exit /b 1\r\n"
    ")\r\n"
    'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*\r\n'
    "if errorlevel 1 pause\r\n"
)

ALIAS = (
    "@echo off\r\n"
    'call "%~dp0start.cmd" %*\r\n'
)

for name, text in (("start.cmd", CMD), ("\u542f\u52a8.cmd", ALIAS)):
    p = os.path.join(D, name)
    io.open(p, "wb").write(text.encode("ascii"))
    print("wrote", name, len(text), "chars")
