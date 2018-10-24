from typing import List, Dict, Tuple
import json


Userdata = Dict[str, Dict[str, int]]
Links = List[str]
Reward = str


def userdata() -> Userdata:
    with open('data.json', 'r') as f:
        return json.load(f)


def save(userdata: Userdata):
    with open('data.json', 'w') as f:
        json.dump(userdata, f)


def commands() -> Dict[str, Tuple[Reward, Links]]:
    with open('config.json', 'r') as f:
        return {k : (cmd["reward"], tuple(cmd["images"]))
                for k, cmd in json.load(f).items()}
