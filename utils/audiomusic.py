class Audio:
    def __init__(self, url=None, title=None, artist=None, vkurl=None, size=0):

        self.title = title
        self.artist = artist
        self.vkurl = vkurl
        self.size = size
        
        if url is None:
            url = vkurl
        else:
            self.url = url

    def __str__(self):
        return self.artist + " - " + self.title
    def __repr__(self):
        return str(self)
