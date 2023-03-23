# Mastodon top articles

Simple bot that posts top articles linked from Mastodon. Similar in scope to Twitter's 
Top Articles feature. [See here for an example of the output](https://neuromatch.social/@lotd).

## One-time setup

Create a conda env and install requirements.txt inside of it.

Bot requires to got through an OAuth sequence. Use [ngrok](https://ngrok.io) to 
create a tunnel to your local machine, e.g. `ngrok http 5000`. 

* Set the correct setting for the ngrok URL in `settings.py`
* Run `python oauth_server.py` to start the OAuth server loop
* Run `python authorize_app.py` to authorize the app

Note that your Mastodon account needs to:

* Be identified as a bot
* Have HTML enabled in the settings (go to `Preferences > Other > Default format for toots > HTML`)

## Retrieve top articles and post to Mastodon

* Set the various settings in `settings.py`. You will need an OpenAI API key
* `python get_toots.py` grabs the hottest toots from the last 24 hours and summarizes them using GPT3.5/GPT-4
* `python post_toots.py` posts the toots to Mastodon

## Cron

To set the bot to run automatically at 8AM, add this entry to your crontab (default location: `/etc/crontab`):

```
0 8 * * * cd /path/to && ./get_and_post.sh
```

Edit get_and_post.sh to use the correct conda environment. Make sure to `chmod +x get_and_post.sh` to make it executable.