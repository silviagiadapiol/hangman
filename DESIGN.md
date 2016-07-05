#Full Stack Nanodegree Project 4 Reflections on the Design

I first wrote a simple python program that run the hangman game
in order to analyze the game flow starting from a solid base.
I then tried to translate it in api but it was'n t easy.
It worked better when I stop thinking about like a single program
and divided the problem in small steps. I modeled the main entities
and Forms and wrote the endpoints, testing every step with GAE 
and fixing the errors using the logs and the Datastore Viewer.
Once I got the first basic version functioning, I started adding the new
endpoints required and I also added some features like the possibility
for the user to chose the secret word category, to help him with his
guesses; I also figured out how to optimized the answer messages to
organize them in a better way and to make them more meaningful.
The README file was written and constantly updated during the process
to reflect the changes and track the new features. 

 - User class:
   I had to add the properties victories, losses and ratio in order
   to store the values that define the players ranking. I also added
   the UserForm class, the UserForms class and the get_user_rankings
   endpoint to present the results to the user. 
   At the beginning I had some issues with the type conversion 
   integer-float but then I solved it with a cast.

 - Game class:  
    I added the properties secretWord , missedLetters, correctLetters
    and word_category necessary to handle the specific game logic.
    I added the boolean field game_cancelled to store the flag about the
    deletion of a specific game and the game_history field to store the
    game history of guesses and answers.
    I modified the make_move enpoint to reflect the hangman logic and to
    store the information about the player raking and the game history. 
    This was the most complicated endpoint and required a lot of tries 
    and logs reading, expecially for the ranking feature. 
    I added the cancel_game endpoint in order to allow a game deletion by
    activating the game_cancelled flag; I had to modify the make_move 
    endpoint to prevent a cancelled game to be played.
    I modified the get_game endpoint in order to communicate if a chosen
    game was active, completed or cancelled.
    I added the get_active_user_games, the get_cancelled_user_games
    and the  get_completed user_games endpoint to retrieve all the active
    games, the cancelled games or the completed games of a user.
    
 - Score class:  
    I didn't change much because the existing properties fitted for the
    hangman game logic, I just added the get_high_scores endpoint



