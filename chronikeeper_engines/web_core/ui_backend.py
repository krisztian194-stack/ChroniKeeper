import os
import sys

# ✅ Make sure project root is on path BEFORE imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# now import modules
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chronikeeper_engines.world_core.environment_engine import EnvironmentEngine
from chronikeeper_engines.simulation_core.character_state_engine import CharacterStateEngine
from chronikeeper_engines.world_core.world_state import WorldState
from chronikeeper_engines.prompt_core.prompt_manager import PromptManager


app = FastAPI(title="ChroniKeeper Web UI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "ui_templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "ui_static")), name="static")

# --- init engines ---
world = WorldState()
world.environment_engine = EnvironmentEngine()
char_engine = CharacterStateEngine()
prompt_manager = PromptManager(char_engine, world)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    ctx = char_engine.get_context_fragment()
    return templates.TemplateResponse("dashboard.html", {"request": request, "ctx": ctx})


@app.get("/api/state")
async def api_state():
    return JSONResponse(char_engine.get_context_fragment())


@app.get("/api/tick")
async def api_tick(hours: float = 0.05):
    # 1) advance env time
    world.environment_engine.advance_time(hours)

    # 2) refresh world signature (different versions name this differently)
    if hasattr(world, "update_environment"):
        world.update_environment()
    elif hasattr(world, "refresh"):
        world.refresh()
    else:
        # fallback: pull it directly from env
        world.environment_signature = world.environment_engine.signature

    # 3) let character react
    char_engine.update_state(world.environment_signature)

    # 4) persist
    char_engine.save()

    return JSONResponse({
        "ok": True,
        "hours": hours,
        "state": char_engine.get_context_fragment()
    })


@app.get("/api/prompt")
async def api_prompt():
    prompt_text = prompt_manager.build_instruction_prompt("Look around.")
    return JSONResponse({"prompt": prompt_text})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "chronikeeper_engines.web_core.ui_backend:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
