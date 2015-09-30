# Like post_tweet.py but doesn't actually post a tweet.  Just previews what the next tweet would be.

from credentials import BITLY_TOKEN

from bs4 import BeautifulSoup
import requests
import praw

import os
import shutil
import codecs

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL_IMG_FILE = SCRIPT_DIR + '\\reaction.gif'
RECENT_TWEETS_FILE = SCRIPT_DIR + '\\recent_tweets.dat'

GIF_SITE_URL = 'http://replygif.net/random'
MAX_GIF_SIZE = 3E6 # In Bytes

TWEET_BUFFER_LEN = 30
MAX_HEADLINE_LEN = 100
USER_AGENT = "Headline Gifs Twitter Account"

NUM_REDDIT_POSTS = 50

def get_recent_tweets():
    '''Return list of URLs to recently tweeted pets'''
    # Get recent tweets from local file if they exist
    if os.path.isfile(RECENT_TWEETS_FILE):
        with codecs.open(RECENT_TWEETS_FILE, 'r', 'utf-8') as f:
            recent_tweets = f.read().splitlines()
    else:
        recent_tweets = []

    return recent_tweets

def get_gif():
    res = requests.get(GIF_SITE_URL)
    soup = BeautifulSoup(res.text)
    gif_url = soup.find('img')['src'] + ".gif"
    
    res = requests.get(gif_url, stream=True)
    with open(LOCAL_IMG_FILE, 'wb') as f:
        shutil.copyfileobj(res.raw, f)

def main():
	'''Compose a tweet, but don't post it.'''

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
	for submission in submissions:
	    submission_list.append(submission)

	# Pick a headline (and URL) that is short and hasn't been tweeted recently
	recent_headlines = get_recent_tweets()
	for submission in submission_list:
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

	tweet_msg = cur_headline + ' ' + short_url

	print tweet_msg
	print "Tweet is {0} characters long".format(len(tweet_msg))
	
if __name__ == "__main__":
	main()