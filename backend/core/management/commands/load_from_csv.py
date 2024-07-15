from django.core.management.base import BaseCommand

from ._csv_parsers import csv_parse
from ._introspects import get_name_model_dict


class Command(BaseCommand):
    help = 'Load data to database from CSV'

    def handle(self, *args, **options):
        model = get_name_model_dict()[options['model'][0]]
        files = options['files']
        for file in files:
            csv_parse(self, file, model)

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--files',
            action='append',
            type=open,
            nargs='+',
            required=True,
            help='CSV files to load'
        )
        parser.add_argument(
            '-m',
            '--model',
            action='store',
            choices=get_name_model_dict().keys(),
            nargs=1,
            required=True,
            help='Model into which the values are loaded')
