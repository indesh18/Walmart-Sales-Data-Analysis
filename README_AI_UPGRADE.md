# Walmart Sales Analytics — AI Upgrade

## Added features
- KPI cards: total sales, units sold, transactions, average transaction value
- Filters: city, branch, category, payment method, and date (where available)
- Sales by product category and monthly trend charts
- Branch performance and payment method tables
- Gemini-powered AI Sales Assistant grounded in metrics from the filtered dataset
- Optional CSV upload

## Files to add
Copy `app.py`, `requirements.txt`, `.gitignore`, and `README_AI_UPGRADE.md` into the same folder as your existing `Walmart_Dataset.csv`. Keep your original notebook and SQL file unchanged.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Dashboard charts work without an API key. AI Q&A needs a Google Gemini API key.

## Configure Gemini
1. Get a key from https://aistudio.google.com/app/apikey
2. Create a `.streamlit` folder beside `app.py`.
3. Create `.streamlit/secrets.toml` with:
```toml
GOOGLE_API_KEY = "AIzaSyDSG77vfnF4gkFUmtAuqpqw9IRbhnmyXSU"
```
4. Restart Streamlit.

Never upload your real key, `.env`, or `.streamlit/secrets.toml` to GitHub. The `.gitignore` file excludes them.

## Deploy on Streamlit Community Cloud
1. Push the files to GitHub.
2. Go to https://share.streamlit.io/ and create a new app.
3. Select your repository and set Main file path to `app.py`.
4. Add this under the app's Advanced settings → Secrets:
```toml
GOOGLE_API_KEY = "your_real_key"
```
5. Deploy.

## Metric note
Sales = `unit_price × quantity`. If `profit_margin` exists, estimated profit is sales × profit_margin. This is an estimate, not audited accounting profit.
