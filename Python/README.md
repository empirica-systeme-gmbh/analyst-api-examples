Python-Analyst-API
----


Description
----
The Python-Analyst-API is a set of functions and classes to interact with api.empirica-systeme.de

At its heart there is "immobrain-search-query". This is an instance to the API itself. Given an adress and various filters it
will materialize the given parameters and return the results.

`csv_transform` is the csv-approach in using this class. It takes CSV-Files and calls the api for each line, adding new information on its way.

There is also a [Swagger documentation of the API](https://api-stage.empirica-systeme.de/api-docs/#/Queries/createQuery)


Basic Usage
----

Required local files:
- `test.csv`
- `analystApi.login` in your user's homedirectory

Add required data in `analystApi.login`:
- username = ###.###
- password = #####
- endpoint = https://api.empirica-systeme.de
- include_unknown = True or False #(define wether you want to include unknown values)
- values_to_add = count /aggregated/kosten_je_flaeche/MEDIAN /aggregated/kosten_je_flaeche/AVG /aggregated/kosten/AVG #(define the values you want)

Example:
```
[global]
username = max.mustermann
password = 12mxf_21ppq
endpoint = https://api.empirica-systeme.de
include_unknown = False
values_to_add = count /aggregated/kosten_je_flaeche/MEDIAN /aggregated/kosten/AVG
```


Filter settings
----

- Filter variables are defined by column names in the header, filter values by column values
  - To add `min` or `max` values for a variable, use "variable::von" in header for `min` and "variable::bis" for `max`
  - To add `true` or `false` values for a boolean variable use: "variable::includeTRUE", "variable::includeFALSE" or "variable::includeUNKNOWN" with (with "1" or "true" or TRUE as column value) 

Special Filters
---- 
- Adresse: define the center of periphery search use header `Adresse`
  - define default distance of periphery search use header `Adresse::distance`
  - define max distance for "*maximum distance minimum count approach*" use header `Adresse::maxdistance`
  - define min count for "*maximum distance minimum count approach*" use header `Adresse::mincount`
- Segment: define the segment to query (e.g. `WHG_K` = flats for purchase)

The "*maximum distance minimum count approach*" will increase the query distance until there are at least `mincount` results or until `maxdistance` is reached, whatever happens first. This way only one query is required instead of repeatedly submitting queries with increasing distance until `mincount` is reached.

Unvalid filter settings are ignored

Get Results
----
Then, in the folder `Python` where the `analystApi.sh` is located, execute the command

```shell
./analystApi.sh test.csv 
```
The results of your query are stored in "test_executed.csv"


Interpretation of result columns
----

- `count` in results is NULL --> address has not been georeferenced sucessfully
- `count` in result is 0 --> address have been found, but no matching cases in radius (check filter settings or max distance)
- `query` contains the query string that was sent using the [API](https://api-stage.empirica-systeme.de/api-docs/#/Queries/createQuery)



Example
----
Executing the command in folder `Python`:

```shell
./analystApi.sh test.csv 
```
will produce an output like

> POO-2321S, Einsteinufer 63 a, 10587 Berlin => 7055099 OK

and a new file `test_executed.csv` will be created containing the results.
