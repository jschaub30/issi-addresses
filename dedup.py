'''
Remove duplicates and clean up list of student addresses
'''

import csv
from pathlib import Path

from nltk import edit_distance
from states import STATE_ABBREV, STATE_MAP

HEADERS = ['First name', 'Last name', 'Street address', 'City', 'State', 'Zip', 'Email address', 'Source', 'Match']
def read_data(fname):
    """Read TSV of file and set some default values"""
    with open(fname, "r") as fid:
        fname = Path(fname).stem
        csv_file = csv.DictReader(fid, delimiter="\t")
        data = []

        for line in csv_file:
            line['State'] = line['State'].upper()
            if line['State'] == "NOT AVAILABLE":
                continue
            if line['State'] not in STATE_ABBREV:
                # print(f"Fixing {line['State']}")
                found = False
                for abbrev in STATE_ABBREV:
                    if line['State'].upper() == STATE_MAP[abbrev].upper():
                        line['State'] = abbrev
                        found = True
                        break
                if not found:
                    raise Exception(line['State'])
            if 'street1' in line:
                line['Street address'] = line.pop('street1') + ', ' + line.pop('street2')
            for field in HEADERS:
                # set default values
                if field not in line:
                    line[field] = ''
            # fields = ['Last name', 'First name', 'Street address', 'City', 'State']
            fields = ['Last name', 'Street address', 'Zip']
            line['Zip'] = line['Zip'].split('-')[0]
            key = ''
            for field in fields:
                key += line[field].upper()
            line['key'] = key
            line['Source'] = fname
            line['Match'] = ""
            data.append(line)
    return data

def show(p):
    return f"{p['Source']} {p['First name']} {p['Last name']} {p['Street address']}, {p['City']}, {p['State']}"


def find_uniques(all_data):
    matches = 0
    prev_key = ''
    uniques = []
    prev_line = {}
    for line in all_data:
        if edit_distance(prev_key, line['key']) <= 2:
            line["Match"] = "MATCH"
            prev_line["Match"] = "MATCH"
            if prev_line['Email address'] and prev_line['First name']:
                # don't do anything--use the previous record
                pass
            else:
                uniques[-1] = line
            print(f"MATCH FOUND:\n{show(line)}")
            print(f"{show(prev_line)}")
            matches += 1
        else:
            uniques.append(line)

        prev_line = line
        prev_key = line['key']
    print(f"{matches} matches found")
    return uniques


def save_data(fname, data):
    ''' Save data to TSV file '''
    Path(fname).parent.mkdir(parents=True, exist_ok=True)
    with open(fname, 'w') as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames = HEADERS)

        # writing headers (field names)
        writer.writeheader()

        # writing data rows
        for line in data:
            short = {}
            for key in line:
                if key in HEADERS:
                    short[key] = line[key]
            writer.writerow(short)
    print(f"{len(data)} records written to {fname!r}")


all_data = []
for fn in ["SAU Families(1).tsv", "SAU Teachers(1).tsv", "ISSIUsers2019 (1).tsv", "SAA mailing list 2022.tsv"]:
    all_data += read_data(fn)
all_data = sorted(all_data, key=lambda x: x.get('key'))
uniques = find_uniques(all_data)
uniques2 = find_uniques(uniques)
print(len(uniques))
print(len(uniques2))

save_data("all.tsv", all_data)
save_data("unique.tsv", uniques2)
