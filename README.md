#Full Stack Nanodegree Project 4 - HANGMAN API

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 
 
##Game Description:
Hangman is a simple guessing game. Each time a player creates a new game
he has to chose a category between 1-animals, 2-fodd and 3-jobs. The 'secret
word' to guess is randomly chosen from a given list of words of that category. 
The player 'Guesses' are sent to the `make_move` endpoint which will reply with 
a list of the missed letters and one of the letters correctly guessed, placed
between some * (that indicates the hidden letters still to guess).
When all the letters of the secret word have been guessed, it will reply with
'you win'; if the maximum number of attempts (10) is reached before the whole
word is guessed, it will reply 'game over'. It's possible to see the average
number of attemps remaining.
For each User the Score is determined by the number of attempts (missed letters)
made before guessing the word. So the lower is the Score, the best is the result.
Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.
It's possible to cancel active games but not completed ones.
It is possible to see also the players ranking and a game history (a sequence of 
the attemped guesses and the answer messagges of a chosen completed or active game).

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - index.py: Composite index.
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
    - Parameters: user_name, category_1_animals_2_food_3_jobs
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Category must be chosen
    between 1(animals), 2(food) or 3(jobs) - will raise a NotFoundException if not.
    Also adds a task to a task queue to update the average moves remaining for
    active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms
    - Description: Returns all Games played by the selected player, listing
    all the active games first (game_over=false) and then the completed ones 
    (game_over=true) .
    Will raise a NotFoundException if the User does not exist.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **cancel_game**
    - Path: ''game_canc/{urlsafe_game_key}''
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: Message confirming game deletion
    - Description: Allows users to cancel a game in progress but not 
      a completed game (a Boolean field identify cancelled games).

 - **get_average_attempts_remaining**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.
    
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
    
 - **get_high_scores**
    - Path: 'high_scores/user/{user_name}'
    - Method: GET
    - Parameters: max_results_to_show (optional)
    - Returns: ScoreForms. 
    - Description: Returns all players total Scores ordered with the best (lowest) first.
    
- **get_user_rankings**
    - Path: 'user_ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserForms. 
    - Description: Returns all players ordered by victories/losses ratio (with ties broken
      by the number of victories).
 
 - **get_game_history**
    - Path: 'game_history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage with the sequene of guesses and answers of a game
    - Description: Returns a 'history' of moves for each game.  

##Models Included:
 - **User**
    - Stores unique user_name, email address (optional) and winning ratio.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    word_category, game_over flag, game_cancelled flag, message, user_name).

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

 - **UserForm**
    - Representation of a user's Ranking (user_name, email, ratio, victories,
    losses).

 - **UserForms**
    - Multiple UserForm container.

 - **StringMessage**
    - General purpose String container. -->