import os

import analystApi.api_basic
from analystApi.api_basic import immobrain_search_query


def write_to_file(output_filename, columns, values_to_add):
    (basename, fileext) = os.path.splitext(output_filename)
    tablename = os.path.basename(basename)
    lines = construct_file_content(tablename, output_filename, columns, values_to_add)
    with open(basename + '.psql', 'w') as psql_file:
        psql_file.writelines(lines)


def construct_file_content(tablename, filename, columns, values_to_add):
    column_lines = construct_column_definitions(columns, values_to_add)
    lines = f"""
psql -c 'DROP TABLE IF EXISTS {tablename};'

psql -c 'CREATE TABLE {tablename}
(
{column_lines}
)'

# CSV einlesen..
psql -c "\\copy {tablename} from {filename} delimiter ',' csv header;"

# Georef anreichern...
psql -c "INSERT INTO georef SELECT id,adresse,
                                    (query::json->'peripherySpatialFilter'->'coordinate'->'lat')::text::numeric oadr_koord_lat_epsg4326,
                                    (query::json->'peripherySpatialFilter'->'coordinate'->'lon')::text::numeric oadr_koord_lon_epsg4326 
                                    FROM {tablename} WHERE precision='HOUSE'
                                    ON CONFLICT DO NOTHING"
                                    
"""
    return lines


def construct_column_definitions(columns, values_to_add):
    if not analystApi.api_basic.column_documentation:
        immobrain_search_query.load_variable_documentation()

    # lowercase copy of columns
    cols = [x.lower() for x in columns]

    col_id = 'id'
    basic_cols = {
        col_id: 'text NOT NULL',
        'adresse': 'text NOT NULL',
        'adresse::distance': 'numeric',
        'adresse::mincount': 'integer',
        'adresse::maxdistance': 'integer',
        'segment': 'text',
    }

    if not contains(col_id, cols):
        raise Exception(f'Must contain {col_id} column')

    lines = []

    # Handle all columns
    while cols:
        col = cols.pop(0)       # Remove first element
        if col in [k.lower() for k in basic_cols]:
            for col_name, col_type in basic_cols.items():
                if col == col_name.lower():
                    append_col(lines, col_name, col_type)
                    break
        else:
            col_filter = immobrain_search_query.get_filter_for_column(col)
            if col_filter is None:
                col_type = 'text'
            else:
                col_type = col_filter.get_sql_type()
            append_col(lines, col, col_type)

    lines.append('')
    lines.append('results_start_here text,')
    lines.append('')
    lines.append('queryid bigint,')
    lines.append('distance_used numeric,'),
    lines.append('precision text,'),
    lines.append('query json,'),
    lines.append('')

    for v in values_to_add:
        lines.append(f'"{v}" numeric,')

    lines.append('')
    lines.append(f'PRIMARY KEY ("{col_id}")')

    lines_string = '\n'.join([f'    {line}' for line in lines])
    # remove last comma
    return lines_string


def append_col(lines, name, col_type):
    lines.append(f'"{name}" {col_type},')


def append_col_and_remove_if_exists(lines, name, col_type, columns_lowercase):
    if contains(name, columns_lowercase):
        lines.append(f'"{name}" {col_type},')
        remove(name, columns_lowercase)


def contains(needle, haystack_lowercase):
    return needle.lower() in haystack_lowercase


def remove(needle, haystack_lowercase):
    haystack_lowercase.remove(needle.lower())
