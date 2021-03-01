### Exceptions ###
class APIQueryFailure(RuntimeError):
    """
    Raised when querying an api fails
    """

    def __init__(self, status_code, text):
        self.status_code = status_code
        super().__init__(text)


class UnknownOrganization(APIQueryFailure):
    """
    Raised when an organization is requested, but it is not found.
    """

    def __init__(self, org_name):
        return super().__init__(404, f"Unknown organization: {org_name}")
