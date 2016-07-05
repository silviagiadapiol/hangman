"""game_class.py - This file contains the Game class and its forms
   definitions"""

import random
from score_class import Score
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

wordList1 = 'antelope badger bear beaver cat cow dog donkey elephant fish\
            fox giraffe goat hippopotamus horse kangaroo lion monkey parrot\
            penguin pig pony rhinoceros sheep snake tiger varan wale wolf\
            zebra'.split()
wordList2 = 'apple artichoke banana baens bread carrot cheese courgette date\
             egg eggplant garlic grapefruit ham lemon lettuce mango nut onion\
             orange pasta pizza pepper potato rice salad salmon strawberry\
             tomato tuna waffle'.split()
wordList3 = 'actor attorney carpenter dentist doctor electrician engineer\
             farmer hairdresser nurse painter pharmacist plumber surgeon\
             veterinary'.split()


class Game(ndb.Model):
    """Game object"""
    secretWord = ndb.StringProperty()
    missedLetters = ndb.StringProperty()
    correctLetters = ndb.StringProperty()
    word_category = ndb.IntegerProperty()
    attempts_allowed = ndb.IntegerProperty(default=10)
    attempts_remaining = ndb.IntegerProperty(required=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_cancelled = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    user_name = ndb.StringProperty()
    game_history = ndb.PickleProperty(required=True, default=[])

    @classmethod
    def new_game(cls, user, category):
        """Creates and returns a new game, choose your category"""
        if category == 1:
            wordList = wordList1
        elif category == 2:
            wordList = wordList2
        else:
            wordList = wordList3

        game = Game(user=user,
                    user_name=user.get().name,
                    secretWord=wordList[random.randint(0, len(wordList) - 1)],
                    missedLetters='',
                    correctLetters='',
                    word_category=category,
                    attempts_allowed=10,
                    attempts_remaining=10,
                    game_cancelled=False,
                    game_over=False)
        game.game_history = []
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.word_category = self.word_category
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.game_cancelled = self.game_cancelled
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user,
                      date=date.today(),
                      won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining)
        score.put()

    def add_history(self, letter, msg):
        self.game_history.append({'guess': letter, 'answer': msg})
        self.put()


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    word_category = messages.IntegerField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    game_cancelled = messages.BooleanField(5, required=True)
    message = messages.StringField(6, required=True)
    user_name = messages.StringField(7, required=True)


class GameForms(messages.Message):
    """GameForms -- multiple Game outbound form message"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    cat_1_animals_2_food_3_jobs = messages.IntegerField(2)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)
