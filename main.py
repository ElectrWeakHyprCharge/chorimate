#!/usr/bin/env python
#! -*- coding: utf-8 -*-

from unicodedata import normalize
from typing import Dict, Optional
from traceback import print_exc
from random import choice
from time import sleep
from os import path
import json
import re

from praw.models import Comment
import praw


reddit = praw.Reddit('chorimate')
sub = reddit.subreddit('uruguay+rou')
with open('data.json', 'r') as f:
    userdata = json.load(f)


def load_images(from_path: str, path_prefix: Optional[str]=None):
    filepath = path.join(
        path_prefix or path.dirname(path.abspath(__file__)),
        from_path
    )

    with open(filepath, 'r') as f:
        return [link[1:] for link in f.read().splitlines()
                if link.startswith('#')]


COMMANDS = {
    # Command: (reward, reward_images)
    '!redditchoripan': ('choripán', load_images('img/choripan')),
    '!tomateunmate':   ('mate',     load_images('img/mate'))
}

PATTERN = re.compile(
    '(%s)(?: /?u/([a-z_-]{3,20}))?' % '|'.join(COMMANDS.keys())
)


def match_commands(comment: Comment, accents=True) -> set:
    """
    Return a set with tuples of the form ((reward, reward_images), recipient),
    one for each match in the body of the provided comment.
    """
    if not accents:
        content = normalize('NFD', comment.body).encode('ascii', 'ignore')
        content = content.decode('ascii')

    return {
        (COMMANDS[m.group(1)], m.group(2) or comment.parent().author)
        for m in PATTERN.finditer(content)
    } 


def reply(comment, recipient, sender, times_received, reward, images, retries=5) -> None:
    msg =(
        f'#[Aquí está tu {reward}, /u/{recipient}!]'
        f'({choice(images)} "{reward}")\n\n'
        f'/u/{recipient} recibió {reward} {times_received} '
        f'{"vez" if times_received == 1 else "veces"}.'
        f'(dado por /u/{sender})'
    )

    for _ in range(retries):
        try:
            comment.reply(msg)
            print('Reply:')
            print(msg.replace('\n', '\n | '))
        except Exception as e:
            print('Reply error')
            print_exc()
            print('Retrying in 5 seconds...')
            sleep(5)
        else:
            break


def is_valid_command(comment: Comment) -> bool:
    print('Reading:', comment.permalink)
    matches = match_commands(comment, accents=False)

    if not matches: return False
        
    print('Matches:',  matches) 
    for command, user in matches:
        reward, reward_images = COMMANDS[command]

        user_cf = user.casefold()
        userdata[reward][user_cf] = userdata[reward].get(user_cf, 0) + 1
        
        reply(
            comment,
            user,
            comment.author.name,
            userdata[reward][user_cf],
            reward, reward_images
        )
        sleep(1)
    return True


def main():
    for comment in sub.stream.comments():
        if comment.saved: continue
        
        if is_valid_command(comment):
            comment.save()
            with open('data.json', 'w') as f:
                json.dump(userdata, f)
                

if __name__ == '__main__':
    print('Start')

    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except Exception as e:
            msg = 'UNCATCHED EXCEPTION: '
            print_exc()
            print('RETRYING')
            sleep(5)


