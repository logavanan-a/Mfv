from django.core.management.base import BaseCommand
from survey.response_mail import *


class Command(BaseCommand):

    help = 'Runs cron for sending mail on survey reponses'

    # C def add_arguments(self, parser):
    # C    parser.add_argument('poll_id', nargs='+', type=int)

    @staticmethod
    def handle(*args, **options):
        survey_responses()
