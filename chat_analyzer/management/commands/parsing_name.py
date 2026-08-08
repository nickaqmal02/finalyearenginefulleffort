from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Greets a person with name and optional age'
    # add_arguments , s sbb plural
    def add_arguments(self, parser):
        # name is positional argument
        parser.add_argument('name', type=str, help='Your name')
        # --age is optional argument
        parser.add_argument('--age', type=int, help='Your age', required=False)

    def handle(self, *args, **options):
        name = options['name']
        age = options.get('age')

        message = f"Hello, {name}!"
        if age:
            message += f" You are {age} years old."

        self.stdout.write(message)

