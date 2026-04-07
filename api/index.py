from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import math

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dados dos Animais
ANIMALS = {
    "passaro": {
        "name": "Pássaro",
        "type": "Criativo",
        "color": "bg-blue-300"
    },
    "coruja": {
        "name": "Coruja",
        "type": "Sábio",
        "color": "bg-amber-700"
    },
    "raposa": {
        "name": "Raposa",
        "type": "Estratégico",
        "color": "bg-orange-300"
    }
}

@app.get("/")
async def root():
    """Serve the main HTML file"""
    public_path = os.path.join(os.path.dirname(__file__), "..", "public", "index.html")
    if os.path.exists(public_path):
        return FileResponse(public_path)
    return {"message": "Pomodoro Animais - API Running"}

@app.get("/api/animals")
async def get_animals():
    """Retorna lista de animais disponíveis"""
    return {
        "animals": [
            {
                "id": key,
                "name": data["name"],
                "type": data["type"]
            }
            for key, data in ANIMALS.items()
        ]
    }

@app.post("/api/calculate-level")
async def calculate_level(xp: int):
    """Calcula o nível baseado em XP"""
    if xp < 0:
        return {"level": 1, "xp": 0, "xp_for_next_level": 100}
    
    level = (xp // 100) + 1
    xp_current_level = xp % 100
    xp_for_next_level = 100
    
    return {
        "level": level,
        "xp": xp,
        "xp_current_level": xp_current_level,
        "xp_for_next_level": xp_for_next_level,
        "progress": (xp_current_level / xp_for_next_level) * 100
    }

@app.get("/api/animal/{animal_id}")
async def get_animal(animal_id: str):
    """Retorna dados de um animal específico"""
    animal_id = animal_id.lower()
    if animal_id not in ANIMALS:
        return JSONResponse(
            status_code=404,
            content={"error": "Animal não encontrado"}
        )
    
    animal = ANIMALS[animal_id]
    return {
        "id": animal_id,
        "name": animal["name"],
        "type": animal["type"],
        "color": animal["color"]
    }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Pomodoro Animais API is running"}

# Configurar arquivos estáticos da pasta public
try:
    public_dir = os.path.join(os.path.dirname(__file__), "..", "public")
    if os.path.exists(public_dir):
        app.mount("/static", StaticFiles(directory=public_dir), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
