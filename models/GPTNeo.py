import torch
from transformers import GPTNeoForCausalLM, GPT2Tokenizer
from models.GPT import GPT


class GPTNeo(GPT):
    def __init__(self, conf, device):
        super(GPTNeo, self).__init__(conf, device)

    def init(self):
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.conf.model.name)
        self.base_model = GPTNeoForCausalLM.from_pretrained(self.conf.model.name, pad_token_id=self.tokenizer.eos_token_id)
        self.few_shot_eos = self.tokenizer("###")["input_ids"][0]



if __name__ == '__main__':
    import os

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    conf = Config(root_config_file="base.json")
    model = GPTNeo(conf)


    # while True:
    #     instr = input()
    #
    # # input = "What if I was a robot?"
    #     print(model.few_shot(instr))

    prompt = 'Tweet: "I hate it when my phone battery dies."\n' \
             'Sentiment: Negative\n' \
             '###\n' \
             'Tweet: "My day has been 👍\n' \
             '"Sentiment: Positive\n' \
             '###\n' \
             'Tweet: "This is the link to the article"\n' \
             'Sentiment: Neutral\n' \
             '###\n' \
             'Tweet: "Here are the latest results"\n' \
             'Sentiment:'
    print(model.show_id_maping(prompt))
    print(model.few_shot(prompt))
    print(model.count_parameters())
