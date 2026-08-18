# Laptop store chatbot

End to end chatbot over scraped priceoye.pk laptop listings and store policy FAQs.

## Setup

```
pip install -r requirements.txt
```

Set your Groq key (optional, used only to phrase final answers):

```
export GROQ_API_KEY=your_key_here
```

## Build data and database

Run these once, in order:

```
cd scraper
python scrape_products.py

cd ../database
python build_db.py

cd ../faq
python build_faq_index.py
```

This creates `data/products.json`, `database/ecommerce.db`, and `faq/faq_embeddings.npy`.

## Run the app

```
cd ..
streamlit run app.py
```

## Expose with ngrok

Install ngrok and authenticate once with your token, then in a separate terminal:

```
ngrok http 8501
```

Copy the forwarding https link ngrok prints and share that as the live link.

Alternative using pyngrok inside python:

```python
from pyngrok import ngrok
public_url = ngrok.connect(8501)
print(public_url)
```

## Notes

- The scraper adds a delay between page requests and is capped at 6 pages.
- If priceoye.pk changes its page layout, the CSS selectors in
  `scraper/scrape_products.py` may need adjustment.
- If `GROQ_API_KEY` is not set, the app falls back to a plain templated
  answer instead of a phrased one.
