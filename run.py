import os

from app import create_app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "0.0.0.0"),
        port=int(os.environ.get("FLASK_RUN_PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        use_reloader=os.environ.get(
            "FLASK_USE_RELOADER", "false").lower() == "true",
    )
