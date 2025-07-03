@echo off
REM Script para eliminar archivos de métodos de pago obsoletos

del "d:\MI-APP-WEB\payment_methods.json" /f /q
if exist "d:\MI-APP-WEB\payment_methods.json" (
    echo No se pudo eliminar payment_methods.json
) else (
    echo payment_methods.json eliminado
)

del "d:\MI-APP-WEB\templates\payment_methods.json" /f /q
if exist "d:\MI-APP-WEB\templates\payment_methods.json" (
    echo No se pudo eliminar templates\payment_methods.json
) else (
    echo templates\payment_methods.json eliminado
)

del "d:\MI-APP-WEB\data\payment_methods.json" /f /q
if exist "d:\MI-APP-WEB\data\payment_methods.json" (
    echo No se pudo eliminar data\payment_methods.json
) else (
    echo data\payment_methods.json eliminado
)

pause
