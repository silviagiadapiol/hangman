import webbrowser

class Movie():
    """ This class contains key information about movies"""
    def __init__(self, movie_title, movie_year, movie_storyline, poster_image,
                 trailer_youtube):     
        self.title=movie_title
        self.year=movie_year
        self.storyline=movie_storyline
        self.poster_image_url=poster_image
        self.trailer_youtube_url=trailer_youtube

    def show_trailer(self):
        """opens a web page with the trailer of the instance movie"""
        webbrowser.open(self.trailer_youtube_url)
