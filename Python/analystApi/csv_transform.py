# Python script to query REST-API from empirica-systeme, see
# https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", see
# http://creativecommons.org/licenses/by/4.0/
#
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

import argparse
import configparser
import csv
import datetime
import json
import logging
import math
import os
import random
import sys
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from os.path import expanduser

from analystApi import api_basic, psql_writer
from analystApi.api_basic import call_with_retries, MAX_RETRY_COUNT, MAX_RETRY_TIME, RETRY_DELAY
from analystApi.utils import RepeatingTimer

brokenColumns = []
DEFAULT_CLIENT_WORKERS = 4

progress_num_total: int = 0
progress_num_success: int = 0
progress_num_fail: int = 0


class ExecutionResult:
    def __init__(self, object_id: str, query_id: int, successful: bool):
        self.object_id = object_id
        self.query_id = query_id
        self.successful = successful


def execute_query_per_csv_line(args):
    if datetime.time.hour == 23 and datetime.time.min >= 50:
        # Pause um Mittnernacht da die Analyst neustarten
        time.sleep(60 * 15)

    try:
        line: OrderedDict = args[0]
        values_to_add: OrderedDict = args[1]
        csv_writer: csv.DictWriter = args[2]

        collected_errormessages = []
        entry_id: str = 'NONE'

        # Each Input-Line is a Query. Instanciate accordingly
        isq = api_basic.immobrain_search_query()

        # Add the Columns from CSV.
        # Columns are quite likely to contain filter-variables.
        # Add all variables as filters.
        # If a column doesnt look like a valid filter complain but continue.
        for column_name in line.copy():
            if column_name in brokenColumns:
                continue

            if column_name.lower() == 'id':
                entry_id = line[column_name].strip()

            if column_name.lower() in ['id', 'kommentar', 'comment']:
                # Let's not complain about comments and ID being invalid filters.
                continue
            try:
                isq.add_column(column_name, line[column_name].strip())
            except Exception as e:
                collected_errormessages.append(str(e))

                if column_name.lower() in ['adresse', 'adresse']:
                    continue

                brokenColumns.append(column_name)
                logging.warning(f"{entry_id}: Could not add column {column_name}")
                logging.warning(f"{entry_id}: {str(e)}")

        # Execute Querys and collect values as required.
        for value in values_to_add:
            try:
                # Wenn schon COUNT=0 rauskam, dann nichts weiter probieren...
                if "count" in isq.data and isq.data['count'] <= 0:
                    logging.warning(f"count is 0, überspring {value} für Eintrag {entry_id}")
                    continue

                call_with_retries(MAX_RETRY_COUNT, MAX_RETRY_TIME, RETRY_DELAY, isq.collect, value)
            except Exception as e:
                logging.warning(f"{entry_id}: {str(e)}")
                collected_errormessages.append(str(e))

                # There is little reason to continue. It _might_ yield results
                # but realistically speaking a retry will happen anyway.
                # Die quickly so we don't bloat with errors
                break

        query_pretty = ''
        try:
            query_pretty = json.dumps(isq.to_query(), indent=4, sort_keys=True)
        except Exception:
            # If an error prevents a query from coming into play ( e.g. missing adress )
            # skip
            pass
        # Pythonic "merge dicts"

        # Output-Row should contain "old"-Value and whatever is new.
        output_row = OrderedDict()
        output_row.update(line)
        output_row.update({'distance_used': isq.get_distance_used(),
                           'precision': isq.get_precision(),
                           'query': query_pretty})
        output_row.update(isq.data)
        output_row['QUERY-ID'] = isq.id

        logging.debug(output_row)
        csv_writer.writerow(output_row)

        # Regardless of logging, this is expected output:
        logging.debug(" %s, %s => %s %s " % (line['ID'], line['Adresse'], isq.id,
                      'OK' if not collected_errormessages else '/'.join(collected_errormessages)))

        return ExecutionResult(entry_id, isq.id, not collected_errormessages)

    except Exception as e:

        if str(e) == str("User must be in the role rest"):
            logging.critical("Check your API user: must be in the role 'rest'")
            sys.exit()

        logging.exception("Unexpected Exception", e)
        return ExecutionResult('', 0, False)


def main():
    parser = argparse.ArgumentParser()

    # CSV-File is always required.
    parser.add_argument(
        'csvfile', help='The CSV to load. Output will have an _executed-suffix')

    # It is not verbose, unless ticked
    parser.add_argument('-v', '--verbose', help='Turn to a nice verbosity', action='store_true')
    parser.add_argument('-V', '--veryverbose', help='Turn to maximum verbosity', action='store_true')
    parser.add_argument(
        '--testonepercent',
        help='Test one percent of the entrys only. Helps validating the job itself.',
        action='store_true')
    args = parser.parse_args()

    home = expanduser("~")
    login_file = '%s/analystApi.login' % home

    # If verbosity is required, jump to debug.
    if args.veryverbose:
        target_loglevel = logging.DEBUG
    elif args.verbose:
        target_loglevel = logging.INFO
    else:
        target_loglevel = logging.WARN

    logging.basicConfig(
        level=target_loglevel,
        format='%(asctime)-15s %(levelname)-8s %(message)s'
    )

    logging.info("Starting.. ")
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
        logging.fatal("Could not load '%s'" % login_file)
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
    global_config = config['global']
    api_basic.username = global_config.get('username')
    api_basic.password = global_config.get('password')
    csv_file = args.csvfile
    api_basic.endpoint = global_config.get('endpoint')
    client_workers = global_config.getint('client_workers', fallback=DEFAULT_CLIENT_WORKERS)

    logging.info("Using API at " + api_basic.endpoint)

    api_basic.include_unknown_default = False
    if global_config.get('include_unknown'):
        logging.info("Default_Value for Unknown-Values Set")
        api_basic.include_unknown_default = global_config.getboolean('include_unknown')

    values_to_add = config.get('global', 'values_to_add').split(' ')

    if "count" not in values_to_add:
        values_to_add.insert(0, "count")

    # Open Input-CSV
    logging.debug("Loading from %s" % csv_file)
    with open(csv_file) as filehandle:
        csv_reader = csv.DictReader(filehandle, delimiter=',')

        # Output-CSV has more columns than input, so input-columns + QUERY-ID + values_to_add...
        fieldnames_out = concatenate(
            [csv_reader.fieldnames, ['--RESULTS--', 'QUERY-ID', 'distance_used', 'precision', 'query'], values_to_add])

        (csv_file_base, csv_file_type) = os.path.splitext(csv_file)
        output_csv_file = csv_file_base + '_executed.csv'

        psql_writer.write_to_file(output_csv_file, csv_reader.fieldnames, values_to_add)

        csv_writer = csv.DictWriter(
            open(output_csv_file, 'w'),
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

        if client_workers > 29:
            client_workers = 29
        if client_workers > 1:
            logging.info("Using %s clients..." % client_workers)

        api_basic.poolsize = client_workers
        logging.info(f"Set poolsize to {api_basic.poolsize}")

        global progress_num_total
        global progress_num_success
        global progress_num_fail
        progress_num_total = len(csv_entrys)

        t = RepeatingTimer(60.0, print_progress, daemon=True)
        t.start()

        with ThreadPoolExecutor(max_workers=client_workers) as executor:
            tasks = [(line, values_to_add, csv_writer) for line in csv_entrys]
            executor_map = executor.map(execute_query_per_csv_line, tasks)
            for item in executor_map:
                if item.successful:
                    progress_num_success += 1
                else:
                    progress_num_fail += 1
                # print(f'{num_fail + num_success}/{num_total} - success: {num_success}, failed: {num_fail}')
                # print(f'{item.query_id}, {item.object_id}, {item.successful}')

        # actually collect things
        t.cancel()
        t.call_function()
        executor.shutdown(wait=True)

    logging.info("Done")
    logging.info('Script completed, see output/log for any errors')


def print_progress():
    logging.info(f'Processed {progress_num_fail + progress_num_success} of {progress_num_total} entries '
                 f'- success: {progress_num_success}, failed: {progress_num_fail}')


def chained(sequences):
    for seq in sequences:
        yield from seq


def concatenate(sequences):
    sequences = iter(sequences)
    first = next(sequences)
    if hasattr(first, 'join'):
        return first + ''.join(sequences)
    return first + type(first)(chained(sequences))


if __name__ == "__main__":
    main()
