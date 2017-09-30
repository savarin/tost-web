from app import create_app
from werkzeug.serving import run_simple


app = create_app()


if __name__ == "__main__":
    # app.run()
    run_simple('localhost', 8000, app,
               use_reloader=True, use_debugger=True, use_evalex=True)