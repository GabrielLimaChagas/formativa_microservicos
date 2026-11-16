class DomainException(Exception):
    """Exceção base de domínio."""
    pass

class EntityNotFoundException(DomainException):
    """Lançada quando uma entidade não for encontrada."""
    pass

class ValidationException(DomainException):
    """Lançada quando os dados da entidade forem inválidos."""
    pass
