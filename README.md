# GET-E Converter

This project contains a small Streamlit application for converting GET‑E raw Excel files into the import format used by the system.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application with:
   ```bash
   streamlit run app.py
   ```
   The web interface will be available on `http://localhost:8501`.

## Deployment

Deploy the app on any server capable of running Python. The repository bundles a CSV template (`template.csv`) which the app loads automatically. Uploading a custom template is optional.

