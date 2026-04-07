# Script de Setup - Pomodoro Animais
# Execute este script em PowerShell para configurar o projeto

Write-Host "Configurando Pomodoro Animais..." -ForegroundColor Cyan
Write-Host ""

# Verificar se Python está instalado
Write-Host "Verificando Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro: Python não encontrado! Instale Python 3.8+ de https://www.python.org/" -ForegroundColor Red
    exit 1
}

Write-Host "Python encontrado!" -ForegroundColor Green
Write-Host ""

# Criar ambiente virtual (opcional)
Write-Host "Criando ambiente virtual..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "Ambiente virtual criado!" -ForegroundColor Green
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "Ambiente virtual não necessário" -ForegroundColor Yellow
}

Write-Host ""

# Instalar dependências
Write-Host "Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependências instaladas!" -ForegroundColor Green
} else {
    Write-Host "Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Informações finais
Write-Host "Setup Completo!" -ForegroundColor Green
Write-Host ""
Write-Host "Para executar o servidor:" -ForegroundColor Cyan
Write-Host "   python api/index.py" -ForegroundColor White
Write-Host ""
Write-Host "Depois acesse:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000" -ForegroundColor White
Write-Host ""
