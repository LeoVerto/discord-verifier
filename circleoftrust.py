# -*- coding: utf-8 -*-


def check_betrayal(reddit, subreddit, redditor):
    flair = reddit.flair(subreddit, redditor)

    if flair:
        return analyze_flair(flair)

    return None


# https://github.com/albertwujj/CircleOfTrust/blob/master/GetCircles.py
def analyze_flair(flair):
    flair = flair.replace(",", "")
    flair = flair.strip()
    flair_arr = flair.split(' ')
    return int(flair_arr[0]), int(flair_arr[1]), len(flair_arr) > 2
