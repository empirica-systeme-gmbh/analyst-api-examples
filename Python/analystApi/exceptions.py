class AnalystApiError(Exception):
    """Base class for all Analyst API errors"""
    pass


class AnalystApiGeorefError(AnalystApiError):
    pass


class GeorefAddressInvalid(AnalystApiGeorefError):
    """No or empty address parameter given, or invalid georef address (Status Code: 400)"""
    pass


class GeorefAccessDenied(AnalystApiGeorefError):
    """You are not permitted to use the geo reference API (Status Code: 403)"""
    pass


class GeorefNotFound(AnalystApiGeorefError):
    """No geo reference found for your address query (Status Code: 404)"""
    pass


class GeorefMultipleFound(AnalystApiGeorefError):
    """Multiple georeferences found for your address query (Status Code: 409)"""
    pass


class GeorefOffline(AnalystApiGeorefError):
    """Georeferencing service is offline at the moment"""
    pass


class AnalystApiQueryError(AnalystApiError):
    pass


class QueryMissingOrInvalidParameter(AnalystApiQueryError):
    """Required parameters are missing, or have invalid values (Status Code: 400)"""
    pass


class QueryAccessDenied(AnalystApiQueryError):
    """Access to requested variables or region not granted by license (Status Code: 403)"""
    pass


class QuerySegmentNotFoundInLicense(AnalystApiQueryError):
    """Given segment not found in your license (Status Code: 404)"""
    pass


class QueryLimitReached(AnalystApiQueryError):
    """The yearly limit of submitted queries for the license is reached (Status Code: 429)"""
    pass
