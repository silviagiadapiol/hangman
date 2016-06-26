"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

from __future__ import print_function
import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

wordList1 = 'ant baboon badger bat bear beaver'.split()
wordList2 = 'bread spaghetti pizza pasta rice blueberry'.split()
wordList3 = 'taylor chemister hairdresser doctor attorney'.split()


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    victories = ndb.IntegerProperty(default=0)
    losses = ndb.IntegerProperty(default=0)
    ratio = ndb.FloatProperty(default=0.0)

    def to_form(self):
        form = UserForm()
        form.name = self.name
        form.email = self.email
        form.ratio = float(self.victories)/(
                     float(self.victories)+float(self.losses))
        form.victories = self.victories
        form.losses = self.losses
        return form


class Game(ndb.Model):
    """Game object"""
    secretWord = ndb.StringProperty()
    missedLetters = ndb.StringProperty()
    correctLetters = ndb.StringProperty()
    word_category = ndb.IntegerProperty()
    attempts_allowed = ndb.IntegerProperty(default=10)
    attempts_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_cancelled = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    user_name = ndb.StringProperty()

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
                    secretWord=wordList[random.randint(0, len(wordList)-1)],
                    missedLetters='',
                    correctLetters='',
                    word_category=category,
                    attempts_allowed=3,
                    attempts_remaining=3,
                    game_cancelled=False,
                    game_over=False)
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


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        form = ScoreForm()
        form.user_name = self.user.get().name
        form.won = self.won
        form.date = str(self.date)
        form.guesses = self.guesses
        return form


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
    category_1_animals_2_food_3_jobs = messages.IntegerField(2)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class UserForm(messages.Message):
    """UserForm for outbound ranking"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    ratio = messages.FloatField(3)
    victories = messages.IntegerField(4)
    losses = messages.IntegerField(5)


class UserForms(messages.Message):
    """Return multiple UserForms"""
    items = messages.MessageField(UserForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
