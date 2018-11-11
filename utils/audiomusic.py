class Audio:
    def __init__(self, url=None, title=None, artist=None, vkurl=None, size=None):

        self.title = title
        self.artist = artist
        self.vkurl = vkurl
        self.size = size
        
        if url is None:
            url = vkurl
        else:
            self.url = url
