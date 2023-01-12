'''
Remove duplicates and clean up list of student addresses
'''

import csv
from pathlib import Path

from nltk import edit_distance
from states import STATE_ABBREV, STATE_MAP

HEADERS = ['First name', 'Last name', 'Street address', 'City', 'State', 'Zip', 'Email address', 'Source', 'Match']


def split_address(addr):
    '''
    Split address string into street, city, state, zip
    Return dict
    '''
    try:
        street, city_state, zipcode, _ = addr.split('\n')
    except ValueError:
        print(addr)
        raise
    return {
        'Street address': street.strip(),
        'City': city_state.split(',')[0].strip(),
        'State': city_state.split(',')[1].strip(),
        'Zip': zipcode.strip()
    }


def norm_state(state):
    """
    Normalize state as 2 letter abbreviation
    >>> norm_state('UT')
    'UT'
    >>> norm_state('Utah')
    'UT'
    """
    state = state.upper()
    if state not in STATE_ABBREV:
        found = False
        for abbrev in STATE_ABBREV:
            if state.upper() == STATE_MAP[abbrev].upper():
                state = abbrev
                found = True
                break
        if not found:
            raise Exception(f"Couldn't find state={state}")
    return state


def read_issi(fname):
    """Read CSV of file and set some default values"""
    with open(fname, "r") as fid:
        fname = Path(fname).stem
        csv_file = csv.DictReader(fid, delimiter=",")
        data = []

        for line in csv_file:
            first, last = line['Parent Name'].strip().rsplit(' ', 1)
            line['First name'] = first
            line['Last name'] = last
            line['Email address'] = line['Parent email']
            line.update(split_address(line['Address']))
            line['State'] = norm_state(line['State'])
            for field in HEADERS:
                # set default values
                if field not in line:
                    line[field] = ''
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
            line['State'] = norm_state(line['State'])
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
    return f"{p['Source'][:9]}    {p['First name']} {p['Last name']} {p['Street address']}, {p['City']}, {p['State']}"


def find_uniques(all_data):
    matches = 0
    prev_key = ''
    uniques = []
    prev_line = {}
    for line in all_data:
        if edit_distance(prev_key, line['key']) <= 4:
            line["Match"] = "MATCH"
            prev_line["Match"] = "MATCH"
            if prev_line['Email address'] and prev_line['First name']:
                # don't do anything--use the previous record
                pass
            elif not line['First name']:
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
    print(f"\n{matches} matches found\n\n")
    return uniques


def save_data(fname, data):
    ''' Save data to CSV file '''
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


def main():
    """ Read and merge 4 files """
    all_data = []
    all_data += read_issi("data/issi_2022.csv")

    for fn in ["data/SAU Families(1).tsv", "data/SAU Teachers(1).tsv", "data/SAA mailing list 2022.tsv"]:
        all_data += read_data(fn)
    all_data = sorted(all_data, key=lambda x: x.get('key'))
    uniques = find_uniques(all_data)
    uniques2 = find_uniques(uniques)
    print(len(uniques))
    print(len(uniques2))

    save_data("all.csv", all_data)
    save_data("unique.csv", uniques2)


if __name__ == '__main__':
    main()
