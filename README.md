#Full Stack Nanodegree Project 4 - HANGMAN API

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 
 
##Game Description:
Hangman is a simple guessing game. Each game begins with a random 'secret word'
(randomly chosen between a given list of words) and a maximum number of
'attempts'. 'Guesses' are sent to the `make_move` endpoint which will reply
with a list of the missed letters and the correct letters guessed between 
some * that indicates the hidden letters; it will reply with 'you win', or 
'game over' (if the maximum number of attempts is reached before guessing 
the whole word). For each User the Score is determined by the number of 
attempts made before guessing the word (or losing). The lower the Score
the best is the result.
Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Attempts must be less
    then 11. Also adds a task to a task queue to update the average moves 
    remaining for active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_average_attempts_remaining**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

- **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms
    - Description: Returns all Games played by the selected player, listing
    all the active games first (game_over=false) and then the completed ones 
    (game_over=true) .
    Will raise a NotFoundException if the User does not exist.
    
 - **cancel_game**
    - Path: ''game_canc/{urlsafe_game_key}''
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: Message confirming game deletion
    - Description: Allows users to cancel a game in progress but not 
      a completed game (a Boolean field identify cancelled games).
    
 - **get_high_scores**
    - Remember how you defined a score in Task 2?
            Now we will use that to generate a list of high scores in descending order, a leader-board!
            - Accept an optional parameter `number_of_results` that limits the number of results returned.
    
 - **get_user_rankings**
    - Come up with a method for ranking the performance of each player.
            (winning percentage with ties broken by the average number of guesses.)
            - Create an endpoint that returns this player ranking. 
            The results should include each Player's name and the 'performance' indicator (eg. win/loss ratio).
 
 - **get_game_history**
        - Your API Users may want to be able to see a 'history' of moves for each game.
        - Add the capability for a Game's history to be presented in a similar way.
         For example: If a User made played 'Guess a Number' with the moves:
        (5, 8, 7), and received messages such as: ('Too low!', 'Too high!',
        'You win!'), an endpoint exposing the game_history might produce something like:
        [('Guess': 5, result: 'Too low'), ('Guess': 8, result: 'Too high'),
        ('Guess': 7, result: 'Win. Game over')].
        - Adding this functionality will require some additional properties in the 'Game' model
        along with a Form, and endpoint to present the data to the User.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).

 - **GameForms**
    - Multiple GameForm container.

 - **NewGameForm**
    - Used to create a new game (user_name, attempts)

 - **MakeMoveForm**
    - Inbound make move form (guess).

 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).

 - **ScoreForms**
    - Multiple ScoreForm container.

 - **StringMessage**
    - General purpose String container.