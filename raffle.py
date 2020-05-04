import csv
import os
from collections import OrderedDict
from random import shuffle, randrange

import click

COMMA_DELIMITER = ','
TAB_DELIMITER = '\t'
RESIDENTS_FILENAME = {COMMA_DELIMITER: 'residents.csv', TAB_DELIMITER: 'residents.tsv'}
RESIDENTS_FIELDS = ('id', 'slots', 'disabled', 'elderly', 'defaulting')
SLOTS_FILENAME = {COMMA_DELIMITER: 'slots.csv', TAB_DELIMITER: 'slots.tsv'}
SLOTS_FIELDS = ('id', 'disabled', 'elderly')
OUTPUT_FILENAME = {COMMA_DELIMITER: 'output.csv', TAB_DELIMITER: 'output.tsv'}


@click.command()
@click.option('--directory',
              help='Path of the directory containing the input files - defaults to ./input',
              default='input',
              type=click.Path(exists=True))
@click.option('--delimiter',
              help='delimiter used in input and output files - defaults to tab',
              default='tab',
              type=click.Choice(['comma', 'tab'],
                                case_sensitive=False))
def main(directory, delimiter):
    delimiter = COMMA_DELIMITER if delimiter == 'comma' else TAB_DELIMITER
    absolute_directory = os.path.join(os.path.dirname(__file__), directory)
    residents, slots = read_input(absolute_directory, delimiter)
    output = do_raffle(residents, slots)
    write_output(absolute_directory, output, delimiter)


def read_input(directory, delimiter):
    residents_file_name = directory + os.path.sep + RESIDENTS_FILENAME[delimiter]
    slots_file_name = directory + os.path.sep + SLOTS_FILENAME[delimiter]
    check_file(residents_file_name)
    check_file(slots_file_name)
    residents = parse_file(residents_file_name, RESIDENTS_FIELDS, delimiter, format_resident, RESIDENTS_FIELDS[0])
    slots = parse_file(slots_file_name, SLOTS_FIELDS, delimiter, format_slots, SLOTS_FIELDS[0])

    if len(slots) < len(residents):
        click.echo(
            'number of slots must be greater or equal than number of residents')
        exit(1)

    residents = list(residents.items())
    shuffle(residents)

    return OrderedDict(residents), slots


def parse_file(file_name, fieldnames, delimiter, format_function, id_key):
    parsed = {}
    with open(file_name, mode='r', newline='') as file:
        reader = csv.DictReader(file, fieldnames=fieldnames, delimiter=delimiter)
        for index, line in enumerate(reader):
            format_function(index, line)
            id_value = line[id_key]
            if id_value in parsed:
                click.echo('Duplicated id %s in file %s line %d' % (id_value, file_name, index + 1))
                exit(1)
            parsed[id_value] = line
    return parsed


def check_file(file_name):
    if not os.path.isfile(file_name):
        click.echo(file_name + ' must exist')
        exit(1)
    if os.path.getsize(file_name) <= 0:
        click.echo(file_name + ' must not be empty')
        exit(1)


def format_resident(index, resident):
    for key, value in resident.items():
        # Check if values are not missing or empty
        if value is None:
            click.echo('%s is missing in line %d' % (key, index + 1))
            exit(1)
        # Check if 'id' is not empty
        if key == RESIDENTS_FIELDS[0]:
            resident[key] = format_id(index, key, value)
        # Check if 'slots' is a number and is not smaller than 1
        elif key == RESIDENTS_FIELDS[1]:
            resident[key] = format_integer(index, key, value)
        # Check if 'disabled' 'elderly' 'defaulted' are bool
        elif key in (
            RESIDENTS_FIELDS[2], RESIDENTS_FIELDS[3], RESIDENTS_FIELDS[4]):
            resident[key] = format_bool(index, key, value)


def format_slots(index, slot):
    for key, value in slot.items():
        # Check if values are not missing or empty
        if value is None:
            click.echo('%s is missing in line %d' % (key, index + 1))
            exit(1)
        # Check if 'id' is not empty
        if key == SLOTS_FIELDS[0]:
            slot[key] = format_id(index, key, value)
        # Check if 'disabled' 'elderly' are bool
        elif key in (SLOTS_FIELDS[1], SLOTS_FIELDS[2]):
            slot[key] = format_bool(index, key, value)


def do_raffle(residents, slots):
    output = {}
    slots_disabled = [slot[SLOTS_FIELDS[0]] for slot in slots.values() if
                      slot[SLOTS_FIELDS[1]]]
    slots_elderly = [slot[SLOTS_FIELDS[0]] for slot in slots.values() if
                     slot[SLOTS_FIELDS[2]]]
    slots_rest = [slot[SLOTS_FIELDS[0]] for slot in slots.values() if
                  not slot[SLOTS_FIELDS[1]] and not slot[SLOTS_FIELDS[2]]]
    # For each resident
    for resident in residents.values():
        slots_for_resident = []
        # For each slot the resident is entitled
        for i in range(resident[RESIDENTS_FIELDS[1]]):
            # if the resident is disabled and has not already been awarded a slot
            if resident[RESIDENTS_FIELDS[2]] and len(slots_for_resident) <= 0:
                slots_for_resident.append(
                    select_random_slot(slots_disabled, RESIDENTS_FIELDS[2]))
            # if the resident is elderly and not defaulting and has not already been awarded a slot
            elif resident[RESIDENTS_FIELDS[3]] and not resident[
                RESIDENTS_FIELDS[4]] and len(slots_for_resident) <= 0:
                slots_for_resident.append(
                    select_random_slot(slots_elderly, RESIDENTS_FIELDS[3]))
            # if the resident is the rest
            else:
                slots_for_resident.append(select_random_slot(slots_rest))
        output[resident[RESIDENTS_FIELDS[0]]] = slots_for_resident
    return output


def select_random_slot(slots, category='regular'):
    remaining_slots = len(slots)
    if remaining_slots <= 0:
        click.echo('No more %s slots available' % category)
        exit(1)
    return slots.pop(randrange(remaining_slots))


def format_id(index, key, value):
    value = value.strip()
    if len(value) <= 0:
        click.echo('%s is empty in line %d' % (key, index + 1))
        exit(1)
    return value


def format_integer(index, key, value):
    integer = 0
    try:
        integer = int(value)
    except ValueError:
        click.echo('%s is not an integer in line %d' % (key, index + 1))
        exit(1)
    if integer < 1:
        click.echo('%s is less than 1 in line %d' % (key, index + 1))
        exit(1)
    return integer


def format_bool(index, key, value):
    boolean = False
    value = value.lower()
    if value == 'true':
        boolean = True
    elif value == 'false':
        boolean = False
    else:
        click.echo(
            '%s is not formatted correctly in line %d' % (key, index + 1))
        exit(1)
    return boolean


def write_output(directory, output, delimiter):
    output_file_name = directory + os.path.sep + OUTPUT_FILENAME[delimiter]
    with open(output_file_name, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=delimiter)
        for key, value in output.items():
            writer.writerow([key] + value)


if __name__ == '__main__':
    main()
