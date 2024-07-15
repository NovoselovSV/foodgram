import csv


def csv_parse(command, file, model):
    with open(file[0].name, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                model.objects.get_or_create(**row)
            except Exception as error:
                command.stdout.write(row)
                command.stdout.write(error)
