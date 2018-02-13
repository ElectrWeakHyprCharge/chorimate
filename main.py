#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import praw, pickle, re
from random import choice
import atexit
from time import sleep
from os import path
import logging


PATH = path.dirname(path.abspath(__file__))
PATH += '' if PATH.endswith('/') else '/'

logging.basicConfig(filename = PATH + 'ChoriMate.log', level=logging.DEBUG)



with open(PATH + 'Choripanes.txt', 'r') as f: choripanes = f.read().splitlines()
with open(PATH + 'Mates.txt', 'r')      as f: mates = f.read().splitlines()

IMAGES = {
    'choripán': [line[1:] for line in choripanes if line.startswith('#')],
    'mate':     [line[1:] for line in mates if line.startswith('#')], 
}

WORDMAP = {'redditchoripan': 'choripán', 'tomateunmate': 'mate'}

MESSAGE = (
    '#[Aquí está tu {coso}, /u/{beneficiado}!]({img}  "{coso}")\n\n'
    '/u/{beneficiado} recibió {coso} {n} vece(s). (dado por /u/{beneficiador})'
)

PATTERN = re.compile('!(%s) ?(\/?u\/[a-z\-\_]{3,20})?' % '|'.join([key for key in WORDMAP]))    
ACCENT_CORRECTION = {'í': 'i', 'á':'a'} #Para tonterias == tonterías, choripán == choripan etc.

reddit = praw.Reddit('ChoriMate', user_agent = 'By /u/ElectrWeakHyprCharge 0129395675843884932')

def load_data():
    """Tries to load pickled file"""
    try:
        with open('data.pickle', 'rb') as p: data = pickle.load(p)
    except Exception as e:
        print('CHORIMATE: Loading error', e)
        data = {}
        input('Hubo un error al abrir data.pickle. Enter para continuar; Ctrl+C para salir') #Funciona como pausa, tengo que mejorar esto
    return data

def get_user(group_2, comment):
    try: return next(reddit.redditor(normalize_username(group_2 or comment.parent().author.name)).comments.new()).author.name
    except AttributeError as e: #Si parent().author == None y not user
        print('\nCHORIMATE: ERROR', e)
        return None

def match(comment, ignore_accents = False):
    """Returns a set with the people mentioned in the title"""

    content = comment.body.casefold()
    if ignore_accents:
        content = ''.join([ACCENT_CORRECTION.get(char, '') or char for i, char in enumerate(content)])
                
    return {e for e in {(m.group(1), get_user(m.group(2), comment)) for m in PATTERN.finditer(content)} if e[1] != None}
    
def normalize_username(username):
    """Removes the prefix of a username"""

    if username.startswith('/u/'):
        return username[3:]
    elif username.startswith('u/'):
        return username[2:]
    else:
        return username

def reply(comment, beneficiado, beneficiador, veces, cosa): 
    comment.reply(MESSAGE.format(
        beneficiado  = normalize_username(beneficiado),
        beneficiador = normalize_username(beneficiador),
        n            = veces,
        coso         = cosa,
        img          = choice(IMAGES[cosa])
    ))

def handle_matches(comment, times):
    matches = match(comment, True)
    if not matches: return False
        
    print('CHORIMATE: Matches:',  matches) 
    t = 0
    for comment_type, user in matches:
        t += 1
        print('*', end = '')
        user_lowercase = normalize_username(user).casefold()
        
        cosa = WORDMAP[comment_type]
        
        if (user_lowercase, cosa) not in times: times[user_lowercase, cosa] = 0
        times[user_lowercase, cosa] += 1
        
        for _ in range(5):
            try: reply(comment, user, comment.author.name, times[user_lowercase, cosa], cosa)
            except Exception as e:
                print('\nCHORIMATE: REPLY ERROR', e) 
                t.sleep(6)
                print('CHORIMATE: Retrying...')
            else: break
        if len(matches) > t: sleep(6) #Reddit da error si respondo con una diferencia menor a 5 segundos
    print()
    return True
    
def mainloop(sub, times):
    i = 0
    for comment in sub.stream.comments():
        if comment.saved: continue
        comment.save()
        
        print('CHORIMATE: Reading:', comment.permalink)
        if handle_matches(comment, times):
            i = (i + 1) % 3
            if not i: save_data()
        
@atexit.register
def save_data():
    print('CHORIMATE: Saving...')
    with open('data.pickle', 'wb') as p:
        pickle.dump(times, p)
    
if __name__ == '__main__':
    print('CHORIMATE: Start')
    sub = reddit.subreddit('uruguay+test')
    
    times = load_data()
    while True:
        try: mainloop(sub, times)
        except KeyboardInterrupt: raise
        except Exception as e:
            msg = 'CHORIMATE: UNCATCHED EXCEPTION IN MAINLOOP: ' + str(e) 
            logging.exception(msg)
            print(msg)
            print('CHORIMATE: RETRYING')
            sleep(5)


