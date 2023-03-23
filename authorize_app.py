import settings
from mastodon import Mastodon

if __name__ == "__main__":
    Mastodon.create_app(
        settings.client_name,
        api_base_url=settings.mastodon_url,
        scopes=settings.scopes,
        redirect_uris=settings.redirect_uri,
        website=settings.bot_url,
        to_file=settings.clientcred_file,
    )

    mastodon = Mastodon(
        client_id=settings.clientcred_file, api_base_url=settings.mastodon_url
    )

    url = mastodon.auth_request_url(
        client_id=settings.clientcred_file,
        redirect_uris=settings.redirect_uri,
        scopes=settings.scopes,
    )

    print(f"Go to the following URL: {url}")
    authorization_code = input("Paste the authorization code here:").strip()

    access_token = mastodon.log_in(
        code=authorization_code, redirect_uri=settings.redirect_uri, scopes=["read"]
    )

    with open(".access.secret", "w") as f:
        f.write(access_token)

    print("Access token acquired")
