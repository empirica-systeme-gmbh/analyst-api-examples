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

analystApi_csv Adressen_Demo.csv --testonepercent 
 POO-2321S, Brunsstr. 31, 72074 Tübingen => 7055099 OK
