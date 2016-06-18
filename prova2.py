"""api.py - Create and configure the Game API exposing the resources.
primarily with communication to/from the API's users."""

from __future__ import print_function
import random
attempts=10
words = 'ant baboon badger bat bear beaver'.split()

def getRandomWord(wordList):
  # returns a random string from the passed list of strings.
  wordIndex = random.randint(0, len(wordList)-1)
  return wordList[wordIndex]


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
        guess = raw_input()
        guess = guess.lower()
        if len(guess) != 1:
            print('Enter a single letter!')
        elif guess in guessed:
            print('Letter already guessed. Choose again!')
        elif guess not in 'abcdefghijklmnopqrstuvwxyz':
            print('Please enter a proper LETTER.')
        else:
            return guess

# def playAgain():
#     # True if the player wants to play again, False otherwise
#     print('Do you want to play again? (yes or no)')
#     return raw_input().lower().startswith('y')



print('PLAY HANGMAN')
missedLetters = ''
correctLetters = ''
secretWord = getRandomWord(words)
gameDone = False

while True:
    answer(attempts, missedLetters, correctLetters, secretWord)

    # Let the player type in a letter.
    guess = getGuess(missedLetters + correctLetters)

    if guess in secretWord:
        correctLetters = correctLetters + guess

        # Check if the player has won
        foundAllLetters = True
        for i in range(len(secretWord)):
            if secretWord[i] not in correctLetters:
                foundAllLetters = False
                break
        if foundAllLetters:
            print('Yes! The secret word is "' + secretWord + '"! You have won!')
            gameDone = True
    else:
        missedLetters = missedLetters + guess

        # Check if player has guessed too many times and lost
        if len(missedLetters) == attempts:
            answer(attempts, missedLetters, correctLetters, secretWord)
            print('You are an Hangman!\n'
                  'You have run out of guesses after \n'
                   + str(len(missedLetters)) + ' missed guesses \n' 
                   'and ' + str(len(correctLetters)) + ' correct guesses,\n'
                  'the secret word was "' + secretWord + '"')
            gameDone = True

    #Ask the player if they want to play again (but only if the game is done).
    if gameDone:
        # if playAgain():
        #     missedLetters = ''
        #     correctLetters = ''
        #     gameDone = False
        #     secretWord = getRandomWord(words)
        # else:
        break
