import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # 🔥 ESSENCIAL
        port=port,
        reload=False     # 🔥 IMPORTANTE (Railway não usa reload)
    )