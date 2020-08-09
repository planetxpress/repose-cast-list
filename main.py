import datetime
import re
import requests
import os
from bs4 import BeautifulSoup
from google.cloud import storage


def get_cast():
    response = requests.get('https://www.welcometorepose.com/cast-list.html').text
    parsed = BeautifulSoup(response, 'lxml')
    characters = parsed.find_all('div', {'class': 'paragraph'})
    cast_list = list()
    for c in characters:
        input = c.text.encode('ascii', 'ignore')
        data = input.decode()
        match = re.search('(.*)Species:(.*)Resides:(.*)Employment:(.*)PB:(.*)\[Writer:(.*)\]', data )
        if not match:
            continue
        pb_list = match.group(5).lstrip().split('&')
        for p in pb_list:
            pb = p.lstrip()
            character = match.group(1).lstrip()
            species = match.group(2).lstrip()
            resides = match.group(3).lstrip()
            employment = match.group(4).lstrip()
            writer = match.group(6).lstrip()
            if len(pb_list) > 1:
                character = '<i>%s</i>' % character
                species = '<i>%s</i>' % species
                resides = '<i>%s</i>' % resides
                employment = '<i>%s</i>' % employment
                writer = '<i>%s</i>' % writer
            cast_list.append(
                {
                    'character': character,
                    'species': species,
                    'resides': resides,
                    'employment': employment,
                    'pb': pb,
                    'writer': writer
                }
            )
    return cast_list


def generate_html(cast_list):
    with open('html/header.html', 'r') as f:
        header = f.read().format(
            bucket=os.getenv('BUCKET_NAME'),
        )

    cast_rows = ''
    with open('html/cast-row.html', 'r') as f:
        row = f.read()
    for c in cast_list:
        cast_rows += row.format(
            character=c['character'],
            employment=c['employment'],
            pb=c['pb'],
            resides=c['resides'],
            species=c['species'],
            writer=c['writer']
        )

    with open('html/footer.html', 'r') as f:
        footer = f.read().format(
            time=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        )

    html = header + cast_rows + footer
    return html


def upload(bucket_name, file_name, string):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.metadata = {'Cache-Control': 'private, max-age=0, no-transform'}
    blob.upload_from_string(string, content_type='text/html')
    blob.make_public()


def pubsub_trigger(event,context):
    main()


def main():
    cast_list = get_cast()
    html = generate_html(cast_list)
    upload(os.getenv('BUCKET_NAME'), os.getenv('CAST_FILE'), html)

if __name__ == '__main__':
    main()
