# app.py
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)

def duckduckgo_search(query, num_results=3):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", class_="result__a"):
            href = a.get("href")
            if href and "uddg=" in href:
                parsed = urlparse(href)
                link = unquote(parse_qs(parsed.query).get("uddg", [""])[0])
                title = a.text.strip()
                results.append({"title": title, "link": link})
            if len(results) >= num_results:
                break
    except Exception as e:
        results.append({"title": "Error", "link": "#", "snippet": str(e)})
    return results

def scrape_details(link):
    try:
        res = requests.get(link, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p"))
        return text
    except:
        return ""

def extract_health_info(text):
    import re

    diseases = []
    meds = []
    precautions = []

    # Basic pattern matching
    for sentence in text.split("."):
        s = sentence.lower()
        if "disease" in s or "disorder" in s or "condition" in s:
            diseases.append(sentence.strip())
        if "take" in s or "medicine" in s or "drug" in s or "tablet" in s:
            meds.append(sentence.strip())
        if "avoid" in s or "should not" in s or "rest" in s or "drink water" in s:
            precautions.append(sentence.strip())

    return {
        "diseases": diseases[:3],
        "medications": meds[:3],
        "precautions": precautions[:3]
    }

@app.route("/", methods=["GET", "POST"])
def index():
    user_input = ""
    extracted_info = {"diseases": [], "medications": [], "precautions": []}
    search_results = []

    if request.method == "POST":
        user_input = request.form.get("text")
        if user_input.strip():
            search_results = duckduckgo_search(user_input)
            for result in search_results:
                content = scrape_details(result["link"])
                info = extract_health_info(content)
                for k in extracted_info:
                    extracted_info[k].extend(info[k])

            # Deduplicate
            for k in extracted_info:
                extracted_info[k] = list(set(extracted_info[k]))[:3]

    return render_template("index.html", query=user_input, results=search_results, info=extracted_info)

if __name__ == "__main__":
    app.run(debug=True)
