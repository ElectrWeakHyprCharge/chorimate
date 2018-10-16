#!/usr/bin/env python
#! -*- coding: utf-8 -*-

from unicodedata import normalize
from typing import Tuple, Optional
from traceback import print_exc
from random import choice
from time import sleep
from os import path
import json
import re

from praw.models import Comment
import praw


reddit = praw.Reddit('chorimate')
sub = reddit.subreddit('uruguay+rou+argentina')
with open('data.json', 'r') as f:
    userdata = json.load(f)


def load_images(from_path: str, path_prefix: Optional[str]=None) -> Tuple[str]:
    """
    Load a tuple of image links from the file at path_prefix + from_path.
    path_prefix is by default where the script is located
    """
    filepath = path.join(
        path_prefix or path.dirname(path.abspath(__file__)),
        from_path
    )

    with open(filepath, 'r') as f:
        return tuple([link[1:] for link in f.read().splitlines()
                      if link.startswith('#')])


COMMANDS = {
    # Command: (reward, reward_images)
    '!redditchoripan': ('choripán', load_images('img/choripan')),
    '!tomateunmate':   ('mate',     load_images('img/mate')),

    '!redditchivito': ('chivito', load_images('img/chivito')),
    # Capaz que algún día implemento estos:
    # '!redditempanada': ('empanada', load_images('img/empanada')),
    # '!reddit(?:milanesa|milanga)': ('milanesa', load_images('img/milanesa')),
}

PATTERN = re.compile(
    r'(?<!\\)(%s)(?: /?u/([a-z_-]{3,20}))?' % '|'.join(COMMANDS.keys()),
    re.IGNORECASE
)


def match_commands(comment: Comment, accents=True) -> set:
    """
    Return a set with tuples of the form ((reward, reward_images), recipient),
    one for each match in the body of the provided comment.
    """
    content = comment.body
    if accents is False:
        content = normalize('NFD', content).encode('ascii', 'ignore')
        content = content.decode('ascii')

    return {
        (COMMANDS[m.group(1)], m.group(2) or comment.parent().author.name)
        for m in PATTERN.finditer(content)
    }


def reply(comment: Comment,
          recipient: str,
          sender: str,
          times_received: int,
          reward: str,
          image: str,
          retries: str = 5) -> None:
    msg = (
        f'#[Aquí está tu {reward}, /u/{recipient}!]({image} "{reward}")\n\n'
        f'/u/{recipient} recibió {reward} {times_received} '
        f'{"vez" if times_received == 1 else "veces"}. '
        f'(dado por /u/{sender})  \n'
        '[^^¿Qué ^^es ^^esto?](https://github.com/ElectrWeakHyprCharge/'
        'chorimate/blob/master/Ayuda.md)'
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

    if not matches:
        return False

    print('Matches:',  matches)
    for command, user in matches:
        reward, reward_images = command

        usercf = user.casefold()
        if not userdata.get(reward, {}):
            userdata[reward] = {}
        userdata[reward][usercf] = userdata[reward].get(usercf, 0) + 1

        reply(
            comment=comment,
            recipient=user,
            sender=comment.author.name,
            times_received=userdata[reward][usercf],
            reward=reward,
            image=choice(reward_images)
        )
        sleep(1)
    return True


def main() -> None:
    for comment in sub.stream.comments():
        if comment.saved:
            continue

        if is_valid_command(comment):
            comment.save()
            with open('data.json', 'w') as f:
                json.dump(userdata, f)


if __name__ == '__main__':
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except Exception as e:
            msg = 'Uncatched exception: '
            print_exc()
            print('Retrying')
            sleep(5)

