import csv


def csv_parse(file, model):
    with open(file[0].name, encoding='utf-8') as f:
        print(f'In file {f.name}')
        reader = csv.DictReader(f)
        for row in reader:
            try:
                model.objects.get_or_create(**row)
            except Exception as e:
                print(row)
                print(e)
    print('File done')
