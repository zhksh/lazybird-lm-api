import json


class Config(object):
    def __init__(self, config=None, config_file=None, root_path=None):
        config_parent = None
        self.path = root_path
        if config_file:            
            config = self.json_loadf(config_file)
            self.configname = config_file.split("/")[-1]
       
        if config:
            self._merge(config)
       
    def _merge(self, config):
        if not isinstance(config, dict):
            return
        newdata = {}
        if 'include' in config:
            self._merge(self.json_loadf(config['include']))
            del(config['include'])
        for key in config:
            if key in self.__dict__:                
                if isinstance(config[key], dict): 
                    self.__dict__[key]._merge(config[key])            
                elif isinstance(config[key], list):
                    self.__dict__[key] = [Config(x) if isinstance(x, dict) else x for x in config[key]]
                else:
                    newdata[key] = config[key]
            else :
                if isinstance(config[key], dict): 
                     newdata[key] = Config(config[key])                
                elif isinstance(config[key], list):
                    newdata[key] = [Config(x) if isinstance(x, dict) else x for x in config[key]]
                else:
                    newdata[key] = config[key]
        self.__dict__.update(newdata)

    def __repr__(self):
        return '%s' % self.__dict__

    def json_loadf(self, filename):

        conf = None
        try:
            conf = json.load(open(filename))
        except FileNotFoundError as fnfe:
            try:
                conf = json.load(open(self.path +"/conf/"+ filename))
            except Exception as e:
                raise Exception("loading config file {} failed".format(filename))
        except Exception as e:
            raise Exception("in file {} : ".format(filename))
        return conf

    def add(self, key, value):
        self.__dict__[key] = value  
        
    def as_dict(self):
        dict = vars(self)
        for key in dict:
            if isinstance(dict[key], Config):
                dict[key] = dict[key].as_dict()
            elif isinstance(dict[key], list):
                for i, el in enumerate(dict[key],0):
                    if isinstance(el, Config):
                        dict[key][i] = el.as_dict()
    
        return dict 
    