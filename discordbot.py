#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import discord
import praw
from praw.models import Comment
from prawcore.exceptions import ResponseException, Forbidden, OAuthException
import asyncio
import config
from werkzeug.urls import url_fix

logging.basicConfig(level=logging.INFO)


reddit = praw.Reddit(user_agent="ccKufi Discord Verifier (by /u/Leo_Verto)",
                     client_id=config.REDDIT_ID, client_secret=config.REDDIT_SECRET,
                     username=config.REDDIT_USER, password=config.REDDIT_PASS
                     )
logging.info("Logged into reddit as {}".format(reddit.user.me()))
post = reddit.submission(url=config.POST_URL)

client = discord.Client()


@client.event
async def on_ready():
    logging.info("Logged in as: {}, ID: {}".format(client.user.name, client.user.id))


@client.event
async def on_message(message):
    author = message.author
    name = get_disc_name(author)

    if message.channel.id == config.VERIFICATION_CHANNEL and message.content.startswith("!verify"):
        logging.info("Verify started by {}".format(name))
        arguments = message.content.split(" ")

        if len(arguments) < 2:
            logging.info("No URL from {}".format(name))
            await answer(message, "Please include the comment URL!")
            return

        raw_url = arguments[1]
        url = url_fix(raw_url)

        if not url.startswith(config.POST_URL):
            logging.info("Invalid URL from {}".format(name))
            await answer(message, "Invalid URL!")
            return

        comment = Comment.id_from_url(url)
        logging.info("Reading comment {}".format(comment))

        comment_body = get_comment(comment)

        if comment_body is None:
            logging.info("Comment {} does not exist".format(comment))
            await answer(message, "that comment does not exist!")
            return

        if comment_body == name:
            # TODO: betrayal check
            logging.warning("Verified reddit user {}, discord ID {}".format("empty", name))
            await answer(message, "you have been successfully verified!")
        else:
            logging.info("Comment {} does not contain discord ID".format(comment))
            await answer(message, "that comment does not contain your discord ID!")

    return


async def answer(message, content):
    await client.send_message(message.channel, "{} {}".format(message.author.mention, content))


def get_disc_name(user):
    return "{}#{}".format(user.name, user.discriminator)


def get_comment(id):
    try:
        post.comments.replace_more(limit=0)
        for comment in post.comments:
            logging.debug(comment.id)
            if comment.id == id:
                return comment.body
        return None
    except (ResponseException, Forbidden, OAuthException) as e:
        logging.error(e)


client.run(config.DISCORD_TOKEN)
