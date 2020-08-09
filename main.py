import datetime
import logging
import re
import requests
import os
from bs4 import BeautifulSoup
from google.cloud import storage

def check_env(vars):
    check = True
    for v in vars:
        if not os.getenv(v):
            logging.error('Missing %s in environment' % v)
            check = False
    return check


def get_cast():
    try:
        response = requests.get('https://www.welcometorepose.com/cast-list.html').text
        parsed = BeautifulSoup(response, 'lxml')
        characters = parsed.find_all('div', {'class': 'paragraph'})
    except Exception as ex:
        logging.error(ex)
        raise
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
    # Header
    with open('html/header.html', 'r') as f:
        header = f.read().format(
            bucket=os.getenv('BUCKET_NAME'),
        )
    # Table rows
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
    # Footer
    with open('html/footer.html', 'r') as f:
        footer = f.read().format(
            time=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        )
    html = header + cast_rows + footer
    return html


def upload_string(bucket_name, file_name, content_type, string):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(string, content_type=content_type)
    blob.make_public()


def upload_file(bucket_name, file_name, content_type, source_dir):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename('%s/%s' % (source_dir, file_name))
    blob.make_public()


def main():
    vars = [
        'BUCKET_NAME',
        'CAST_FILE'
    ]
    if not check_env(vars):
        exit(1)
    cast_list = get_cast()
    html = generate_html(cast_list)
    upload_string(os.getenv('BUCKET_NAME'), os.getenv('CAST_FILE'), 'text/html', html)
    upload_dir = 'js'
    for f in os.listdir(upload_dir):
        upload_file(os.getenv('BUCKET_NAME'), f, 'application/javascript', upload_dir)


def pubsub_trigger(event,context):
    main()

if __name__ == '__main__':
    main()
