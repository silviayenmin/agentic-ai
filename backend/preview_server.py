import os
import sys
import importlib.util
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Setup directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(BASE_DIR, "..", "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# Add workspace to system path so imports inside workspace work
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

app = FastAPI(title="Dynamic Universal Preview Server")

# General CORS for the preview environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def health_check():
    """Health check for the React UI to see if the workspace server is online."""
    return {"status": "online"}

# Attempt to load the workspace backend dynamically
main_py = os.path.join(WORKSPACE_DIR, "main.py")
if os.path.exists(main_py):
    try:
        spec = importlib.util.spec_from_file_location("workspace_main", main_py)
        module = importlib.util.module_from_spec(spec)
        sys.modules["workspace_main"] = module
        spec.loader.exec_module(module)
        
        # If the workspace creates an 'app', mount it
        if hasattr(module, "app") and isinstance(module.app, FastAPI):
            app.mount("/api", module.app)
            print("[Preview Server] Hosted Workspace Backend at /api")
        # Fallback if they just made a router
        elif hasattr(module, "router"):
            app.include_router(module.router, prefix="/api")
            print("[Preview Server] Hosted Workspace API Router at /api")
    except Exception as e:
        print(f"[Preview Server] Failed to load workspace backend: {e}")

# Mount static files (React/HTML generation)
# We serve anything in workspace that isn't python logic
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(WORKSPACE_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Preview Server Online</h1><p>No index.html generated yet.</p>"

# Serve other static files (like CSS, independent JS, assets)
app.mount("/static", StaticFiles(directory=WORKSPACE_DIR), name="workspace_static")

if __name__ == "__main__":
    import uvicorn
    # Important: Run with --reload pointing to the workspace so it hot-reloads when agents write code!
    uvicorn.run("preview_server:app", host="127.0.0.1", port=8001, reload=True, reload_dirs=[WORKSPACE_DIR, BASE_DIR])
