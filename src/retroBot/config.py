import yaml

class config(dict):
    
    def __init__(self, filename):
        self.load(filename)
    
    def load(self, filename):
        self.filename = filename
        with open(filename, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)
                return
        # safe_load returns None for an empty file, and the existing contents
        # are only discarded once the new ones have parsed cleanly.
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise TypeError(f'{filename} must contain a YAML mapping, got {type(data).__name__}')
        self.filename = filename
        self.clear()
        self.update(data)
    
    def save(self):
        with open(self.filename, 'w') as stream:
            try:
                stream.write(yaml.safe_dump(self.copy()))
            except yaml.YAMLError as e:
                print(e)


    def reload(self):
        self.load(self.filename)