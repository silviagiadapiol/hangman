# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""

from __future__ import print_function
import random
import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

wordList = 'ant baboon badger bat bear beaver'.split()

@endpoints.api(name='hangman', version='v1')
class Hangman(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))


    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('attemps must be 10 or less!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        game.alreadyGuessed = game.missedLetters + game.correctLetters

        letter = request.guess
        letter = letter.lower()
        if len(letter) != 1:
            msg = 'Enter a single letter!'
            return game.to_form(msg)
        elif letter in game.alreadyGuessed:
            msg = 'Letter already guessed. Choose again!'
            return game.to_form(msg)
        elif letter not in 'abcdefghijklmnopqrstuvwxyz':
            msg = 'Please enter a proper LETTER.'
            return game.to_form(msg)
        else:
            request.guess = letter

        if request.guess in game.secretWord:
            game.correctLetters = game.correctLetters + request.guess
            # Check if the player has won
            foundAllLetters = True
            for i in range(len(game.secretWord)):
                if game.secretWord[i] not in game.correctLetters:
                    foundAllLetters = False
                    break
            if foundAllLetters:
                game.end_game(True)
                #return game.to_form('You win!')
                return game.to_form('Yes! The secret word is: ' + game.secretWord +'! You win!')
        else:
            game.missedLetters = game.missedLetters + request.guess

        # Print the missed letters and the correct letter in the right place between blanks
        game.attempts_remaining = game.attempts_allowed-len(game.missedLetters)
        blanks = '*' * len(game.secretWord)
        for i in range(len(game.secretWord)): # replace blanks with correctly guessed letters
            if game.secretWord[i] in game.correctLetters:
                blanks = blanks[:i] + game.secretWord[i] + blanks[i+1:]
        msg = 'Guessed letters: '+ blanks + ' - Missed Letters: ' + game.missedLetters + ' - You have ' + str(game.attempts_remaining) + ' attempts left.'
 

        # Check if player has guessed too many times and lost
        if len(game.missedLetters) == game.attempts_allowed:
            #msg = 'You are an Hangman! You have run out of guesses after '+ str(len(game.missedLetters)) + ' missed guesses and' + str(len(game.correctLetters)) + ' correct guesses, the secret word was "' + game.secretWord + '"'
            msg = 'You lose!'
            game.end_game(False)
            return game.to_form(msg + ' Game over!') 
        else:
            game.put()
            return game.to_form(msg)
        
        # game.attempts_remaining -= 1
        # if request.guess == game.target:
        #     game.end_game(True)
        #     return game.to_form('You win!')

        # if request.guess < game.target:
        #     msg = 'Too low!'
        # else:
        #     msg = 'Too high!'

        # if game.attempts_remaining < 1:
        #     game.end_game(False)
        #     return game.to_form(msg + ' Game over!')
        # else:
        #     game.put()
        #     return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])




    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([Hangman])