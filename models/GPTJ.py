import torch.nn
from transformers import AutoTokenizer, AutoModelForCausalLM
from models.GPT import GPT

from utils.Config import Config


class GPTJ(GPT):
    def __init__(self, conf, device):
        conf.model.name = "EleutherAI/gpt-j-6B"
        super(GPTJ, self).__init__(conf, device)

    def init(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.conf.model.name)
        self.base_model = AutoModelForCausalLM.from_pretrained(self.conf.model.name, pad_token_id=self.tokenizer.eos_token_id)




if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    conf = Config(config_file="../base.json")
    model = GPTJ(conf, device)
    model.say_hello()

    while True:
        instr = input()
        print(model.generate(instr))

