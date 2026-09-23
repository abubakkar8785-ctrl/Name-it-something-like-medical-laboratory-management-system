"""
Development entry point. Run with:  python run.py

For the packaged desktop experience, use desktop_launcher.py instead
(that's what gets built into MedicalLaboratory.exe).
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
