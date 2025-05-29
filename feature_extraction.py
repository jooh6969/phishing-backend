from urllib.parse import urlparse, urljoin, urlunparse
import re
import numpy as np
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv

def length_url(url):
    return len(url)

def count_www(url):
    return url.lower().count("www")

def longest_word_path(url):
    path = urlparse(url).path  # e.g., '/some/longestword123/path'
    words = path.strip("/").split("/")  # split by slash
    if not words or words == ['']:
        return 0
    longest_word = max(words, key=len)
    return len(longest_word)

def phish_count(url):
    with open('phishing_keywords.csv', 'r') as file:
        csv_reader = csv.reader(file)
        url_lower = url.lower()
        countPhish = sum(1 for row in csv_reader if row[0].lower() in url_lower)
    return countPhish

def num_hyper(url):
    try:
        base_domain = urlparse(url).netloc
        # make sure you have chrome driver in the path else this will not work      
        driver = webdriver.Chrome()
        driver.get(url)

        a_elements = driver.find_elements(By.TAG_NAME, "a")
        all_links = []
        internal_links = []
        for link in a_elements:
            href = link.get_attribute("href")
            if (link.get_attribute("href")):
                all_links.append(href)
                full_url = urljoin(url, href)
                link_domain = urlparse(full_url).netloc

                # 5. Check if it's an internal link (same domain)
                if link_domain == base_domain:
                    internal_links.append(full_url)

        driver.quit()
        len_int = len(internal_links)
        return len_int, len(all_links) - len_int, len(all_links)
    
    except requests.RequestException as e:
        print(f"Error fetching URL given {url}:{e}, try another url")
        return 0,0,0
    

def get_domain_age(domain):
    load_dotenv()
    api_key = os.getenv("WHOIS_API_KEY")
    url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

    params = {
        "apiKey" : api_key,
        "domainName": domain,
        "outputFormat": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        data = response.json()
        #print(data["estimatedDomainAge"])
        if "ErrorMessage" in data:
            print("WHOISAPI error ", data["ErrorMessage"])

        # Parse creation and expiration dates
        dom_age = data['WhoisRecord']['estimatedDomainAge']

        return dom_age if dom_age > 0 else -1

    except Exception as e:
        print(f"WHOIS API error: {e}")
        return None


def clean_url(domain):
    parsed = urlparse(domain)

    # Rebuild the URL without query and fragment
    clean = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '', '', ''  # no params, query, or fragment
    ))
    return clean

def get_google_index(domain):
    load_dotenv()
    api_key = os.getenv("SERPAPI_API_KEY")
    url = "https://serpapi.com/search"

    # cleaned_url = str(clean_url(domain))
    # print("cleaned Link ", cleaned_url)

    params = {
        "engine": "google",
        "q": f"site:{domain}",
        "api_key": api_key,
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print("SERPAPI error ", data.get("error"))

        # If there are organic results, the domain is indexed
        return 1 if bool(data.get("organic_results")) else 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 0

def run(url):
    print(phish_count(url))

## For Testing
if __name__ == "__main__":
    test_url = "http://www.crestonwood.com/router.php"
    test2 = "https://leetcode.com/urgent/loginbitcoin/invoice"
    run(test2)

def extract_features(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    # url = clean_url(url)
    ## Length of url
    lenUrl = length_url(url)

    ## Number of www
    countW = count_www(url)

    ## Longest word path
    longest_path = longest_word_path(url)

    ## Phish hints
    phish_hints = phish_count(url)

    ## number of hyperlinks (Need to scrape)
    num_hyperlinks = num_hyper(url)
    total_links = num_hyperlinks[2]

    ## Ratio intHyperLinks
    if total_links == 0:
        ratio_int = 0
    else:
        ratio_int = num_hyperlinks[1] / total_links

    ## domain_age (WHOISAPI)
    age = get_domain_age(url)

    ## google idx (SerpAPI)
    is_indexed = get_google_index(url)

    ##page rank

    features = [
        lenUrl,
        countW,
        longest_path,
        phish_hints,
        total_links,
        ratio_int,
        age,
        is_indexed
    ]

    features_np = np.array([features])
    return features_np


    




    