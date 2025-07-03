@echo off
REM Script para eliminar la plantilla de edición de perfil de usuario

del "d:\MI-APP-WEB\templates\user_edit_profile.html" /f /q
if exist "d:\MI-APP-WEB\templates\user_edit_profile.html" (
    echo No se pudo eliminar user_edit_profile.html
) else (
    echo user_edit_profile.html eliminado
)

pause
