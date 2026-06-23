@echo off
chcp 65001 > nul
echo 포켓북 빌드 중...
python "%~dp0build_book.py"
if %ERRORLEVEL% == 0 (
    echo.
    echo 완료: 포켓북_전체.html 생성됨
    echo 브라우저에서 확인하세요
) else (
    echo.
    echo 오류 발생
)
pause
