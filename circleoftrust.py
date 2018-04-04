# -*- coding: utf-8 -*-
import praw
import prawcore

SAFE_REDDITOR = 'rodly'         # Owner of the reddit admins circle

def get_circle_post(reddit, redditor, subreddit, double_check=True):
    url = '/user/%s/circle' % (redditor.name,)
    try:
        reddit.get(url)
    except prawcore.exceptions.Redirect as exc:
        post = praw.models.Submission(reddit,
                                      url=exc.response.headers['Location'])
        assert post.subreddit == subreddit
        return post
    except prawcore.exceptions.NotFound as exc:
        # Confirm that circles haven't been taken offline by checking
        # that a known participating user is resolving (be careful to
        # only recurse one level)
        if double_check and \
           not get_circle_post(reddit, reddit.redditor(SAFE_REDDITOR),
                               subreddit, double_check=False):
            raise           # Raise as an actual error: circle is down
        return None

def get_circle_comment(reddit, redditor, subreddit, limit=100):
    for comment in redditor.comments.new(limit=limit):
        if comment.subreddit != subreddit:
            continue
        return comment
    else:
        return None

def get_circle_flair(reddit, redditor, subreddit):
    thing = get_circle_post(reddit, redditor, subreddit) or \
            get_circle_comment(reddit, redditor, subreddit)
    if not thing:
        return None
    return thing.author_flair_text

def check_betrayal(reddit, subreddit, redditor):
    flair = get_circle_flair(reddit, subreddit, redditor)

    if flair:
        return analyze_flair(flair)

    return None


# https://github.com/albertwujj/CircleOfTrust/blob/master/GetCircles.py
def analyze_flair(flair):
    flair = flair.replace(",", "")
    flair = flair.strip()
    flair_arr = flair.split(' ')
    return int(flair_arr[0]), int(flair_arr[1]), len(flair_arr) > 2

def _test():
    import config, sys
    reddit = praw.Reddit(
        user_agent="ccKufi Discord Verifier (by /u/Leo_Verto)",
        client_id=config.REDDIT_ID, client_secret=config.REDDIT_SECRET,
        username=config.REDDIT_USER, password=config.REDDIT_PASS
    )
    subreddit = reddit.subreddit('CircleofTrust')
    usernames = sys.argv[1:] if len(sys.argv) > 1 else ('Leo_Verto', 'orbilo')
    for username in usernames:
        user = reddit.redditor(username)
        print(user, check_betrayal(reddit, user, subreddit))

if __name__ == '__main__':
    _test()
