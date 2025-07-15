"""Run the Flask Meeting Assistant.

This file used to contain a Streamlit implementation. To avoid confusing
`ModuleNotFoundError` messages when running `python app.py`, it now simply
launches the Flask app defined in ``run.py``.
"""

from run import app, socketio


if __name__ == "__main__":  # pragma: no cover
    socketio.run(app, debug=True, host="127.0.0.1", port=5000)

