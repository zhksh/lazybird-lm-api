import logging as logger
import time
import torch
from transformers import StoppingCriteria, StoppingCriteriaList

from utils import util

class GPT(torch.nn.Module):

    def __init__(self, conf, device):
        super(GPT, self).__init__()
        self.conf = conf
        start = time.time()
        self.device = device

        self.init()
        self.loading_time = time.time()-start
        self.say_hello()



    def few_shot(self, prompt, eogen, temperature = None):

        if temperature is None:
            temperature = self.conf.inference.temperature

        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        input_ids = input_ids.to(self.device)

        sl = StoppingCriteriaList()
        sl.append(CustomEOSReachedCriteria(eogen))
        max_len = len(prompt) + self.conf.inference.max_len

        gen_tokens = self.base_model.generate(input_ids,
                                              do_sample=True,
                                              temperature=temperature,
                                              max_length=max_len,
                                              eos_token_id=self.tokenizer(eogen)["input_ids"][0],
                                              repetition_penalty=self.conf.inference.repetition_penalty,
                                              stopping_criteria=sl
                                              )
        gen_text = self.tokenizer.batch_decode(gen_tokens)[0]
        logger.debug(f'prompt: {len(prompt)}, allowed maxlen: {max_len}, actual output len { len(gen_text)}, '
                        f' full output: {gen_text}')
        
        return util.strip_response(gen_text, prompt, self.conf.eol_symbols, self.conf.inference.max_len)


    def autocomplete(self, prefix, eogen = '\n', temperature = None, cutoffidx=1):
        input_ids = self.tokenizer(prefix, return_tensors="pt").input_ids
        input_ids = input_ids.to(self.device)

        if temperature is None:
            temperature = self.conf.inference.temperature

        max_len = self.conf.inference.max_len
        gen_tokens = self.base_model.generate(input_ids,
                                              do_sample=True,
                                              temperature=temperature,
                                              max_length=max_len,
                                              min_length=20,
                                              eos_token_id=self.tokenizer(eogen)["input_ids"][0],
                                              repetition_penalty=self.conf.inference.repetition_penalty,
                                              )
        gen_text = self.tokenizer.batch_decode(gen_tokens)[0]

        logger.debug(f'prompt: {len(prefix)}, allowed maxlen: {max_len}, actual output len { len(gen_text)}, '
                     f'cutoofidx: {cutoffidx}, full output: {gen_text}')

        return util.strip_response(gen_text, prefix, self.conf.eol_symbols, max_len=max_len)


    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


    def show_id_maping(self, prompt):
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        for i, id in enumerate(input_ids[0]):
            print("{} {} -{}-".format(i, id, self.tokenizer.decode([id])))


    def say_hello(self):
        logger.info(f'hi im {self.conf.model.name} i have {self.count_parameters()} params, loading took: {self.loading_time}')





class CustomEOSReachedCriteria(StoppingCriteria):

    def __init__(self, custom_eos: int):
        logger.debug("applying eos id:{} as stopping criteria".format(custom_eos))
        self.custom_eos = custom_eos

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        return input_ids[0][-1] == self.custom_eos