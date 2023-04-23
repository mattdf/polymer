import os
import re
import json
from typing import TypedDict
from typing import Optional
from os.path import dirname
import openai
from .prompts import Prompt
from .utils import sexyhash

OPENAI_API_KEY:Optional[str] = None
try:
    from config import OPENAI_API_KEY as config_OPENAI_API_KEY
    OPENAI_API_KEY = config_OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    raise RuntimeError('Must specify "OPENAI_API_KEY" in config.py or environment')


openai.api_key = OPENAI_API_KEY


CACHE_DIR = os.path.join(dirname(dirname(__file__)), 'cache.openai')
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)


class ChatCompletionChoice(TypedDict):
    index: int
    logprobs: dict[str, float]
    text: str
    finish_reason: str


class ChatCompletion(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    prompt: str
    session: str
    status: str


class CompletionChoice(TypedDict):
    index: int
    text: str


class CompletionUsage(TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class CompletionResult(TypedDict):
    choices: list[CompletionChoice]
    created: int
    id: str
    model: str
    object: str
    usage: CompletionUsage


def extract_markdown_codes(result:CompletionResult):
    codes = []
    for choice in result['choices']:
        buf = []
        in_code = False
        for line in choice['text'].splitlines():
            if not in_code:
                if line.startswith('```'):
                    lang = line[3:].strip()
                    if not len(line):
                        lang = None                    
                    in_code = True
                    continue
            else:
                if line.startswith('```'):
                    in_code = False
                    codes.append([lang, '\n'.join(buf)])
                    lang = None
                    buf = []
                    continue
                buf.append(line)
    return codes


def completion(p:Prompt, replacements:dict[str,str], cache_ctx:dict|None=None, default_model:str='text-davinci-003', default_max_tokens:int=1000):
    args: dict[str,str] = dict()    
    if p.model is not None:
        args['model'] = p.model
    else:
        args['model'] = default_model
    if p.max_tokens is not None:
        args['max_tokens'] = p.max_tokens
    else:
        args['max_tokens'] = default_max_tokens
    if p.temperature:
        args['temperature'] = p.temperature
    pt = p.text

    replacements = {k.upper(): v for k, v in replacements.items()}  # All replacements are uppercase
    # Removed unused replacements
    for _ in set(re.findall(r'\$\$([A-Z]+)\$\$', pt)).difference(set(replacements.keys())):
        pt = pt.replace(f'$${_}$$', '')

    # Fill used replacements
    for k, v in replacements.items():
        pt = pt.replace('$$' + str(k) + '$$', v)
    args['prompt'] = pt

    # OpenAI is expensive, cache results
    cid = sexyhash(p.name, **args)
    cp = os.path.join(CACHE_DIR, cid + '.json')

    if not os.path.exists(cp):
        result:CompletionResult = openai.Completion.create(**args)
        with open(cp, 'w') as handle:
            info = {
                'cid': cid,
                'ctx': cache_ctx,
                'replacements': replacements,
                'args': args,
                'result': result
            }
            handle.write(json.dumps(info))
    else:
        with open(cp, 'r') as handle:
            info = json.load(handle)
    return info


def chatcompletion():
    model = "gpt-4"
    temperature = 0.6
    presence_penalty = 0
    top_p = 1

    system_prompt = "x"
    user_prompt = "y"

    openai.api_key = os.environ.get("OPENAI_API_KEY")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )
