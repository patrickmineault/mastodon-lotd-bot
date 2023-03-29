import json
import logging
import time

import openai
import settings
import tqdm
from mastodon import Mastodon

openai.api_key_path = settings.open_ai_api_key_path


def get_formatted_toots(lotd):
    toots = []
    for link in lotd:
        accounts = ["@" + x["account"]["username"] for x in link["backlinks"]]
        if len(accounts) == 1:
            accounts = accounts[0]
        elif len(accounts) > 3:
            accounts = ", ".join(accounts[:3]) + f" and {len(accounts) - 3} others"
        else:
            accounts = ", ".join(accounts[:-1]) + f" and {accounts[-1]}"
        tags = ["#lotd"]
        if link["is_scientific_article"]:
            tags.append("#science")
        if link["is_news"]:
            tags.append("#news")
        tags = " ".join(tags)

        content = f"""
<h1><a href='{link['url']}'>{link['title']} - {link['website']}</a></h1>
<h2>TL;DR {link['tldr']}</h2>
<p>Linked by {accounts} ({link['popularity']}⭐)</p>
<p>{link['summary']}</p>
<p>{tags}</p>
"""

        toots.append(content)
    return toots

def summarize_together(links):
    summaries = [link["tldr"] for link in links]
    all_together = "\n".join(summaries)

    model = 'gpt-4'
    prompt = f"""
Summarize in three short statements (max 15 words total, separated by a comma) the themes of the following summaries.
You don't have to cover all the summaries, but you should cover the themes of at least 3 of them. 
If things are mentioned multiple times, you can mention them once. Make it short and sweet, enticing but not clickbait-y.

{all_together}
"""

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
            return content
        except (openai.error.APIError, openai.error.RateLimitError) as e:
            logger.warning(e)
            logger.warning(f"Failed to get response from model {model}")
        
        logger.warning(f"Retrying in {delay} s")
        time.sleep(delay)

logging.basicConfig(level=logging.INFO)

# Create the logger
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    with open(".access.secret", "r") as f:
        access_token = f.read()

    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=settings.mastodon_url
    )

    date_str = time.strftime("%Y-%m-%d", time.localtime())
    with open(f"cache/lotd-{date_str}.json", "r") as f:
        lotd = json.load(f)

    # Generate summaries of summaries.
    logger.info("Summarizing summaries...")
    global_summary = summarize_together(lotd)

    toots_formatted = get_formatted_toots(lotd)

    first_str = f'<h1>🎉 Today\'s most popular links</h1><h2>{global_summary}</h2><p>{date_str} edition</p>'
    first_toot = mastodon.status_post(first_str)
    first_toot_id = first_toot["id"]

    with open('cache/first_toot_id.txt', 'w') as f:
        f.write(str(first_toot_id))

    for toot in tqdm.tqdm(toots_formatted):
        mastodon.status_post(
            toot,
            in_reply_to_id=first_toot_id,
            visibility='unlisted'
        )
        time.sleep(1)
