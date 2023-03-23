import json
import time
import settings
import tqdm
from mastodon import Mastodon


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

if __name__ == "__main__":
    with open(".access.secret", "r") as f:
        access_token = f.read()

    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=settings.mastodon_url
    )

    with open("cache/lotd.json", "r") as f:
        lotd = json.load(f)

    toots_formatted = get_formatted_toots(lotd)

    for toot in tqdm.tqdm(toots_formatted):
        mastodon.status_post(toot)
        time.sleep(1)
