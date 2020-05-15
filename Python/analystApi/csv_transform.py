# Python script to query REST-API from empirica-systeme, see https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", sett http://creativecommons.org/licenses/by/4.0/
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

import os
import csv
import json
import random
import configparser
import sys

from analystApi import api_basic
import logging
import argparse
import math
import traceback
from concurrent.futures import ThreadPoolExecutor
from os.path import expanduser


def execute_query_per_csv_line(args):
    try:
        line, values_to_add, csv_writer = args
        collected_errormessages = []
        # Each Input-Line is a Query. Instanciate accordingly
        isq = api_basic.immobrain_search_query()

        # Add the Columns from CSV.
        # Columns are quite likely to contain filter-variables.
        # Add all variables as filters.
        # If a column doesnt look like a valid filter complain but continue.
        for column_name in line:
            if column_name.lower() in ['id', 'kommentar', 'comment']:
                # Let's not complain about comments and ID being invalid filters.
                continue
            try:
                isq.add_column(column_name, line[column_name].strip())
            except Exception as e:
                logging.info("Could not add column %s" % (column_name))
                logging.warning(str(e))

                collected_errormessages.append(str(e))

        # Execute Querys and collect values as required.
        for value in values_to_add:
            try:
                isq.collect(value)
            except Exception as e:
                logging.warning(str(e))
                collected_errormessages.append(str(e))

                # There is little reason to continue. It _might_ yield results
                # but realistically speaking a retry will happen anyway.
                # Die quickly so we don't bloat with errors
                break

        query_pretty = ''
        try:
            query_pretty = json.dumps(isq.to_query(), indent=4, sort_keys=True)
        except:
            # If an error prevents a query from coming into play ( e.g. missing adress )
            # skip
            pass
        # Pythonic "merge dicts"
        # Output-Row should contain "old"-Value and whatever is new.
        output_row = {**(line), **{'distance_used': isq.get_distance_used(),
                                   'precision': isq.get_precision(),
                                   'query': query_pretty,
                                   },
                      **(isq.data)}
        output_row['QUERY-ID'] = isq.id

        logging.debug(output_row)
        csv_writer.writerow(output_row)

        # Regardless of logging, this is expected output:
        print(" %s, %s => %s %s " % (line['ID'], line['Adresse'], isq.id,
                                     'OK' if not collected_errormessages else '/'.join(collected_errormessages)))
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])


def main():
    parser = argparse.ArgumentParser()

    # CSV-File is always required.
    parser.add_argument(
        'csvfile', help='The CSV to load. Output will have an _executed-suffix')

    # It is not verbose, unless ticked
    parser.add_argument(
        '--verbose', help='Turn to a nice verbosity', action='store_true')
    parser.add_argument(
        '--veryverbose', help='Turn to maximum verbosity', action='store_true')
    parser.add_argument(
        '--testonepercent',
        help='Test one percent of the entrys only. Helps validating the job itself.',
        action='store_true')
    args = parser.parse_args()

    home = expanduser("~")
    login_file = '%s/analystApi.login' % (home)

    # If verbosity is required, jump to debug.
    if args.veryverbose:
        target_loglevel = logging.DEBUG
    elif args.verbose:
        target_loglevel = logging.INFO
    else:
        target_loglevel = logging.FATAL
    logging.basicConfig(
        level=target_loglevel)

    logging.info("Starting against ")
    # Load our configuation-file. Complain and exit if this fails.
    try:
        config = configparser.ConfigParser()
        config.read_file(open(login_file))
        if config.get('global', 'password') == 'YYY':
            # seems like we hit a template-file here. Error out.
            # On the off-chance that someone uses 'YYY' as password
            # we happily take the chance to punish the users choice.
            raise Exception("Template-File found. Please use real credentials")
    except Exception as e:
        logging.fatal("Could not load '%s'" % (login_file,))
        template_login_file_contents = """
[global]
username = XXX
password = YYY
endpoint = https://api.empirica-systeme.de
values_to_add = count /aggregated/kosten_je_flaeche/MEDIAN
include_unknown = False

"""

        logging.fatal("""File 'analystApi.login' is required in your home directory.

!!!!!

%s

!!!!

An empty template has been created.
""" % (template_login_file_contents,))

        # Let's not nest exceptions here. If the file can not be written now
        # there is little reason in continuing our endeavour.
        with open(login_file, 'w') as f:
            f.write(template_login_file_contents)

        raise e

    # Push credentials and endpoints into the api_basic module.
    # Refactoring might move there variables into one of the contained classes
    # but for now it seems more appropriate to provide a 'global' configuration in
    # the context of a scripts execution.
    api_basic.username = config.get('global', 'username')
    api_basic.password = config.get('global', 'password')
    csv_file = args.csvfile
    api_basic.endpoint = config.get('global', 'endpoint')
    api_basic.include_unknown_default = False
    if config.get('global', 'include_unknown'):
        logging.info("Default_Value for Unknown-Values Set")
        api_basic.include_unknown_default = config.get('global', 'include_unknown')

    values_to_add = config.get('global', 'values_to_add').split(' ')

    # Open Input-CSV
    logging.debug("Loading from %s" % (csv_file))
    with open(csv_file) as filehandle:
        csv_reader = csv.DictReader(filehandle, delimiter=',')

        # Open Output-CSV
        # Output-CSV has more columns than input, so input-columns + QUERY-ID + whatever
        # we're looking for needs to be inserted
        fieldnames_out = csv_reader.fieldnames + \
                         ['--RESULTS--', 'QUERY-ID', 'distance_used',
                          'precision', 'query'] + values_to_add

        (csv_file_base, csv_file_type) = os.path.splitext(csv_file)
        csv_writer = csv.DictWriter(
            open(
                csv_file_base + '_executed.csv', 'w'),
            delimiter=',',
            fieldnames=fieldnames_out)
        csv_writer.writeheader()

        # Fetch all lines early. CSVs in here should not span many megabytes
        # and it helps us detect parsing-errors early.
        csv_entrys = [line for line in csv_reader]

        # In test-mode - reduce list to one percent of itself.
        # Rounding should be ceil'd, otherwise we might just pull nothing.
        if args.testonepercent:
            csv_entrys = random.sample(
                csv_entrys, math.ceil(len(csv_entrys) * 0.01))

        # for line in csv_entrys:
        #    execute_query_per_csv_line(line, values_to_add, csv_writer)

        with ThreadPoolExecutor(max_workers=8) as executor:
            tasks = [(line, values_to_add, csv_writer) for line in csv_entrys]
            results = executor.map(execute_query_per_csv_line, tasks)

        # actually collect things
        for result in results:
            pass

    logging.debug("Done")


if __name__ == "__main__":
    main()
