import json

class Config:

    link_dict={}

    def __init__(self, config_dict, file_path='config.json'):
        self.file_path=file_path
        try:
            with open(self.file_path, 'r')as f:
                self.config = json.load(f)
        except:
            self.config = json.loads('{}')
        for key, value in config_dict.items():
            if not key in self.config:
                self.config[key]=value
        self.__save()

    def __getitem__(self,key):
        if key in self.config:
            return self.config[key]
        else:
            return None
    def __setitem__(self,key,value):
        self.config[key] = value
        self.__save()
    def __save(self):
        with open(self.file_path, 'w')as f:
            json.dump(self.config, f, indent=4)

