#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import discord
import praw
from praw.models import Comment
import asyncio
import config
from werkzeug.urls import url_fix, url_join

logging.basicConfig(level=logging.INFO)


reddit = praw.Reddit(user_agent="ccKufi Discord verification bot (by /u/leo_verto)",
                     client_id=config.REDDIT_ID, client_secret=config.REDDIT_SECRET)
post = reddit.submission(url=config.POST_URL)
client = discord.Client()


@client.event
async def on_ready():
    logging.info("Logged in as: {}, ID: {}".format(client.user.name, client.user.id))


@client.event
async def on_message(message):
    author = message.author

    if message.channel.n message.content.startswith("!verify"):
        logging.debug("Verify started by {}".format(author.user.id))
        raw_url = message.split(" ")[1]
        url = url_fix(raw_url)

        if url.startswith(config.POST_URL):
            comment = Comment.id_from_url(url)
            logging.debug("Reading comment {}".format(comment))

            comment_body = get_comment(comment)
            if comment_body == author.id:
                # TODO: betrayal check
                logging.info("Verified reddit user {}, discord ID {}")
            elif comment_body is None:
                logging.debug("Comment {} does not exist".format(comment))
                await client.send(message.channel, "@{} that comment does not exist!".format(author.id.name))
            else:
                logging.debug("Comment did not contain discord ID")
                await client.send(message.channel, "@{} the comment does not contain your discord ID!".format(author.id.name))

        else:
            logging.debug("Invalid URL from {}".format(author.id))
            await client.send_message(message.channel, "@{} Invalid URL!".format(author.id.name))
            return


def get_comment(id):
    post.comments.replace_more(limit=0)
    for comment in post.comments:
        if comment.id == id:
            return comment.body
        return None


client.run(config.DISCORD_TOKEN)
