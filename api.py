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
    ScoreForms, GameForms#, GameQueryForm, GameQueryForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key = messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key = messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(
	user_name = messages.StringField(1),
	email = messages.StringField(2))
CANCEL_REQUEST = endpoints.ResourceContainer(
       urlsafe_game_key = messages.StringField(1),)
HIGH_SC_REQUEST = endpoints.ResourceContainer(
	max_results_to_show = messages.IntegerField(1),)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

wordList1 = 'ant baboon badger bat bear beaver'.split()
wordList2 = 'bread spaghetti pizza pasta rice blueberry'.split()
wordList3 = 'taylor, chemister, hairdresser'.split()

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
        if request.category_1_animals_2_food_3_jobs <1 or request.category_1_animals_2_food_3_jobs >3:
            raise endpoints.NotFoundException(
            	'You should choose a category between 1 and 3! '\
            	'1=animals, 2=food, 3=jobs')
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.category_1_animals_2_food_3_jobs)
        except ValueError:
        	raise endpoints.BadRequestException('ddd')
    
        # Use a task queue to update the average attempts remaining.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman! You have 10 '
        'attempts to guess the secret word of your chosen category: '+
        str(request.category_1_animals_2_food_3_jobs))

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

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return games created by user."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query().filter(Game.user == user.key).order(Game.game_over)
        return GameForms(items=[game.to_form('game retrieved') for game in games])

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
        if game.game_cancelled:
            return game.to_form('Game cancelled! You cannot play it!')
        # Check if the player enters a single letter not already guessed
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
        # If the letter is in the secret word add it the correct
        # letters list, otherwise add it to the wrong letter list
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
                msg = 'Yes, the secret word is: '+ game.secretWord + \
                '! You win after ' + str(len(game.missedLetters)) + \
                ' missed guesses'
            	return game.to_form(msg)
        else:
            game.missedLetters = game.missedLetters + request.guess
        # Print the missed letters and replace blanks with guessed letters
        game.attempts_remaining = game.attempts_allowed-len(game.missedLetters)
        blanks = '*' * len(game.secretWord)
        for i in range(len(game.secretWord)):
            if game.secretWord[i] in game.correctLetters:
                blanks = blanks[:i] + game.secretWord[i] + blanks[i+1:]
        msg = 'Guessed letters: ' + blanks + ' - Missed Letters: ' +\
        game.missedLetters + ' - You have ' +\
        str(game.attempts_remaining) + ' attempts left.'
        # Check if player has guessed too many times and lost
        if len(game.missedLetters) == game.attempts_allowed:
            msg = 'You are an Hangman! You have run out of guesses after ' + \
            str(len(game.missedLetters)) + ' missed guesses and ' + \
            str(len(game.correctLetters)) + ' correct guesses, '\
            ' the secret word was: ' + game.secretWord + '! '
            game.end_game(False)
            return game.to_form(msg + 'Game over!')
        else:
            game.put()
            return game.to_form(msg)

    @endpoints.method(request_message=CANCEL_REQUEST,
                      response_message=StringMessage,
                      path='game_canc/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel a given game. Returns a success message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return StringMessage(
                message='Game already over! You cannot cancel it!')
        else:
            game.game_cancelled = True
            game.put()
            return StringMessage(message='Game {} canceled!'.format(
                request.urlsafe_game_key))

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

    @endpoints.method(request_message=HIGH_SC_REQUEST,
                      response_message=ScoreForms,
                      path='high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Returns the players total scores ordered with the best first\
        (the player with the lowest number of attemps to guess) """
        if request.max_results_to_show:
        	scores = Score.query(Score.won == True).order(Score.guesses).fetch(request.max_results_to_show)
      	else:
        	scores = Score.query(Score.won == True).order(Score.guesses).fetch()
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