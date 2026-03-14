class TUDelftCliError(Exception):
    pass


class AuthenticationError(TUDelftCliError):
    pass


class SessionExpiredError(TUDelftCliError):
    pass


class PortalChangedError(TUDelftCliError):
    pass


class ValidationError(TUDelftCliError):
    pass

class LoginTimeoutError(TUDelftCliError):
    pass
