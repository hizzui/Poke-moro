# DIB

Aplicativo web com técnica Pomodoro e sistema de gamificação com animais.

## Funcionalidades

- Timer Pomodoro (25 min foco + 5 min pausa, customizável)
- Seleção entre 3 animais (Pássaro, Coruja, Raposa)
- Sistema de XP e Níveis (10 XP por minuto)
- Persistência automática com localStorage
- To-do list integrada
- Interface minimalista responsiva  

## Como Executar

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Rodar o servidor:
```bash
python api/index.py
```

3. Acessar em: http://localhost:8000

## Tecnologias

Backend: FastAPI, Uvicorn  
Frontend: HTML5, JavaScript, Tailwind CSS  
Recursos: GSAP (animações), Three.js (fundo 3D), Lenis (scroll suave)  
Armazenamento: localStorage


