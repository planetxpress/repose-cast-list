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
            cast_list.append({'character': character,
                            'species': species,
                            'resides': resides,
                            'employment': employment,
                            'pb': pb,
                            'writer': writer
                            })
    return cast_list


def generate_html(cast_list):
    html = """
    <!DOCTYPE html>
    <html>
    <title>Repose Cast List</title>
    <meta charset="utf-8">
    <meta HTTP-EQUIV="CACHE-CONTROL" CONTENT="NO-CACHE">
    <meta HTTP-EQUIV="EXPIRES" CONTENT="Sat, 01 Jan 2000 00:00:01 GMT">
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <script src="https://code.jquery.com/jquery-latest.min.js"></script>
    <script src="https://storage.googleapis.com/%s/tablesort.js"></script>
    <script>
    $(function(){
        $('#castlist').tablesort();
    });
    </script>
    
    <body class="w3-container">
    <h2>Repose Cast List</h2>
    <table id="header text">
        <tr><tb>Click the table headers to sort by category.<br>
        An <i>italicized</i> character is represented by multiple PBs.<br>
        <a href="https://www.welcometorepose.com/cast-list.html">Return to the image Cast List</a>.
        <br></td></tr>
    </table>
    <p>Last Updated: %s UTC
    <table id="castlist" class="w3-table-all">
    <thead>
    <tr style="background-color: #C8C7C7">
        <th style="cursor:pointer">Character</th>
        <th style="cursor:pointer">Species</th>
        <th style="cursor:pointer">Resides</th>
        <th style="cursor:pointer">Employment</th>
        <th style="cursor:pointer">PB</th>
        <th style="cursor:pointer">Writer</th>
    </tr>
    </thead>
    <tbody>
""" % (os.getenv('BUCKET_NAME'), datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M'))

    for c in cast_list:
        html += """
        <tr class="item">
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
        </tr>
""" % (c['character'], c['species'], c['resides'], c['employment'], c['pb'], c['writer'])

    html += """
    </tbody>
    </table>
    </body>
    </html>
"""
    return html


def upload(html):
    bucket_name = os.getenv('BUCKET_NAME')
    destination_object = os.getenv('CAST_FILE')
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_object)
    blob.upload_from_string(html, content_type='text/html')
    blob.make_public()


def pubsub_trigger(event,context):
    main()


def main():
    cast_list = get_cast()
    html = generate_html(cast_list)
    upload(html)

if __name__ == '__main__':
    main()