import time, json

class ContextItem(object):
    def __init__(self, input=None, output=None, ts=None, source="man", dict=None):
        if dict is not None:
            self.__dict__ = dict
        else:
            self.input = "\"" + input + "\""
            self.output = "\"" + output + "\""
            self.source = source
            if ts is None:
                self.ts = time.time()

        self.delim = ""


    @staticmethod
    def normalize( value):

        if len(value) == 0: return value
        value = value.strip("\n ")
        #make First letter upper
        value = value[0].upper() + value[1:]
        
        parens = "\""
        if value[0] != parens:
            value = parens + value
        tmp = value.strip()
        suff = value[len(tmp):]
        if tmp[-1] != parens:
            tmp += parens
            value = tmp + suff

        return value


    def to_context_str(self, inputname, outputname, normalize=False):
            return "{}: {}\n{}: {}\n:".format(
                inputname,
                ContextItem.normalize(self.input) if normalize else self.input,
                outputname,
                ContextItem.normalize(self.output) if normalize else self.output,
                )


    @staticmethod
    def export(self):
        return self.__dict__

    @staticmethod
    def build_context_str(ci_list, inputname, outputname, normalize=False, input=None):
        str = ""
        for item in ci_list:
            str += item.to_context_str(inputname, outputname, normalize=normalize)
        if input is not None:
            str += "{}: {}\n{}: ".format(inputname, ContextItem.normalize(input) if normalize else input, outputname)
        str += inputname + ":"

    @staticmethod
    def to_conversational_hist(hist, normalize = False):
        context_str = ""
        first_source = hist[0]["source"]
        for item in hist:
            context_str += "{}: {}\n".format(
                item["source"], ContextItem.normalize(item['msg']) if normalize else item['msg'])

        return "{}{}:".format(context_str, first_source)


    @staticmethod
    def tolist(json_list):
        return [ContextItem(dict=item) for item in json_list]



