# e.g. Change this to an ngrok public URL
bot_url = "https://public-url.ngrok.io"  
 # Change this to your Maston instance.
mastodon_url = "https://neuromatch.social"
# Change this to your key location
open_ai_api_key_path = "/home/pmin/Documents/nma-match/.openai-key"

# This you probably don't need to change
client_name = "MastodonScraperBot"
redirect_uri = f"{bot_url}/callback"
clientcred_file = ".clientcred.secret"
scopes = ["read", "write"]