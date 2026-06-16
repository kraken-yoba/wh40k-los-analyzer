@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify-public.ps1" %*
