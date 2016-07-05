"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import webapp2
from google.appengine.api import mail, app_identity
from api import Hangman
from models.user_class import User
from models.game_class import Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email
        who has incompleted games. Called every 6 hours
        using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email is not None)
        for user in users:
            games = Game.query().filter(
                Game.user == user.key and Game.game_over is False)
            if games:
                subject = 'This is a reminder for Hangman game!'
                body = 'Hi {}, complete your Hangman game!'.format(user.name)
                # the arguments to send_mail are: from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                               user.email,
                               subject,
                               body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        Hangman._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
