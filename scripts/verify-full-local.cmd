@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify-full-local.ps1" %*
