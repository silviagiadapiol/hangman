# Full Stack Nanodegree Project 4 - HANGMAN API

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 
 
## Game Description:
Hangman is a simple guessing game. Each time a player creates a new game
he has to chose a category between 1-animals, 2-fodd and 3-jobs. The 'secret
word' to guess is randomly chosen from a given list of words of that category. 
The player 'Guesses' are sent to the `make_move` endpoint which will reply with a list of the missed letters and one of the letters correctly guessed, placed between some - (that indicates the hidden letters still to guess).
When all the letters of the secret word have been guessed (or the whole word),
it will reply with 'you win'; if the maximum number of attempts (10) is 
reached before the whole word is guessed, it will reply 'game over'.
Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved by using the path parameter
`urlsafe_game_key`. 
It's possible to cancel active games but not completed ones.
It is also possible to see the players ranking and a game history (a sequence of the attemped guesses and the answer messagges of a chosen completed or active game).
It's also possible to see the average number of attemps remaining.
For each User the Score is determined by the number of attempts (missed letters) made before guessing the word. So the lower is the Score, the better is the result.
It's possible to see all the scores of all users, all the scores of a user or the players total scores ordered with the best first, as well as the player ranking (win/loss ratio).

 - Use the `new_game` endpoint to create a new user. Remember to copy the 
  `urlsafe_key` property for later use.
 - Use the `new_game` endpoint to create a new game for a user and a category.
 - Use the `make_move` endpoint to retrieve a game you want to play (through 
  its `urlsafe_key`) and to insert a letter or a word to make your guess.
 - Use the `cancel_game` endpoint to cancel a game through its `urlsafe_key`.
 - Use the `get_game` endpoint to retrieve a single game through its `urlsafe_key`.
 - Use the `get_user_active_games` endpoint to retrieve all the active games of a user.
 - Use the `get_user_cancelled_games` endpoint to retrieve all the cancelled games of a user.
 - Use the `get_user_completed_games` endpoint to retrieve all the completed games of a user.
 - Use the `get_game_history` endpoint to retrieve a 'history' of moves and answer messages for each game.
 - Use the `get_average_attempts_remaining` to retrieve the average number of attempts remaining.
 - Use the `get_scores` endpoint to retrieve all the scores of all the users unordered.
 - Use the `get_user_scores` endpoint to retrieve all the scores of a user.
 - Use the `get_high_scores` endpoint to retrieve the players total scores ordered with the best first (the player with the lowest number of attemps to guess).
 - Use the `get_user_ranking` endpoint to retrieve all players ordered by victories/losses ratio (with ties broken by the number of victories) .

## Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - index.py: Composite index.
 - main.py: Handler for taskqueue handler.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - In the models folder: `game_class.py`, `score_class.py` and `user_class.py`  Entities, forms and messages definitions including helper methods.

## Endpoints Included:
 - **`create_user`**
    - Path: 'user'
    - Method: POST
    - Parameters: `user_name`, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. `user_name` provided must be unique. Will raise a ConflictException if a User with that `user_name` already exists.
    
 - **`new_game`**
    - Path: 'game'
    - Method: POST
    - Parameters: `user_name`, `category_1_animals_2_food_3_jobs`
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. `user_name` provided must correspond to an existing user (will raise a NotFoundException if not).
    Category must be chosen between 1(animals), 2(food) or 3(jobs). Will raise a NotFoundException if not.
    Also adds a task to a task queue to update the average moves remaining for
    active games.
     
 - **`make_move`**
    - Path: 'game/{`urlsafe_game_key`}'
    - Method: PUT
    - Parameters: `urlsafe_game_key`, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' (a single letter or a whole word) and returns the updated state of the game. If this causes a game to end, a corresponding Score entity will be created.
    Will raise a ForbiddenException if the game has been cancelled or is over.

 - **`cancel_game`**
    - Path: '`game_canc`/{`urlsafe_game_key`}'
    - Method: PUT
    - Parameters: `urlsafe_game_key`
    - Returns: Message confirming game deletion
    - Description: Allows users to cancel a game in progress but not 
      a completed game (a Boolean field identify cancelled games).
      Will raise a NotFoundException if the User does not exist.

 - **`get_game`**
    - Path: 'game/{`urlsafe_game_key`}'
    - Method: GET
    - Parameters: `urlsafe_game_key`
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
      Will raise a NotFoundException if the Game does not exist.

 - **`get_user_active_games`**
    - Path: 'active_games/user/{`user_name`}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: GameForms
    - Description: Returns all active Games played by the selected player.
      Will raise a NotFoundException if the User does not exist.

 - **`get_user_cancelled_games`**
    - Path: '`cancelled_games`/user/{`user_name`}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: GameForms
    - Description: Returns all cancelled Games played by the selected player.
      Will raise a NotFoundException if the User does not exist.

 - **`get_user_completed_games`**
    - Path: '`completed_games`/user/{`user_name`}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: GameForms
    - Description: Returns all completed Games played by the selected player.
      Will raise a NotFoundException if the User does not exist.
 
 - **`get_game_history`**
    - Path: '`game_history`/{`urlsafe_game_key`}'
    - Method: GET
    - Parameters: `urlsafe_game_key`
    - Returns: StringMessage with the sequene of guesses and answers of a game
    - Description: Returns a history of moves and answer messages for each game
      Will raise a NotFoundException if the Game does not exist

 - **`get_average_attempts_remaining`**
    - Path: 'games/`average_attempts`'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.
    
 - **`get_scores`**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **`get_user_scores`**
    - Path: 'scores/user/{`user_name`}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player
     (unordered).
      Will raise a NotFoundException if the User does not exist.
    
 - **`get_high_scores`**
    - Path: '`high_scores`/user/{`user_name`}'
    - Method: GET
    - Parameters: `max_results_to_show` (optional)
    - Returns: ScoreForms. 
    - Description: Returns all players total Scores ordered with the best 
     (lowest) first.
    
- **get_user_rankings**
    - Path: '`user_ranking`'
    - Method: GET
    - Parameters: None
    - Returns: UserForms. 
    - Description: Returns all players ordered by victories/losses ratio (with ties broken by the number of victories).

## Models Included:
 - **User**
    - Stores unique `user_name`, email address (optional) and winning ratio.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
## Forms Included:
 - **UserForm**
    - Representation of a user's Ranking (user_name, email, ratio, victories,
    losses).

 - **UserForms**
    - Multiple UserForm container.

 - **GameForm**
    - Representation of a Game's state (`urlsafe_key`, `attempts_remaining`,
    `word_category`, `game_over` flag, `game_cancelled` flag, message and
    `user_name`).

 - **GameForms**
    - Multiple GameForm container.

 - **NewGameForm**
    - Used to create a new game (`user_name`, attempts)

 - **MakeMoveForm**
    - Inbound make move form (guess).

 - **ScoreForm**
    - Representation of a completed game's Score (`user_name`, date, won flag,
    guesses).

 - **ScoreForms**
    - Multiple ScoreForm container.

 - **StringMessage**
    - General purpose String container.