class DatabaseError(Exception):
    """Base database exception."""


class RecordNotFoundError(DatabaseError):
    """Record not found."""


class DuplicateRecordError(DatabaseError):
    """Duplicate record found."""


class TransactionError(DatabaseError):
    """Transaction failure."""