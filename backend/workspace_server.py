import os
import importlib.util
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

def create_app():
    app = FastAPI(title="Dynamic Workspace Server")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workspace")
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    @app.get("/hello")
    def hello():
        return {"status": "online", "message": "Universal Workspace Server is active"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Dynamic Route Loader
    def load_workspace_routes():
        main_py = os.path.join(WORKSPACE_DIR, "main.py")
        if not os.path.exists(main_py):
            return
        
        try:
            # 1. Load the module dynamically
            spec = importlib.util.spec_from_file_location("workspace_main", main_py)
            module = importlib.util.module_from_spec(spec)
            sys.modules["workspace_main"] = module
            spec.loader.exec_module(module)
            
            # 2. Look for FastAPI app or APIRouter
            if hasattr(module, "app") and isinstance(module.app, FastAPI):
                # We can't easily merge two FastAPI apps at runtime in a simple way 
                # without sub-mounting, but we can mount it as a sub-app
                app.mount("/api", module.app)
                print("[Workspace] Mounted workspace app at /api")
            elif hasattr(module, "router"):
                app.include_router(module.router)
                print("[Workspace] Included workspace router")
        except Exception as e:
            print(f"[Workspace Error] Could not load workspace/main.py: {e}")

    # Fallback to serve index.html at root
    @app.get("/", response_class=HTMLResponse)
    async def root():
        index_path = os.path.join(WORKSPACE_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>Platform Preview Ready</h1><p>Generate some code to see it here.</p>"

    # Load routes on startup 
    # (Note: For true dynamic behavior, we'd use a file watcher or reload on every request in dev)
    load_workspace_routes()
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
