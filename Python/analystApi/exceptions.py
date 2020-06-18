class AnalystApiError(Exception):
    pass


class MissingOrInvalidParameter(AnalystApiError):
    """Required parameters are missing, or have invalid values (Status Code: 400)"""
    pass


class AccessDenied(AnalystApiError):
    """Access to requested variables or region not granted by license (Status Code: 403)"""
    pass


class SegmentNotFoundInLicense(AnalystApiError):
    """Given segment not found in your license (Status Code: 404)"""
    pass


class QueryLimitReached(AnalystApiError):
    """The yearly limit of submitted queries for the license is reached"""
    pass
