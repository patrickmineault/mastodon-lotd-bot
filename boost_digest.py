from mastodon import Mastodon
import settings


if __name__ == "__main__":
    with open(".access.secret", "r") as f:
        access_token = f.read()

    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=settings.mastodon_url
    )

    with open('cache/first_toot_id.txt', 'r') as f:
        first_toot_id = int(f.read())

    mastodon.status_reblog(first_toot_id)