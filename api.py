#!/usr/bin/python3
import logging as logger
import os
import string
import sys
import time
from collections import deque
from logging.config import dictConfig

import openai
import torch
from exceptions.exceptions import ApiException
from flask import Flask, request
from models.GPTNeo import GPTNeo
from utils import util
from utils.Config import Config
from utils.ContextItem import ContextItem

conf_file = "conf/test.conf"
if len(sys.argv) > 1 and sys.argv[1].endswith(".conf"):
    conf_file = sys.argv[1]
logger.info(f'starting up ({conf_file}) this might take a while')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
conf = Config(root_path=ROOT_DIR, config_file=conf_file)
app = Flask(__name__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = GPTNeo(conf, device)
# model = GPTJ(conf, device)
model.to(device)

punct  = string.punctuation

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': conf.loglevel,
        'handlers': ['wsgi']
    }
})


def create_incontext_post(params):
    logger.debug(params)
    in_context_prompt = ContextItem.to_conversational_hist(params["context"])
    temperature = None if 'temperature' not in params else params['temperature']
    mood = None if 'mood' not in params else params['mood']
    use_external = True if 'ours' not in params else params['ours'].lower() != 'true'

    prompt = util.prepare_incontext_prompt(in_context_prompt, mood)
    logger.debug("incontex prompt: " + prompt)

    if use_external:
        openai.api_key = conf.openai.api.key
        completion = openai.Completion.create(
            engine=conf.openai.model,
            temperature = temperature,
            max_tokens = conf.openai.max_tokens,
            prompt=prompt)
        logger.info(completion)
        completion = completion.choices[0]['text']
        completion = util.normalize_response(completion)

    else:
        completion = model.few_shot(prompt, "\n:", temperature=temperature)
    logger.debug(f'create post from history resp: {completion}')

    return completion


def complete_post(params):
        temperature = None if 'temperature' not in params else params['temperature']
        mood = None if 'mood' not in params else params['mood']
        use_external = True if 'ours' not in params else params['ours'].lower() != 'true'
        prompt = util.prepare_complete_prompt(params['prefix'], mood=mood)
        logger.info("complete prompt: " + prompt)
        if use_external:
            openai.api_key = conf.openai.api.key
            completion = openai.Completion.create(
                engine=conf.openai.model,
                temperature = temperature,
                max_tokens = conf.openai.max_tokens,
                prompt=prompt)
           
            completion = util.normalize_response(completion.choices[0]['text'])
        else:
            completion = model.autocomplete(prompt, temperature = temperature)
        logger.info("model(external={}) completion: {}".format(use_external, completion))
        return params['prefix'], completion


def create_self_description(params):
    temperature = None if 'temperature' not in params else params['temperature']
    use_external = True if 'ours' not in params else params['ours'].lower() != 'true'
    mood = None if 'mood' not in params or not use_external else params['mood']

    use_entity = False if 'use_entity' not in params else params['use_entity'].lower() == 'true'
    me, entity, prompt = util.prepare_self_desc_prompt(mood=mood)
    logger.debug("entitiy: {}, prompt: {}".format(entity, prompt))
    completion = ""
    if not use_entity:
        logger.info("prompt: " + prompt)
        if use_external:
            openai.api_key = conf.openai.api.key
            completion = openai.Completion.create(
                engine=conf.openai.model,
                temperature = temperature,
                max_tokens = conf.openai.self_desc_max_tokens,
                prompt=prompt,
                stop=".")
            
            completion = util.normalize_response(completion.choices[0]['text'])
        else:
            completion = model.autocomplete(prompt, temperature = temperature)
            completion = "{}. {}".format(me, completion)
        logger.info("model(external={}) completion: {}".format(use_external, completion))
    
    return entity, completion


@app.route('/api/create-incontext-post', methods=['POST'])
def create_post_from_history():
    try:
        start = time.time()
        validate_params(request.json, {"temperature", "context"})
        validate_temperature(request.json['temperature'])

        msg = create_incontext_post(request.json)
        end = time.time()-start
        logger.info(f'response: {msg}, took: {end}')
    
        return util.http_ok({
            "response" : msg,
            "time" : end})
    
    except Exception as e:
        if  isinstance(e, ApiException):
            return util.http_400(e)
        logger.exception("bad error")
        return util.http_500(e)


@app.route('/api/complete-post', methods=['POST'])
def complete_post_from_suffix():
    try:
        start = time.time()
        validate_params(request.json, {"temperature", "prefix"})

        pref, msg = complete_post(request.json)
        end = time.time()-start
        logger.info(f'comment: {msg}, took: {end}')

        return util.http_ok({
            "response" : msg,
            "prefix" : pref,
            "time" : end})
    
    except Exception as e:
        if  isinstance(e, ApiException):
            return util.http_400(e)
        logger.exception("bad error")
        return util.http_500(e)


@app.route('/api/self-description', methods=['POST'])
def create_self_desc():
    try:
        start = time.time()
        validate_params(request.json, {"temperature"})
        validate_temperature(request.json['temperature'])
        logger.debug("self desc payload: {}".format(request.json))
        entity, desc = create_self_description(request.json)
        end = time.time()-start
        logger.info(f'self description: {desc}, took: {end}')

        return util.http_ok({
            "response" : desc,
            "entity" : entity,
            "time" : end})

    except Exception as e:
        if  isinstance(e, ApiException):
            return util.http_400(e)
        logger.exception("bad error")
        return util.http_500(e)


def validate_temperature(t):
    if t > 2 or t < 0: raise ApiException("the t param is too small or large")

def validate_params(params, req):
    for p in req:
        if p not in params:
            raise ApiException("param {} is required and missing".format(p))
    



if __name__ == '__main__':
    app.run(host=conf.api.host,
            port=conf.api.port)

