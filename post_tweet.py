from credentials import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BITLY_TOKEN

from bs4 import BeautifulSoup
import requests
import tweepy
import praw

import os
import shutil
import codecs

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL_IMG_FILE = SCRIPT_DIR + '\\reaction.gif'
RECENT_TWEETS_FILE = SCRIPT_DIR + '\\recent_tweets.dat'

print LOCAL_IMG_FILE

GIF_SITE_URL = 'http://replygif.net/random'
MAX_GIF_SIZE = 3E6 # In Bytes

TWEET_BUFFER_LEN = 30
MAX_HEADLINE_LEN = 95
USER_AGENT = "Headline Gifs Twitter Account"

NUM_REDDIT_POSTS = 50

MAX_TWEET_ATTEMPTS = 3

class TwitterAPI(object):

    def __init__(self): 
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth)
    
    def tweet(self, message):
        self.api.update_status(status=message)

    def tweet_with_img(self, img_path, msg):
        self.api.update_with_media(filename=img_path, status=msg)

def get_recent_tweets():
    '''Return list of URLs to recently tweeted pets'''
    # Get recent tweets from local file if they exist
    if os.path.isfile(RECENT_TWEETS_FILE):
        with codecs.open(RECENT_TWEETS_FILE, 'r', 'utf-8') as f:
            recent_tweets = f.read().splitlines()
    else:
        recent_tweets = []

    return recent_tweets

def update_recent_tweets(new_item):
    '''Write profile URL to list of recent tweets'''       
    recent_tweets = get_recent_tweets()
    recent_tweets.append(new_item)

    while len(recent_tweets) > TWEET_BUFFER_LEN:
        recent_tweets.pop(0)

    with codecs.open(RECENT_TWEETS_FILE, 'w', 'utf-8') as f:
        for item in recent_tweets:
            f.write(item + u'\n')

def get_gif():
    res = requests.get(GIF_SITE_URL)
    soup = BeautifulSoup(res.text)
    gif_url = soup.find('img')['src'] + ".gif"
    
    res = requests.get(gif_url, stream=True)
    with open(LOCAL_IMG_FILE, 'wb') as f:
        shutil.copyfileobj(res.raw, f)

def main():
	# Get a gif
	get_gif()
	gif_size = os.path.getsize(LOCAL_IMG_FILE)
	
	# Ensure gif is of appropriate size
	while gif_size > MAX_GIF_SIZE:
		get_gif()
		gif_size = os.path.getsize(LOCAL_IMG_FILE)

	# Get reddit posts
	submission_list = []
	r = praw.Reddit(user_agent=USER_AGENT)
	submissions = r.get_subreddit('news').get_top(limit=NUM_REDDIT_POSTS)
	
	# Convert list of submissions to list (currently generator)
	for submission in submissions:
	    submission_list.append(submission)

	recent_headlines = get_recent_tweets()

	tweet_posted = False
	num_attempts = 0

	while (not tweet_posted) and (num_attempts < MAX_TWEET_ATTEMPTS):
		num_attempts += 1

		try:

			# Pick a headline (and URL) that is short and hasn't been tweeted recently
			while submission_list:

				submission = submission_list.pop(0)
				headline = submission.title
				if (len(headline) < MAX_HEADLINE_LEN) and (headline not in recent_headlines):
					cur_headline = headline
					headline_url = submission.url
					break

			# Shorten URL with bit.ly
			shorten_url = 'https://api-ssl.bitly.com/v3/shorten'
			payload = {'access_token': BITLY_TOKEN, 'longUrl': headline_url, 'domain':'bit.ly'}
			res = requests.get(shorten_url, params = payload)
			short_url = res.json()['data']['url']

			# Compose and post tweet
			twitter = TwitterAPI()

			tweet_msg = cur_headline + ' ' + short_url
			twitter.tweet_with_img(LOCAL_IMG_FILE, tweet_msg)
			tweet_posted = True

		except:
			print("Tweet failed. Getting next headline.")


	if tweet_posted:
		print tweet_msg
		update_recent_tweets(cur_headline)




if __name__ == "__main__":
	main()