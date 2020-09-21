import arrow
import click
import csv
import fastkml
from pathlib import Path
import pprint
from shapely.geometry import Point
import sys
import zipfile

KML_NS = '{http://www.opengis.net/kml/2.2}'
GOOGLE_EARTH_SCALE_DEFAULT = 1.1

def get_rows(csv_file):
    rows = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += [row]

    return rows

def has_lat_lon(row):
    """No point in processing this row if it doesn't have coordinates"""
    clean = {}
    for k, v in row.items():
        clean[k.lower()] = v # Some sheets have capital Ls, some have lower case.
    if 'latitude' in clean.keys() and 'longitude' in clean.keys():
        return clean['latitude'] and clean['longitude']
    return False

def parse_date(date):
    """Get an ISO8601 formatted string for a date in the CSV"""

    # The date format isn't perfectly consistent between rows, try some common formats before giving up
    try:
        return arrow.get(date, 'M/D/YYYY').isoformat()
    except arrow.parser.ParserMatchError:
        return arrow.get(date, 'M/D/YY').isoformat()

def process_members(members):
    kml_data = {}
    kml_data['name'] = "Members"
    kml_data['icon'] = 'http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png'
    kml_data['data'] = []
    rows = get_rows(members)

    for row in rows:
        row_data = {}
        if not has_lat_lon(row):
            continue
        row_data['label'] = row['Label\n"callsign"']
        row_data['lat'] = float(row['latitude'])
        row_data['long'] = float(row['longitude'])
        row_data['metadata'] = {}
        row_data['metadata']['licence_class'] = row['License class']
        for cap in ['HF', '6m', '2m', '220 Mhz', '440 MHz', 'HamWan', 'DMR']:
            row_data['metadata'][cap.lower().replace(" ", "_")] = True if row[cap] == 'Yes' else False
        row_data['metadata']['data_entry_by'] = row['Data Entry by']
        row_data['metadata']['notes'] = row['Notes']
        if row['date modified']:
            row_data['metadata']['date_modified'] = parse_date(row['date modified'])
        kml_data['data'] += [row_data]

    return kml_data

def process_repeaters(repeaters):
    kml_data = {}
    kml_data['name'] = "Repeaters"
    kml_data['icon'] = 'http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png'
    kml_data['data'] = []
    rows = get_rows(repeaters)

    for row in rows:
        row_data = {}
        if not has_lat_lon(row):
            continue
        row_data['label'] = row['Label\n"name / output freq / tone"']
        row_data['lat'] = float(row['latitude'])
        row_data['long'] = float(row['longitude'])
        row_data['metadata'] = {}
        row_data['metadata']['data_entry_by'] = row['Data Entry by']
        row_data['metadata']['notes'] = row['Notes']
        row_data['metadata']['comments'] = row['If you have comments or make an edit, please summarize them in this column']
        if row['date modified']:
            row_data['metadata']['date_modified'] = parse_date(row['date modified'])

        kml_data['data'] += [row_data]
    
    return kml_data

def process_winlink(winlink):
    kml_data = {}
    kml_data['name'] = "Winlink Nodes"
    kml_data['icon'] = 'http://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png'
    kml_data['data'] = []
    rows = get_rows(winlink)

    for row in rows:
        row_data = {}
        if not has_lat_lon(row):
            continue
        row_data['label'] = row['Label\n"name / freq / call"']
        row_data['lat'] = float(row['latitude'])
        row_data['long'] = float(row['longitude'])
        row_data['metadata'] = {}
        row_data['metadata']['data_entry_by'] = row['Data Entry by']
        row_data['metadata']['notes'] = row['Notes']
        row_data['metadata']['comments'] = row['If you have comments or make an edit, please summarize them in this column']
        if row['date modified']:
            row_data['metadata']['date_modified'] = parse_date(row['date modified'])

        kml_data['data'] += [row_data]
    
    return kml_data

def process_assembly_points(assembly_points):
    kml_data = {}
    kml_data['name'] = "Assembly Points"
    kml_data['icon'] = 'http://maps.google.com/mapfiles/kml/pushpin/pink-pushpin.png'
    kml_data['data'] = []
    rows = get_rows(assembly_points)

    for row in rows:
        row_data = {}
        if not has_lat_lon(row):
            continue
        row_data['label'] = row['Name']
        row_data['lat'] = float(row['Latitude'])
        row_data['long'] = float(row['Longitude'])
        row_data['metadata'] = {}
        row_data['metadata']['data_entry_by'] = row['Data Entry by']
        row_data['metadata']['notes'] = row['Notes']
        row_data['metadata']['type'] = row['Type of assembly point (choose one)']
        if row['date modified']:
            row_data['metadata']['date_modified'] = parse_date(row['date modified'])

        kml_data['data'] += [row_data]

    return kml_data

def generate_kml(kml_data, doc_name, doc_id):
    kml = fastkml.kml.KML()
    doc = fastkml.kml.Document(KML_NS, doc_id, doc_name, 'Generated at {} UTC'.format(arrow.utcnow().ctime()))
    kml.append(doc)

    id_counter = 1
    pp = pprint.PrettyPrinter(indent=4)

    for place_type in kml_data:
        folder = fastkml.kml.Folder(KML_NS, place_type['name'], place_type['name'], '')
        doc.append(folder)

        style = fastkml.kml.Style(KML_NS, place_type['name'])
        icon_style = fastkml.styles.IconStyle(KML_NS, scale=GOOGLE_EARTH_SCALE_DEFAULT, icon_href=place_type['icon'])
        style.append_style(icon_style)
        doc.append_style(style)

        for item in place_type['data']:
            point = fastkml.kml.Placemark(KML_NS, str(id_counter), item['label'], pp.pformat(item['metadata']),
                                            styleUrl="#{}".format(place_type['name']))
            point.geometry = Point(item['long'], item['lat'])
            folder.append(point)
            id_counter += 1

    return kml, id_counter

def write_file(kml, output_filename):
    path = Path(output_filename)
    kml_string = kml.to_string(prettyprint=True)

    # Try to be nice to the user and autodetect which format they would like.
    if path.suffix == '.kml':
        with path.open('w') as f:
            f.write(kml_string)
    elif path.suffix == '.kmz':
        with zipfile.ZipFile(path, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=5) as f:
            f.writestr("{}.kml".format(path.stem), kml_string)
    else:
        print('Output filename must end with ".kmz" or ".kml"')
        sys.exit(2)


@click.command()
@click.option('--members', '-m', type=str)
@click.option('--repeaters', '-r', type=str)
@click.option('--winlink', '-w', type=str)
@click.option('--assembly-points', '-a', type=str)
@click.option('--doc-name', '-d', required=True, type=str)
@click.option('--doc-id', '-i', required=True, type=str)
@click.option("--output", '-o', required=True, type=str)
def generate_kmz(members, repeaters, winlink, assembly_points, doc_name, doc_id, output):
    kml_data = []

    if not any([members, repeaters, winlink, assembly_points]):
        print("Must specify at least one of --members, --repeaters, --winlink, or --assembly_points, exiting")
        sys.exit(1)

    if members:
        kml_data += [process_members(members)]

    if repeaters:
        kml_data += [process_repeaters(repeaters)]

    if winlink:
        kml_data += [process_winlink(winlink)]

    if assembly_points:
        kml_data += [process_assembly_points(assembly_points)]

    kml, count = generate_kml(kml_data, doc_name, doc_id)

    write_file(kml, output)
    print("Successfully processed {} data points.".format(count))