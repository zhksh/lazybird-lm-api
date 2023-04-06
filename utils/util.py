import json
import logging as logger
import pickle
from random import randrange

from flask import Response

from .ContextItem import ContextItem


def prepare_complete_prompt(prefix, mood=None):
    mood_prompt = create_mood_prompt(mood)
    return "{}{}:\n{}".format("Complete this sentence", mood_prompt, prefix)


def prepare_self_desc_prompt(mood=None):
    mood_prompt = create_mood_prompt(mood)
    entity = get_enitiy()
    me = "I am {}".format(entity)
    return me, entity, "{}. Write a self description of me{}:\n".format(me, mood_prompt)


def prepare_incontext_prompt(context, mood=None):
    mood_prompt = create_mood_prompt(mood)
    return "{}:\n{}".format("Continue this conversation{}".format(mood_prompt), context)


def create_mood_prompt(mood=None):
    mood_prompt = ""
    if mood is not None:
        det = get_determiner(mood )
        mood_prompt = " in {} {} tone".format(det, mood)

    return mood_prompt


def get_determiner(word):
    return 'an' if word[0] in {'a', 'e', 'i', 'o', 'u'} else 'a'


def get_enitiy():
    data = load_json("res/es.json")
    rand_occ = data['occupations'][randrange(len(data['occupations']))]
    rand_adj = data['adj'][randrange(len(data['adj']))]
    det = get_determiner(rand_adj)
    ent = "{} {} {}".format(det, rand_adj,  rand_occ)

    return ent


def find_eos(s, delims):
    for d in delims:
        i = s.rfind(d)+1
        if i > 0: return i

    return 0


def strip_response(generated_text, prompt, delims, max_len):
    #assuming the last token is anempt string after a whitespace and the token before that is what we should be looking for
    cutoff_idx = len(prompt)

    generated_response = generated_text[cutoff_idx:]
    generated_response = generated_response[:max_len-1]
    generated_response = generated_response[:find_eos(generated_response, delims)]
    logger.debug("cropped generation: {}".format(generated_response))

    return normalize_response(generated_response)

def normalize_response(resp):
    for tbr in ['\\', '\n', '*', '-', ';']:
        resp = resp.replace(tbr, '')

    return resp.strip()


def read_prompts(json_list):
    return ContextItem.tolist(json_list)


def read_turn_history(json_list):
    return ContextItem.tolist(json_list)


def http_500(err):
    return Response(create_api_response({"message":"lmb: something went awfully wrong", "error" : str(err)}), status=500)


def http_400(err):
    return Response(create_api_response({"message":"lmb: malformed request", "error" : str(err)}), status=400)


def http_ok(msg):
    return Response(create_api_response(msg), status=200)


def create_api_response(data):
    return json.dumps(data, indent=6, ensure_ascii=False).encode('utf8')


def pickle_stuff(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
        return data



