# Python script to query REST-API from empirica-systeme, see https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", sett http://creativecommons.org/licenses/by/4.0/
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

import os
import json
import logging
import requests

username = ''
password = ''
endpoint = ''
include_unknown_default = False

json_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

column_documentation = {}


class immobrain_search_query:
    session = requests.Session()

    def __init__(self, id=None):
        if id == '':
            self.id = None
        else:
            self.id = id

        self.filter = {}
        self.meta_data = None
        self.details = None
        self.data = {}

        if not column_documentation:
            immobrain_search_query.load_variable_documentation()

    @staticmethod
    def load_variable_documentation():
        r = immobrain_search_query.session.get(endpoint + '/vars/',
                                               auth=(username, password),
                                               headers=json_headers)
        r.encoding = 'utf-8'
        if r.status_code >= 300:
            raise Exception(json.loads(r.text)['error'])
        # Iterate over every possible variable
        for item in json.loads(r.text)['vars']:
            column_documentation[item['key']] = item

    def get_filter_for_column(self, column):
        if column.lower() == 'id':
            return None
        if column.lower() == 'adresse':
            return get_filter('peripherySpatialFilter')
        if column.lower() == 'segment':
            return get_filter("segmentFilter")
        try:
            # fl_wohnen::von // fl_wohnen::bis
            column = column.split('::')[0].lower()
            return get_filter(column_documentation[column]['filterModelName'])
        except:
            pass
        return None

    def get_precision(self):
        try:
            return self.filter['Adresse'].precision
        except:
            return None

    def get_distance_used(self):
        try:
            return self.details['peripherySpatialFilter']['distance']
        except:
            return None

    def generate_id(self):
        r = immobrain_search_query.session.post(endpoint + '/queries',
                                                auth=(username, password),
                                                data=json.dumps(self.to_query()),
                                                headers=json_headers)
        r.encoding = 'utf-8'
        logging.debug(r.text)
        self.meta_data = json.loads(r.text)
        if r.status_code >= 400:
            raise Exception(self.meta_data["error"])
        self.id = self.meta_data['queryId']
        self.pull_details_for_query()

    def pull_details_for_query(self):
        r = immobrain_search_query.session.get(endpoint + '/queries/%s' % (self.id,),
                                               auth=(username, password),
                                               headers=json_headers)
        r.encoding = 'utf-8'
        logging.debug(r.text)
        self.details = json.loads(r.text)
        if r.status_code >= 400:
            raise Exception(self.details["error"])

    def collect(self, type):
        if not self.id:
            self.generate_id()
        logging.info("Querying: %s" % (self.id))
        r = immobrain_search_query.session.get(endpoint + '/results/%s/%s' % (self.id, type),
                                               auth=(username, password),
                                               headers=json_headers)
        r.encoding = 'utf-8'
        if r.status_code < 300:
            if not 'value' in json.loads(r.text):
                raise Exception("There is no Reply-Value for %s/%s" % (self.id, type))
            self.data[type] = json.loads(r.text)['value']
        else:
            if not self.meta_data:
                logging.warning("QueryID invalid. CSV outdated? Regenerating ID %s .." %
                                (self.id))
                self.generate_id()
                logging.info("New Query-ID = %s" % (self.id))
                self.collect(type)
            # raise Exception(self.data)

    def to_query(self):
        doc = {}
        # Single-Filter
        for filter_name in self.filter:
            if self.filter[filter_name].unique:
                doc[self.filter[filter_name].name] = self.filter[filter_name].to_query()
        # Multiple-Filters.. Toto: Make maintainable
        non_unique_filters = {}
        for filter in self.filter:
            filter_object = self.filter[filter]
            if not filter_object.unique:
                if filter_object.name in non_unique_filters:
                    non_unique_filters[filter_object.name].append(
                        filter_object)
                else:
                    non_unique_filters[filter_object.name] = []
                    non_unique_filters[filter_object.name].append(
                        filter_object)
        for filter_type in non_unique_filters:
            doc[filter_type] = []
            for filter in non_unique_filters[filter_type]:
                doc[filter_type].append(filter.to_query())
        return doc

    def add_filter(self, column):
        # Basically enforcing uniqueness. This is usefull for min/max values :)
        if column in self.filter:
            return

        filter = self.get_filter_for_column(column)
        if not filter:
            raise Exception(
                "Column '%s' is not a valid Filtercolumn" % (column))

        self.filter[column] = filter(column)

    def add_column(self, column, value):
        logging.debug("##" + str(column))
        coltype = column
        bound = None

        if '::' in column:
            (coltype, bound) = column.split('::', 2)

        if value == '':
            return  # empty csv entry..

        self.add_filter(coltype)
        if bound:
            if bound == 'bis':
                self.filter[coltype].set_max(value)
            elif bound == 'von':
                self.filter[coltype].set_min(value)
            elif self.filter[coltype].has_special_key(bound):
                self.filter[coltype].set_special_key(bound, value)
            else:
                raise Exception("This i cannot understand %s for %s!" %
                                (bound, coltype))
        else:
            self.filter[coltype].set_value(value)


def clean_response(response):
    response.encoding = 'utf-8'
    body_as_json = json.loads(response.text)
    if response.status_code < 300:
        return body_as_json
    else:
        raise Exception(body_as_json['error'])


def get_filter(filter_name):
    # Once a column-name is checked against api/vars, we try to find the appropriate
    # class to handle it by type.
    available_filters = {
        "rangeFilter": rangeFilter,
        "rangeDateFilter": rangeDateFilter,
        "timePeriodFilter": timePeriodFilter,
        "peripherySpatialFilter": peripherySpatialFilter,
        "segmentFilter": segmentFilter,
        "categoryFilter": CategoryFilter,
        "booleanFilter": BooleanFilter
    }
    return available_filters[filter_name]


class immobrain_filter:
    def __init__(self):
        self.known_special_keys = []
        self.special_keys = {}

    def set_min(self, value):
        raise NotImplementedError("set_min Not Implemented")

    def set_max(self, value):
        raise NotImplementedError("set_max Not Implemented")

    def set_value(self, value):
        raise NotImplementedError("set_values Not Implemented")

    def to_query(self):
        raise NotImplementedError("to_query Not Implemented")

    def has_special_key(self, key):
        if any([key.lower() == known_attribute.lower() for known_attribute in self.known_special_keys]):
            return True
        return False

    def set_special_key(self, key, value):
        key = \
        [correctly_spelled_key for correctly_spelled_key in self.known_special_keys if correctly_spelled_key.lower()
         == key.lower()][0]
        self.special_keys[key] = value


class segmentFilter(immobrain_filter):
    def __init__(self, column_name):
        super().__init__()
        self.column_name = column_name
        self.name = 'segment'
        self.unique = True
        self.value = None

    def set_value(self, value):
        self.value = value

    def to_query(self):
        return self.value


class CategoryFilter(immobrain_filter):
    def __init__(self, column_name):
        super().__init__()
        self.column_name = column_name
        self.name = 'categoryFilters'
        self.unique = False
        self.value = None

    def set_value(self, value):
        # Split by character is possibly the worst way to identify columns of arbitrary datatypes
        # that may or may not contain strings. Works fine for numerical lists though.
        self.value = value.split(' ')

    def to_query(self):
        return {"var": self.column_name,
                "includedCategoryIds": self.value}


class BooleanFilter(immobrain_filter):
    def __init__(self, column_name):
        self.column_name = column_name
        self.ternary_logic = False
        # if column_name[-1] == '3':
        #    self.ternary_logic = True
        #    logging.info("%s is ternary"%( self.column_name ) ) 
        self.name = 'yesNoFilters'
        self.unique = False
        self.value = None
        self.known_special_keys = ["includeTrue", "includeFalse", "includeUnknown"]
        self.special_keys = {"includeUnknown": include_unknown_default}  # default

    def to_bool(self, value):
        """ Mimmic Java.lang.boolean """
        true = ['true', '1']
        false = ['false', '0']
        if value.lower() in true:
            return True
        if value.lower() in false:
            return False
        # If in doubt - False
        return False

    def to_query(self):
        doc = {"var": self.column_name}
        for special_key in self.special_keys:
            # Booleanfilters currently only support "Boolean attributes"
            # For ease-of-use, work with the boolean interpretation of python for
            # given values
            # This has the potential to be weird.
            doc[special_key] = self.to_bool(self.special_keys[special_key])
        return doc


class rangeFilter(immobrain_filter):
    def __init__(self, column_name):
        super().__init__()
        self.filter_name = column_name
        self.name = 'rangeFilters'
        self.min = None
        self.max = None
        # Is it possible to have multiple of these in an array of filters, or is it exactly one?
        self.unique = False

    def sanitize(self, number):
        # lets assume min/max are numbers.
        # in this case we want to force a common format.
        # If we push XX,X, errors orror. Lets replace ',' with '.'
        try:
            return number.replace(',', '.')
        except:
            pass
        return number

    def set_min(self, min):
        self.min = self.sanitize(min)

    def set_max(self, max):
        self.max = self.sanitize(max)

    def set_value(self, value):
        self.min = float(value) - 2
        self.max = float(value) + 2

    def to_query(self):
        doc = {
            "var": self.filter_name,
            "includeUnknown": include_unknown_default
        }
        if (self.min is not None and self.max is not None) and (float(self.min) > float(self.max)):
            raise Exception("%s has min bigger than max!" % (self.filter_name))
        if self.min is not None:
            doc["minValue"] = self.min
        if self.max is not None:
            doc["maxValue"] = self.max

        return doc


class rangeDateFilter(immobrain_filter):
    def __init__(self, column_name):
        super().__init__()
        self.filter_name = column_name
        self.name = 'rangeDateFilters'
        self.min = None
        self.max = None
        # Is it possible to have multiple of these in an array of filters, or is it exactly one?
        self.unique = False

    def set_min(self, min):
        self.min = min

    def set_max(self, max):
        self.max = max

    def set_value(self, value):
        self.min = float(value) - 2
        self.max = float(value) + 2

    def to_query(self):
        doc = {
            "var": self.filter_name,
            "includeUnknown": include_unknown_default
        }
        if self.min is not None:
            doc["minValue"] = self.min
        if self.max is not None:
            doc["maxValue"] = self.max
        return doc


class timePeriodFilter(immobrain_filter):
    def __init__(self, column_name):
        super().__init__()
        self.filter_name = column_name
        self.name = 'timePeriodFilter'
        self.min = None
        self.max = None
        # Is it possible to have multiple of these in an array of filters, or is it exactly one?
        self.unique = True

    def set_min(self, min):
        self.min = min

    def set_max(self, max):
        self.max = max

    def to_query(self):
        doc = {}
        if self.min is not None:
            doc["from"] = self.min
        if self.max is not None:
            doc["until"] = self.max

        return doc


class peripherySpatialFilter(immobrain_filter):
    def __init__(self, column_name):
        super().__init__()
        self.column_name = column_name
        self.name = 'peripherySpatialFilter'
        self.unique = True

        self.lat = None
        self.lon = None
        self.precision = None
        self.displayName = None
        self.biggerArea = None

        self.known_special_keys = ["distance", "minCount", "maxDistance"]
        self.special_keys = {"distance": .2}  # default
        self.known_error = None

    def set_value(self, value):
        self.adresse = value
        self.get_position()

    def get_position(self):
        logging.debug("Pulling Position for %s" % (self.adresse,))
        r = immobrain_search_query.session.get(endpoint + '/georef',
                                               auth=(username, password),
                                               params={"address": self.adresse},
                                               headers=json_headers)
        try:
            response = clean_response(r)

            self.lat = response["lat"]
            self.lon = response["lon"]
            self.precision = response["precision"]
            self.displayName = response["displayNameDE"]
            self.biggerArea = response["biggerArea"]

        except Exception as e:
            raise (e)

    def to_query(self):

        if not self.lon and not self.lat:
            # No valid GeoRef..
            raise Exception("Address has not been initialized")
        doc = {
            "coordinate": {
                "lat": self.lat,
                "lon": self.lon,
                "precision": self.precision,
                "displayName": self.displayName,
                "biggerArea": self.biggerArea
            },
        }
        for special_key in self.special_keys:
            doc[special_key] = self.special_keys[special_key]
        logging.debug(doc)
        return doc
