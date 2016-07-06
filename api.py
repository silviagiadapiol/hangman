"""api.py - Create and configure the Hangman Game API
exposing the resources and define the endpoints to use it."""
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from utils import get_by_urlsafe

from models.user_class import (
    User,
    UserForms,
    StringMessage,
)
from models.game_class import (
    Game,
    NewGameForm,
    GameForm,
    GameForms,
    MakeMoveForm,
)
from models.score_class import (
    Score,
    ScoreForms,
)

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUESTS = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))
HIGH_SC_REQUEST = endpoints.ResourceContainer(
    max_results_to_show=messages.IntegerField(1),)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman', version='v1')
class Hangman(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Creates a User.
        Args:
            request: The USER_REQUEST object, which includes a users
            chosen name and an optional email.
        Returns:
            StringMessage: A message that is sent to the client, saying that
            the user has been created.
        Raises:
            endpoints.ConflictException: If the user already exists."""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name,
                    email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates a new game.
        Args:
            request: The NEW_GAME_REQUEST object, which includes a
            NewgameForm requiring the user name and the desired category
        Returns:
            a GameForm with the attempts remainming, the cancelled and
            game_over flags, the urlsafe key of the game the user name,
            the chosen category and a messagge that tells how many
            letters the scret word has.
        Raises:
            endpoints.NotFoundException: If that user doesn't exists.
            endpoints.BadRequestException: If the category is not
            1, 2 or 3."""
        user = User.query(User.name == request.user_name).get()
        if request.cat_1_animals_2_food_3_jobs < 1 or request.cat_1_animals_2_food_3_jobs > 3:
            raise endpoints.NotFoundException(
                'You should choose a category 1=animals, 2=food, 3=jobs')
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        try:
            game = Game.new_game(
                user.key, request.cat_1_animals_2_food_3_jobs)
        except ValueError:
            raise endpoints.BadRequestException('bad category')

        # Use a task queue to update the average attempts remaining.
        taskqueue.add(url='/tasks/cache_average_attempts')

        return game.to_form('Good luck playing Hangman! You have 10 attempts '
                            'to guess the secret word of your chosen '
                            'category; it has ' +
                            str(len(game.secretWord)) + ' letters')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move (guess).
        Args:
            request: The MAKE_MOVE_REQUEST object, which includes the
            make_moveForm (that requires a guess) and the game urlsafe
        Returns:
            Game.to_form: telling if the guess is correct or not, the list
            of missed letters and the correct letters in the right order,
            or telling if the user won guessing the word or lost by making
            too much wrong attepts.
        Raises:
            endpoints.ForbiddenException: If that game is already over 
            or it has been cancelled."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            raise endpoints.ForbiddenException(
                'Illegal action: Game is already over.')
        if game.game_cancelled:
            raise endpoints.ForbiddenException(
                'Illegal action: Game has been cancelled.')
        # Check if the player enters a single letter not already guessed
        game.alreadyGuessed = game.missedLetters + game.correctLetters
        letter = request.guess
        letter = letter.lower()
        if letter.isalpha():
            if letter == game.secretWord:
                game.end_game(True)
                user = game.user.get()
                user.victories += 1
                user.ratio = float(user.victories) / float(
                    user.victories + user.losses)
                user.put()
                msg = 'Yes, the secret word is: ' + game.secretWord + \
                      '! You win after ' + str(len(game.missedLetters)) + \
                      ' missed guesses'
                game.add_history(letter, msg)
                return game.to_form(msg)
            else:
                if len(letter) != 1:
                    msg = 'Enter a single letter or try to guess the whole word'
                    return game.to_form(msg)
                else:
                    if letter in game.alreadyGuessed:
                        msg = 'Letter already guessed. Choose again!'
                        return game.to_form(msg)
                    else:
                        request.guess = letter
        else:
            raise endpoints.ForbiddenException(
                'Illegal guess: you have to insert a proper single letter!')
        # If the letter is in the secret word add it the correct
        # letters list, otherwise add it to the wrong letter list
        if request.guess in game.secretWord:
            game.correctLetters = game.correctLetters + request.guess
            mess = 'Yes, the letter ' + letter.upper() + ' is correct! *** '
        else:
            game.missedLetters = game.missedLetters + request.guess
            mess = 'No, the letter ' + letter.upper() + ' is not correct! *** '
        # Print the missed letters and replace blanks with guessed letters
        game.attempts_remaining = game.attempts_allowed - len(game.missedLetters)
        blanks = '-' * (len(game.secretWord))
        for i in range(len(game.secretWord)):
            if game.secretWord[i] in game.correctLetters:
                blanks = blanks[:i] + game.secretWord[i] + blanks[i + 1:]
        msg = mess + 'Missed Letters: ' + game.missedLetters +\
            ' *** Guessed letters: ' + blanks + ' *** You have ' +\
            str(game.attempts_remaining) + ' attempts left.'
        # Check if player has guessed too many times and lost
        if len(game.missedLetters) == game.attempts_allowed:
            msg = 'You are an Hangman! You have run out of guesses after ' + \
                str(len(game.missedLetters)) + ' missed guesses and ' + \
                str(len(game.correctLetters)) + ' correct guesses, '\
                'the secret word was: ' + game.secretWord + '! '
            user = game.user.get()
            user.losses += 1
            user.ratio = float(user.victories) / float(
                user.victories + user.losses)
            user.put()
            game.add_history(letter, msg)
            game.end_game(False)
            return game.to_form(msg + 'Game over!')
        else:
            game.put()
            game.add_history(letter, msg)
            return game.to_form(msg)

    @endpoints.method(request_message=GET_GAME_REQUESTS,
                      response_message=StringMessage,
                      path='game_canc/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel a game.
        Args:
            request: The GET_GAME_REQUESTS object, which require the
            urlsafe_game_key
        Returns:
            StringMessage: telling that the Game has been cancelled
        Raises:
            endpoints.ForbiddenException: If that game is already over."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            raise endpoints.ForbiddenException(
                'Illegal action: Game is already over, you cannot cancel it.')
        else:
            game.game_cancelled = True
            game.put()
            return StringMessage(message='Game {} canceled!'.format(
                request.urlsafe_game_key))

    @endpoints.method(request_message=GET_GAME_REQUESTS,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Retrieve a game.
        Args:
            request: The GET_GAME_REQUESTS object, which require the
            urlsafe_game_key
        Returns:
            StringMessage: telling if the Game is cancelled, already
            completed or still waiting for a new move
        Raises:
            endpoints.NotFoundException: If that game doesn't exists."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return game.to_form('Game already completed!')
            else:
                if game.game_cancelled:
                    return game.to_form('Game cancelled!')
                else:
                    return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='active_games/user/{user_name}',
                      name='get_user_active_games',
                      http_method='GET')
    def get_user_active_games(self, request):
        """Retrieve active games created by user.
        Args:
            request: The USER_REQUEST object, which includes a users
            chosen name and an optional email.
        Returns:
            StringMessage: telling to maj=ke a move in the active games
        Raises:
            endpoints.NotFoundException: If that user doesn't exists."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(
            Game.user == user.key).filter(
                Game.game_over == False).filter(Game.game_cancelled == False)
        return GameForms(
            items=[game.to_form('Time to make a move!') for game in games])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='cancelled_games/user/{user_name}',
                      name='get_user_cancelled_games',
                      http_method='GET')
    def get_user_cancelled_games(self, request):
        """Retrieve all the games created by the user that cannot be played
        because they have been cancelled.
        Args:
            request: The USER_REQUEST object, which includes a users
            chosen name and an optional email.
        Returns:
            StringMessage: telling that the Game is cancelled
        Raises:
            endpoints.NotFoundException: If that user doesn't exists."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(
            Game.user == user.key).filter(Game.game_cancelled == True)
        return GameForms(
            items=[game.to_form('game cancelled!') for game in games])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='completed_games/user/{user_name}',
                      name='get_user_completed_games',
                      http_method='GET')
    def get_user_completed_games(self, request):
        """Retrieve all the games created by the user that cannot be played
        because they have been completed.
        Args:
            request: The USER_REQUEST object, which includes a users
            chosen name and an optional email.
        Returns:
            StringMessage: telling if the Game is cancelled, already
            completed or still waiting for a new move
        Raises:
            endpoints.NotFoundException: If that user doesn't exists."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(
            Game.user == user.key).filter(Game.game_over == True)
        return GameForms(
            items=[game.to_form('game completed!') for game in games])

    @endpoints.method(request_message=GET_GAME_REQUESTS,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return the chosen game guesses and answers history
        Args:
            request: The GET_GAME_REQUESTS object, which require the
            urlsafe_game_key
        Returns:
            StringMessage: telling with the game guesses and answers history
        Raises:
            endpoints.NotFoundException: If that game doesn't exist."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return StringMessage(message=str(game.game_history))
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining
        Args:
            None
        Returns:
            StringMessage: telling the number of average moves remaining"""
        return StringMessage(message=memcache.get(
            MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over is False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                            for game in games])
            average = float(total_attempts_remaining) / count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(
                             average))

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Get all users scores
        Args:
            None
        Returns:
            ScoreForms with the user name, the date, the won flag and
            the number of guesses"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores
        Args:
            request: The USER_REQUEST object, which includes a users
            chosen name and an optional email.
        Returns:
            ScoreForms with the user name, the date, the won flag and
            the number of guesses
        Raises:
            endpoints.NotFoundException: If that user doesn't exist."""
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
        """Returns the players total scores ordered with the best first
        (the player with the lowest number of attemps to guess)
        Args:
            request: The HIGH_SC_REQUEST object, which require the
            optional max number of results to show
        Returns:
            ScoreForms with the user name, the date, the won flag and
            the number of guesses."""
        if request.max_results_to_show:
            scores = Score.query(Score.won is True).order(
                Score.guesses).fetch(request.max_results_to_show)
        else:
            scores = Score.query(Score.won is True).order(
                Score.guesses).fetch()
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserForms,
                      path='user_ranking',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return the players ordered by victories/losses ratio with ties
        broken by the number of victories
        Args:
            request: None
        Returns:
            UserForms: with the user name, mail, win ratio, victories
            and losses."""
        users = User.query().order(-User.ratio, User.victories)
        return UserForms(items=[user.to_form() for user in users])


api = endpoints.api_server([Hangman])
