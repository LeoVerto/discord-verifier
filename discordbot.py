#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
import discord
import praw
from praw.models import Comment, Redditor
from prawcore.exceptions import ResponseException, Forbidden, OAuthException
import asyncio
import config
from werkzeug.urls import url_fix
from circleoftrust import analyze_circle_flair

logging.basicConfig(level=logging.INFO)

reddit_blacklist = config.REDDIT_BLACKLIST.split(", ")
discord_blacklist = config.DISCORD_BLACKLIST.split(", ")

reddit = praw.Reddit(user_agent="ccKufi Discord Verifier (by /u/Leo_Verto)",
                     client_id=config.REDDIT_ID, client_secret=config.REDDIT_SECRET,
                     username=config.REDDIT_USER, password=config.REDDIT_PASS
                     )
logging.info("Logged into reddit as {}".format(reddit.user.me()))
post = reddit.submission(url=config.POST_URL)
cot = reddit.subreddit("CircleofTrust")

client = discord.Client()
verified_role = None
logging_channel = None


@client.event
async def on_ready():
    global verified_role, logging_channel

    logging.info("Logged in as: {}, ID: {}".format(client.user.name, client.user.id))

    for server in client.servers:
        for role in server.roles:
            if role.name == config.VERIFIED_ROLE:
                verified_role = role
                break

    if not verified_role:
        logging.error("Could not find verified role {}!".format(config.VERIFIED_ROLE))

    logging_channel = client.get_channel(config.LOGGING_CHANNEL)

    if not logging_channel:
        logging.error("Could not find logging channel {}!".format(config.LOGGING_CHANNEL))


@client.event
async def on_message(message):
    server = message.server
    author = message.author
    name = get_disc_name(author)

    if message.channel.id == config.VERIFICATION_CHANNEL and message.content.startswith("!verify"):
        logging.debug("Verify started by {}".format(name))
        arguments = message.content.split(" ")

        if len(arguments) < 2:
            await log("No URL from %user%", author)
            await answer(message, "Usage: !verify <cckufi comment url>")
            return

        if name in discord_blacklist:
            await log("Blacklisted discord user %user% just tried to register!", author)
            await answer(message, "Invalid URL!")
            return

        raw_url = arguments[1]
        url = url_fix(raw_url)

        if not url.startswith(config.POST_URL):
            await log("Invalid URL from %user%", author)
            await answer(message, "Invalid URL!")
            return

        comment_id = Comment.id_from_url(url)
        logging.debug("Reading comment {}".format(comment_id))

        comment = get_comment(comment_id)

        if comment is None:
            await log("User %user% linked comment {} which does not exist".format(comment_id), author)
            await answer(message, "that comment does not exist!")
            return

        reddit_user = comment.author
        reddit_name = reddit_user.name

        if reddit_name in reddit_blacklist:
            await log("Blacklisted reddit user {} (discord %user%) just tried to register!".format(reddit_name), author)
            await answer(message, "that comment does not just contain your discord ID!")
            return

        comment_body = comment.body

        if comment_body.startswith(name):

            # Check CoT submissions
            members, joined, betrayed = analyze_circle_flair(reddit, reddit_user, cot)

            if not members:
                await log("Denied discord user %user% (reddit {}), they haven't posted on CoT".format(reddit_name), author)
                await answer(message, "you must have posted or commented on /r/CircleofTrust to be verified.")
                return

            if betrayed:
                await log("Denied discord user %user% (reddit {}), they have betrayed!".format(reddit_name), author)
                await answer(message, "you have betrayed {} times! Please ask for manual verification.".format(joined))
                return

            await client.change_nickname(author, "/u/{}".format(reddit_name))
            await client.add_roles(author, verified_role)
            await log("Verified %user%, member of {} circles".format(joined), author)
            await answer(message, "you have been successfully verified!")
        else:
            await log("Comment does not start with their discord ID: {}, got '{}' instead.".format(url, comment_body))
            await answer(message, "that comment does not start with your discord ID!")

    elif message.content.startswith("!flair"):
        logging.debug("Circle command ran by {}".format(name))

        arguments = message.content.split(" ")

        if len(arguments) < 2:
            await answer(message, "Usage !circles <reddit user>")
            return

        logging.info(arguments[1])

        reddit_name = arguments[1]

        # Check for discord mentions
        discord_id = re.search(r"<@!(\d{17})>", arguments[1])

        if discord_id:
            discord_user = server.get_member(discord_id.group(1))
            logging.info(discord_user)
            if discord_user:
                reddit_name = discord_user.name
                logging.info(reddit_name)

        reddit_name = re.sub(r"(@?/?u/)", "", reddit_name)
        reddit_user = Redditor(reddit, name=reddit_name)

        members, joined, betrayed = analyze_circle_flair(reddit, reddit_user, cot)

        if not members:
            await log("Lookup by %user% for {} failed, they haven't posted on CoT".format(reddit_name), author)
            await answer(message, "that user has not posted on /r/CircleofTrust.")
            return

        await log("Lookup by %user% for {}.".format(reddit_name), author)
        await answer(message, "Users in circle: {}, member of circles: {}".format(members, joined)
                              + (" BETRAYER!" if betrayed else ""))
    return


async def answer(message, content):
    await client.send_message(message.channel, "{} {}".format(message.author.mention, content))


async def log(message, user=None):
    if user:
        log_msg = message.replace("%user%", get_disc_name(user))
        discord_msg = message.replace("%user%", user.mention)
    else:
        log_msg = message
        discord_msg = message

    logging.info(log_msg)
    await client.send_message(logging_channel, discord_msg)


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
