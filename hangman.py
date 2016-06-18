"""hangman.py - Create and configure the Game API exposing the resources."""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm,
    InsertLetterForm, ScoreForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
GUESS_A_LETTER_REQUEST = endpoints.ResourceContainer(
        InsertLetterForm,
        urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_GUESSES_REMAINING = 'GUESSES_REMAINING'

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
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
            game = Game.new_game(user.key, request.wordList, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('Attempts must be less or equal to 10!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Guess a Number!')

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

    @endpoints.method(request_message=GUESS_A_LETTER_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='guess_a_letter',
                      http_method='PUT')
    def insert_a_letter(self, request):
        """Guess a letter. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        def answer(attempts, missedLetters, correctLetters, secretWord):
          print('Missed letters:', end=' ')
          for letter in missedLetters:
            print(letter, end=' ')
            print()
          mlNumber=len(missedLetters)
          print('You have ' + str(attempts-mlNumber) + ' attempts left')
          blanks = '_' * len(secretWord)
          for i in range(len(secretWord)): # replace blanks with correctly guessed letters
            if secretWord[i] in correctLetters:
              blanks = blanks[:i] + secretWord[i] + blanks[i+1:]
          for letter in blanks: # show the secret word with spaces in between each letter
            print(letter, end=' ')
          print()

        def getGuess(guessed):
        # Returns the letter the player entered. Ensures the player entered a single letter
        while True:
          print('Guess a letter.')
          guessLetter = raw_input()
          guessLetter = guessLetter.lower()
          if len(guessLetter) != 1:
            print('Enter a single letter!')
          elif guessLetter in guessed:
            print('Letter already guessed. Insert again!')
          elif guessLetter not in 'abcdefghijklmnopqrstuvwxyz':
            print('Please enter a proper LETTER.')
          else:
            return guessLetter






         if request.guessLetter == game.secretWord:
          guessLetter = getGuess(missedLetters + correctLetters)
          if guessLetter in secretWord:
            correctLetters = correctLetters + guessLetter
          # Check if the player has won
          foundAllLetters = True
          for i in range(len(secretWord)):
            if secretWord[i] not in correctLetters:
                foundAllLetters = False
                break

            if foundAllLetters:
              msg = 'Yes! The secret word is "' + secretWord + '"! You have won!'
              game.end_game(True)
            else: 
              missedLetters = missedLetters + guessLetter
              game.attempts_remaining -= 1



        # if request.guess < game.target:
        #     msg = 'Too low!'
        # else:
        #     msg = 'Too high!'

          # Check if player has guessed too many times and lost
          if len(missedLetters) == attempts:
            answer(attempts, missedLetters, correctLetters, secretWord)
            print('You lose')
            game_over = True


        if game.attempts_remaining < 1:
          game.end_game(False)
          
          return game.to_form(msg + 'You are an Hangman!\n'
                                    'You have run out of guesses after \n'
                                    + str(len(missedLetters)) + ' missed guesses \n' 
                                    'and ' + str(len(correctLetters)) + ' correct guesses,\n'
                                    'the secret word was "' + secretWord + '"')
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


api = endpoints.api_server([HangmanApi])
