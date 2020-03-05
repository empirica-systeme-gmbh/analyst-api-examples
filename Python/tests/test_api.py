# Python script to query REST-API from empirica-systeme, see https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", sett http://creativecommons.org/licenses/by/4.0/
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

from analystApi import api_basic


def test_connect(test_client):
    print(api_basic.username)
    api_basic.immobrain_search_query()

    assert 1 == 1


def test_count(test_client):
    demoset = {  "ID": '1',
                "Adresse": "Brunsstr. 31, 72074 Tübingen",
                "Segment": "WHG_M",
                "Adresse::distance": 1,
                "fl_wohnen::von": 190,
                "fl_wohnen::bis": 200,
                 }

    isq = api_basic.immobrain_search_query()
    for column_name in demoset:
        try:
            isq.add_column(column_name, demoset[column_name])
        except Exception as e:
            print(e)

    for value in ('count',):
        isq.collect( value )

    assert isq.data['count']==6.0


def test_types_id_is_invalid_filter(test_client):
    isq = api_basic.immobrain_search_query()
    try:
        isq.add_column('ID','1')
    except Exception as e:
        print(e)
        if 'is not a valid Filtercolumn' in str(e):
            assert True
            return
    assert False

def test_types_address_is_valid_filter(test_client):
    isq = api_basic.immobrain_search_query()
    isq.add_column('Adresse','Trompeterallee 108 Wickrath')
    assert True

def test_types_address_is_valid_filter_but_contains_nonsense(test_client):
    isq = api_basic.immobrain_search_query()
    try:
        isq.add_column('Adresse','Wo der Pfeffer wächst')
    except:
        assert True
        return
    assert False


def test_types_(test_client):
    isq = api_basic.immobrain_search_query()

    isq.add_column('objekttyp_fein','7 8')
    assert True


def test_regressiontest_a(test_client):
    """
Beispiel A: Ich Sage:
    oeig_vermietet_janein::includeUNKNOWN;oeig_vermietet_janein::includeTRUE; oeig_vermietet_janein::includeFALSE
TRUE; FALSE; FALSE

Und Will:
"includeFalse": FALSE,
            "includeTrue": FALSE,
            "includeUnknown": true,
            "var": "oeig_vermietet_janein"
    """
    
    isq = api_basic.immobrain_search_query()
    isq.add_column("oeig_vermietet_janein::includeUNKNOWN", 'TRuE')
    isq.add_column("oeig_vermietet_janein::includeTRUE", 'FALSE')
    isq.add_column("oeig_vermietet_janein::includeFALSE", 'FALSE')
    print(isq.to_query() )
    assert isq.to_query()['yesNoFilters'][0]['includeTrue'] == False
    assert isq.to_query()['yesNoFilters'][0]['includeFalse'] == False
    assert isq.to_query()['yesNoFilters'][0]['includeUnknown'] == True
    # Also check if we can obtain a result with some demo-values
    isq.add_column('Adresse', 'Trompeterallee 108 Wickrath')
    isq.add_column('Segment', 'WHG_M')
    isq.collect('count')

def test_regressiontest_b(test_client):
    """
Beispiel A: Ich Sage:
    oeig_vermietet_janein::includeUNKNOWN; oeig_vermietet_janein::includeTRUE; oeig_vermietet_janein::includeFALSE
NULL;TRUE;NULL;

Und Will:
"includeTrue": true,
            "includeUnknown": false,
            "includeFalse": false,
            "var": "oeig_vermietet_janein"
    """
    
    isq = api_basic.immobrain_search_query()
    isq.add_column("oeig_vermietet_janein::includeUNKNOWN", 'NULL')
    isq.add_column("oeig_vermietet_janein::includeTRUE", 'TRUE')
    isq.add_column("oeig_vermietet_janein::includeFALSE", 'NULL')
    print(isq.to_query() )
    assert isq.to_query()['yesNoFilters'][0]['includeTrue'] == True
    assert 'includeFalse' not in isq.to_query()['yesNoFilters'][0] or isq.to_query()['yesNoFilters'][0]['includeFalse'] == False
    assert 'includeUnknown' not in isq.to_query()['yesNoFilters'][0] or isq.to_query()['yesNoFilters'][0]['includeUnknown'] == False
    # Also check if we can obtain a result with some demo-values
    isq.add_column('Adresse', 'Trompeterallee 108 Wickrath')
    isq.add_column('Segment', 'WHG_M')
    isq.collect('count')

def test_regressiontest_c(test_client):
    """
Mit 1 und 0 noch nicht ganz sauber, denn 1 wird bei bla::unknown und bla::false noch zu false
    """
    
    isq = api_basic.immobrain_search_query()
    isq.add_column("oeig_vermietet_janein::includeUNKNOWN", '0')
    isq.add_column("oeig_vermietet_janein::includeTRUE", '1')
    isq.add_column("oeig_vermietet_janein::includeFALSE", '0')
    print(isq.to_query() )
    assert isq.to_query()['yesNoFilters'][0]['includeTrue'] == True
    assert 'includeFalse' not in isq.to_query()['yesNoFilters'][0] or isq.to_query()['yesNoFilters'][0]['includeFalse'] == False
    assert 'includeUnknown' not in isq.to_query()['yesNoFilters'][0] or isq.to_query()['yesNoFilters'][0]['includeUnknown'] == False
    # Also check if we can obtain a result with some demo-values
    isq.add_column('Adresse', 'Trompeterallee 108 Wickrath')
    isq.add_column('Segment', 'WHG_M')
    isq.collect('count')
