import string

import analystApi.api_basic
from analystApi.api_basic import immobrain_search_query


def write_to_file(basename, columns, values_to_add):
    lines = construct_file_content(basename, columns, values_to_add)
    with open(basename + '.psql', 'w') as psql_file:
        psql_file.writelines(lines)


def construct_file_content(basename, columns, values_to_add):
    column_lines = construct_column_definitions(columns, values_to_add)

    lines = """
psql -c 'DROP TABLE IF EXISTS {basename};'

psql -c 'CREATE TABLE {basename}
(
{column_lines}
)'

psql -c "\\copy {basename} from {basename}.csv delimiter ',' csv header;"
""".format(basename=basename, column_lines=column_lines)
    return lines


def construct_column_definitions(columns, values_to_add):
    if not analystApi.api_basic.column_documentation:
        immobrain_search_query.load_variable_documentation()

    # lowercase copy of columns
    cols = [x.lower() for x in columns]

    col_id = 'ID'
    basic_cols = {
        col_id: 'text NOT NULL',
        'Adresse': 'text NOT NULL',
        'Adresse::distance': 'numeric',
        'Adresse::mincount': 'integer',
        'Adresse::maxdistance': 'integer',
        'segment': 'text'
    }

    filter_cols = {
        'startdate::von': 'date',
        'enddate::bis': 'date',
        'baujahr::von': 'integer',
        'baujahr::bis': 'integer',
        'flaeche::von': 'numeric',
        'flaeche::bis': 'numeric',
        'fl_grundstueck::von': 'numeric',
        'fl_grundstueck::bis': 'numeric',
        'zust_klassen_empirica': 'integer',
        'aus_klassen_empirica': 'integer',
        'oeig_neubau_janein': 'boolean',
    }

    if not contains(col_id, cols):
        raise Exception(f'Must contain {col_id} column')

    lines = []

    # Write the first static block
    for col_name, col_type in basic_cols.items():
        append_col_and_remove_if_exists(lines, col_name, col_type, cols)

    lines.append('')

    # Write the filter  block
    for col_name, col_type in filter_cols.items():
        append_col_and_remove_if_exists(lines, col_name, col_type, cols)

    lines.append('')
    lines.append('results_start_here text,')
    lines.append('')
    lines.append('queryid bigint,')
    lines.append('distance_used numeric,'),
    lines.append('precision text,'),
    lines.append('query text,'),
    lines.append('')

    for v in values_to_add:
        lines.append(f'"{v}" numeric,')

    lines.append('')
    lines.append(f'PRIMARY KEY ("{col_id}")')

    lines_string = '\n'.join([f'    {line}' for line in lines])
    # remove last comma
    return lines_string


def append_col_and_remove_if_exists(lines, name, col_type, columns_lowercase):
    if contains(name, columns_lowercase):
        lines.append(f'"{name}" {col_type},')
        remove(name, columns_lowercase)


def contains(needle, haystack_lowercase):
    return needle.lower() in haystack_lowercase


def remove(needle, haystack_lowercase):
    haystack_lowercase.remove(needle.lower())
