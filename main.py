#!/usr/bin/env python
#! -*- coding: utf-8 -*-

from unicodedata import normalize
from traceback import print_exc
from random import choice
from time import sleep
import re

from praw.models import Comment
import praw

import load

reddit = praw.Reddit('chorimate')  # Credentials found in praw.ini
sub = reddit.subreddit('uruguay+rou')
userdata = load.userdata()
commands = load.commands()


PATTERN = re.compile(
    r'(?<!\\)(%s)(?: /?u/([a-z_-]{3,20}))?' % '|'.join(commands.keys()),
    re.IGNORECASE
)


def remove_accents(string: str) -> str:
    return normalize('NFD', string).encode('ascii', 'ignore').decode('ascii')


def match_commands(comment: Comment, accents=True) -> set:
    """
    Return a set with tuples of the form ((reward, reward_images), recipient),
    one for each match in the body of the provided comment.
    """
    if accents:
        content = comment.body
    else:
        content = remove_accents(comment.body)

    return {
        (commands[m.group(1)].lower(), m.group(2) or comment.parent().author.name)
        for m in PATTERN.finditer(content)
    }


def reply(comment: Comment,
          recipient: str,
          sender: str,
          times_received: int,
          reward: str,
          image: str,
          retries: int = 5) -> None:
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
            load.save(userdata)


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
