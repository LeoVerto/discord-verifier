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
from circleoftrust import analyze_circle_flair

logging.basicConfig(level=logging.INFO)


reddit = praw.Reddit(user_agent="ccKufi Discord Verifier (by /u/Leo_Verto)",
                     client_id=config.REDDIT_ID, client_secret=config.REDDIT_SECRET,
                     username=config.REDDIT_USER, password=config.REDDIT_PASS
                     )
logging.info("Logged into reddit as {}".format(reddit.user.me()))
post = reddit.submission(url=config.POST_URL)
cot = reddit.subreddit("CircleofTrust")

client = discord.Client()
verified_role = None


@client.event
async def on_ready():
    global verified_role

    logging.info("Logged in as: {}, ID: {}".format(client.user.name, client.user.id))

    for server in client.servers:
        for role in server.roles:
            if role.name == config.VERIFIED_ROLE:
                verified_role = role
                break

    if not verified_role:
        logging.error("Could not find verified role {}!".format(config.VERIFIED_ROLE))


@client.event
async def on_message(message):
    author = message.author
    name = get_disc_name(author)

    if message.channel.id == config.VERIFICATION_CHANNEL and message.content.startswith("!verify"):
        logging.debug("Verify started by {}".format(name))
        arguments = message.content.split(" ")

        if len(arguments) < 2:
            log("No URL from {}".format(name))
            await answer(message, "Please include the comment URL!")
            return

        raw_url = arguments[1]
        url = url_fix(raw_url)

        if not url.startswith(config.POST_URL):
            log("Invalid URL from {}".format(name))
            await answer(message, "Invalid URL!")
            return

        comment_id = Comment.id_from_url(url)
        logging.debug("Reading comment {}".format(comment_id))

        comment = get_comment(comment_id)
        comment_body = comment.body

        if comment_body is None:
            log("Comment {} does not exist".format(comment_id))
            await answer(message, "that comment does not exist!")
            return

        if comment_body == name:
            reddit_user = comment.author
            reddit_name = reddit_user.name

            # Check CoT submissions
            members, joined, betrayed = analyze_circle_flair(reddit, reddit_user, cot)

            if betrayed:
                log("Denied discord user {} (reddit {}), they have betrayed!".format(name, reddit_name))
                await answer(message, "you have betrayed {} times! Please wait for manual verification.".format(joined))
                return

            await client.change_nickname(author, "/u/{}".format(reddit_name))
            await client.add_roles(author, verified_role)
            log("Verified {}, member of {} circles".format(name, joined))
            await answer(message, "you have been successfully verified!")
        else:
            log("Comment does not just contain discord ID: {}".format(url))
            await answer(message, "that comment does not contain your discord ID!")

    return


async def answer(message, content):
    await client.send_message(message.channel, "{} {}".format(message.author.mention, content))


async def log(message):
    logging.info(message)
    await client.send_message(config.LOGGING_CHANNEL, message)


def get_disc_name(user):
    return "{}#{}".format(user.name, user.discriminator)


def get_comment(id):
    try:
        post.comments.replace_more(limit=0)
        for comment in post.comments:
            logging.debug(comment.id)
            if comment.id == id:
                return comment
        return None
    except (ResponseException, Forbidden, OAuthException) as e:
        logging.error(e)


client.run(config.DISCORD_TOKEN)
