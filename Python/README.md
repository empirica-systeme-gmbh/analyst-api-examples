Python-Analyst-API
----


Description
----
The Python-Analyst-API is a set of functions and classes to interact with api.empirica-systeme.de

At its heart there is "immobrain-search-query". This is an instance to the API itself. Given an adress and various filters it
will materialize the given parameters and return the results.

`csv_transform` is the csv-approach in using this class. It takes CSV-Files and calls the api for each line, adding new information on its way.


Installation / Build
----

```shell
apt update
apt install -y python3-pip
sudo python3 setup.py install
```

Alternatively try
```shell
python3 setup.py install --user
```


Uninstall
----

```shell
sudo pip3 uninstall analyst-api-python
```
or if you used `--user` when installing:
```shell
pip3 uninstall analyst-api-python
```


Basic Usage
----

Required local files:
- `Adressen_Demo.csv`
- `analystApi.login`

Add required data in `analystApi.login`:
- username = ###.###
- password = #####
- endpoint = https://api.empirica-systeme.de
- include_unknown = True or False #(define wether you want to include unknown values)
- values_to_add = count /aggregated/kosten_je_flaeche/MEDIAN /aggregated/kosten_je_flaeche/AVG /aggregated/kosten/AVG #(define the values yu want to add to your file)

Example:
```
[global]
username = max.mustermann
password = 12mxf_21ppq
endpoint = https://api.empirica-systeme.de
values_to_add = count /aggregated/kosten_je_flaeche/MEDIAN /aggregated/kosten/AVG
include_unknown = False
```


Filter settings:
----

- Filter variables are defined by column names in the header, filter values by column values
  - To add `min` or `max` values for a variable, use "variable::von" in header for `min` and "variable::bis" for `max`
  - To add `true` or `false` values for a boolean variable use: "variable::includeTRUE", "variable::includeFALSE" or "variable::includeUNKNOWN" with (with "1" or "true" or TRUE as column value) 

Special Filter:
---- 
- Adresse: define the center of periphery search use header `Adresse`
  - define default distance of periphery search use header `Adresse::distance`
  - define max distance for "maximum distance minimum count approach" use header `Adresse::maxdistance`
  - define min count for "maximum distance minimum count approach" use header `Adresse::mincount`
- Segment: define the segment to query (e.g. `WHG_K` = flats for purchase)

Unvalid filter settings are ignored


Get Results:
----
Then, in the folder `Python` where the `setup.py` is located, execute the command

```shell
analystApi_csv filename.csv --testonepercent
```
The results of your query are stored in "filename_executed.csv"


Interpretation of result columns:
----

- /count in results is NULL --> address could not been found
- /count in result is 0 --> address have been found, but no matching cases in radius (check filter settings or max distance)



Example:
----
Executing the command

```shell
analystApi_csv Adressen_Demo.csv --testonepercent
```
will produce an output like

> POO-2321S, Brunsstr. 31, 72074 Tübingen => 7055099 OK

and a new file `Adressen_Demo_executed.csv` will be created containing the results.
