from app.core.exceptions import BaseServiceError


class TemplateNotFoundError(BaseServiceError): ...


class TemplateNameExistsError(BaseServiceError): ...


class TemplateInUseError(BaseServiceError): ...
