class GIMSException(Exception):
    pass

class MemoryNotFoundException(GIMSException):
    pass

class UserNotFoundException(GIMSException):
    pass

class ConversationNotFoundException(GIMSException):
    pass

class EvaluationException(GIMSException):
    pass

class RetrievalException(GIMSException):
    pass

class StorageException(GIMSException):
    pass

class CircuitBreakerOpenException(GIMSException):
    pass

class AuthenticationException(GIMSException):
    pass

class AuthorizationException(GIMSException):
    pass
