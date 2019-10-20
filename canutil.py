import os



class Config():
    def __init__(self, filename):
        self.mFilename = filename
        self.mTimestamp = 0
        self.mData = {}
        self.Read()
    def Read(self):
        if not os.path.isfile(self.mFilename):
            print("ERROR: config file '%s' does not exist" % self.mFilename)
            return
        ts = os.stat(self.mFilename).st_mtime
        if ts != self.mTimestamp:
            print("Config %s changed, reading ..." % self.mFilename)
            self.mTimestamp = ts
            try:
                with open(self.mFilename, 'r') as myfile:
                    data = myfile.read()
                s = eval('{' + data + '}')
                self.mData = s
                print ("Sucessfully read config %s" % self.mFilename)
                return True
            except Exception as e:
                print(traceback.format_exception(None, e, e.__traceback__))
        return False


