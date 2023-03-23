import collections
from datetime import datetime, timedelta
import json
import logging
import pytz
import re
import requests
import settings
import time
import tqdm

from mastodon import Mastodon
from bs4 import BeautifulSoup, Comment, NavigableString
import openai

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

# Configure the logger
logging.basicConfig(level=logging.INFO)

# Create the logger
logger = logging.getLogger(__name__)

openai.api_key_path = settings.open_ai_api_key_path


def resolve_doi(url):
    """Resolve DOI to URL, otherwise two people can link to the same resource 
    and it would count them as separate."""
    if 'doi.org' in url:
        response = requests.get(url, headers={'Accept': 'application/json'})
        if response.status_code == 200:
            links = response.json()['link']
            for link in links:
                if link['content-type'] == 'text/html':
                    return link['URL']
    
    return url


def truncate_paragraph(paragraph, max_words=1000):
    # Split the paragraph into words using a regular expression, including <> tags
    words = re.findall(r'\b\w+\b|[<>]', paragraph)

    words = [x.strip() for x in words if x.strip()]

    # Count the number of words
    word_count = len(words)

    # Truncate the paragraph if it contains more than 1000 words
    if word_count > max_words:
        words = words[:max_words]
        total_len = sum([len(x) for x in words])
        total_len += len(words) - 1

        if total_len < len(paragraph):
            idx = paragraph[total_len:].find(' ')
         
            return paragraph[:(total_len + idx)] + '...'
    return paragraph

def fetch_toots_from_last_day(mastodon):
    # Initialize variables for pagination
    toots = []
    max_id = None
    one_day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    while True:
        fetched_toots = mastodon.timeline_local(limit=None, max_id=max_id)

        # Break the loop if no more toots are fetched
        if not fetched_toots:
            break

        # Filter toots from the last day
        recent_dates = [toot["created_at"] for toot in fetched_toots]
        recent_toots = [
            toot for toot in fetched_toots if toot["created_at"] > one_day_ago
        ]

        # Add the recent toots to the list
        toots.extend(recent_toots)

        # Break the loop if the last fetched toot is older than one day
        if len(recent_toots) < len(fetched_toots):
            break

        # Update the max_id for the next request
        max_id = fetched_toots[-1]["id"]

        # Sleep for a short duration to avoid rate-limiting
        time.sleep(1)

    return toots


def extract_links(html_string):
    # Parse the HTML string with BeautifulSoup
    soup = BeautifulSoup(html_string, "html.parser")

    # Find all the <a> tags
    a_tags = soup.find_all("a")

    # Extract the 'href' attribute from each <a> tag and return the list of links
    links = [a.get("href") for a in a_tags]
    return links


def remove_attrs(soup, attrs):
    for attr in attrs:
        for tag in soup.find_all(attrs={attr: True}):
            del tag[attr]
    return soup


def remove_tags(soup, tags):
    for tag in tags:
        for match in soup.find_all(tag):
            match.decompose()
    return soup


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)


def get_url_via_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)

    # Wait for the articles to load
    class DocumentReadyStateCondition:
        def __call__(self, driver):
            ready_state = driver.execute_script("return document.readyState")
            return ready_state == "complete"

    # Set the maximum waiting time (in seconds) until document.readyState == "complete"
    timeout = 10

    try:
        # Wait until the document.readyState is "complete"
        WebDriverWait(driver, timeout).until(DocumentReadyStateCondition())
        logger.info("Webpage loaded through Selenium successfully")
    except TimeoutError:
        logger.info("Timed out waiting for page to load")

    time.sleep(10)

    # page_title = driver.execute_script("return document.head.innerHTML;")
    # body_text = driver.execute_script("return document.body.innerHTML;")
    return driver.execute_script("return document.documentElement.outerHTML")


def fetch_webpage_data(url):
    if "psyarxiv" in url or "linkinghub" in url:
        # Dreaded javacript nonsense from psyarxiv and elsevier
        html_content = get_url_via_selenium(url)
    else:
        # A mercifully non-javascript webpage.
        response = requests.get(url)
        html_content = response.text

    parsed_content = extract_content(html_content)
    return {"url": url, **parsed_content}


def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.text.strip() if title_tag else ""

    # Remove all non-content tags
    remove_tags(
        soup,
        [
            "link",
            "style",
            "script",
            "noscript",
            "iframe",
            "img",
            "picture",
            "svg",
            "math",  # MathJax
            "form",
            "input",
            "header",
            "footer",
            "nav",
            "ul",  # Often used for navigation
            "ol",
        ],
    )

    # Remove all comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    for comment in comments:
        comment.extract()

    # Remove attributes which start with 'data-' or 'aria-'
    for element in soup():
        # Loop through the element's attributes
        for attr in list(element.attrs.keys()):
            if attr.startswith("data-") or attr.startswith("aria-"):
                # Remove the attribute
                del element.attrs[attr]

    # Find all elements with a useless attribute
    remove_attrs(soup, ["class", "style", "onclick", "id"])

    for text_node in soup.find_all(string=True):
        if isinstance(text_node, NavigableString):
            # Replace extra whitespaces
            new_text = " ".join(text_node.split())
            text_node.replace_with(new_text)

    # Remove empty tags
    for tag in soup.find_all():
        if not tag.contents:
            tag.extract()

    # Unwrap deeply nested tags
    for div in soup.find_all("div"):
        div.unwrap()

    main_tag = soup.find("main")
    if main_tag:
        body = "".join([str(x) for x in main_tag.contents])
    else:
        body_tag = soup.find("body")
        body = "".join([str(x) for x in body_tag.contents]) if body_tag else ""

    webpage_data = {
        "title": title,
        "body": body,
    }

    return webpage_data


def summarize_webpage(contents):
    prompt = f"""
"Below is a webpage summary, including the URL, <title>, and <body>. Return a 
json string with the following keys: 

`website`: the name of the host website (e.g. "NYTimes", "arXiv", etc.)
`title`: a good title for the website (not necessarily the content of <title>)
`is_scientific_article`: bool, whether the article is a scientific article (e.g. if it's on a preprint server, on nature.com, etc.)
`is_news`: bool, whether the article is a news article, or from a blog, etc.
`summary`: an abstract/summary for the webpage. Can be copied verbatim from the webpage if it's a news article or a scientific article). 
`tldr`: a two-sentence summary of the summary

The website:
----------------
url: {contents['url']}
title: {contents['title']}
body: {truncate_paragraph(contents['body'])}
"""
    for model in ['gpt-3.5-turbo', 'gpt-4']:
        # GPT-4 is slower but it almost always returns good results.
        for delay in [1, 2, 4, 8, 16, 32, 64, 128]:
            logger.info(f"Trying model {model}")
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. You always follow instructions."},
                        {"role": "user", "content": prompt},
                    ],
                )
                content = response["choices"][0]["message"]["content"]
                break
            except (openai.error.APIError, openai.error.RateLimitError):
                logger.warn(f"Failed to get response from model {model}")
                
            logger.warn(f"Timed out waiting for {model}, retrying in {delay} seconds.")
            time.sleep(delay)

        try:
            r = json.loads(content)
            return r
        except json.decoder.JSONDecodeError:
            logger.warn(f"Failed to parse JSON with model {model}")
            continue


def main():
    with open(".access.secret", "r") as f:
        access_token = f.read()

    # Initialize Mastodon instance
    mastodon = Mastodon(access_token=access_token, api_base_url=settings.mastodon_url)

    logger.info("Fetching toots from last 24 hours")

    # Time window: last 24 hours
    toots = fetch_toots_from_last_day(mastodon)
    toots = [toot for toot in toots if (
        toot['visibility'] == "public") and ('#nobot' not in toot['account']['note'])]
    logger.info(f"Analyzing {len(toots)} toots...")

    with open("cache/toots.json", "w") as f:
        json.dump(toots, f, cls=DateTimeEncoder)

    # Figure out which links are the most popular
    logger.info("Finding popular links...")
    popularity = collections.defaultdict(int)
    backlinks = collections.defaultdict(list)
    for toot in toots:
        # Find links in toot content
        links = set([resolve_doi(x) for x in extract_links(toot.content) if not x.endswith(".pdf")])

        # Start with arxiv links
        links = sorted(links, key=lambda x: "rxiv" not in x)

        for link in links:
            # Remove tags or links to Mastodon profiles
            if link.startswith(settings.mastodon_url) or "/@" in link:
                continue
            popularity[link] += toot.favourites_count + toot.reblogs_count
            backlinks[link].append(toot)

            if "rxiv" in link:
                # Prevents double-counting when a preprint and its published
                # version are both linked.
                break

    popular_links = sorted(popularity.items(), key=lambda x: x[1], reverse=True)

    logger.info("Most popular links:")
    logger.info(popular_links[:10])

    # Now fetch the content for each of these popular links and summarize
    lotd = []
    logger.info("Summarizing webpages...")
    for link, _ in tqdm.tqdm(popular_links[:10]):
        if popularity[link] < 1:
            continue

        webpage_data = fetch_webpage_data(link)
        summary = summarize_webpage(webpage_data)

        lotd.append(
            {
                **webpage_data,
                **summary,
                "backlinks": backlinks[link],
                "popularity": popularity[link],
            }
        )

    # Dump to disk
    with open("cache/lotd.json", "w") as f:
        json.dump(lotd, f, cls=DateTimeEncoder)


if __name__ == "__main__":
    # Find the most popular links in the toots
    main()
