"""
src/client/exceptions.py

Custom exception hierarchy for SD-WAN automation.
All exceptions are designed to carry structured context for logging and rollback decisions.
"""


class SDWANError(Exception):
    """Base exception for all SD-WAN automation errors."""
    pass


class VManageAuthError(SDWANError):
    """Raised when vManage login fails or session expires."""
    pass


class VManageAPIError(SDWANError):
    """Raised when a vManage API call returns an unexpected error response."""

    def __init__(self, message: str, status_code: int = 0, url: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.url = url

    def __str__(self) -> str:
        return f"{super().__str__()} [HTTP {self.status_code}] URL={self.url}"


class VManageTimeoutError(SDWANError):
    """Raised when a vManage API call or deploy poll exceeds its timeout."""
    pass


class TemplateNotFoundError(SDWANError):
    """Raised when a required feature or device template cannot be found."""

    def __init__(self, template_name: str, template_id: str = ""):
        self.template_name = template_name
        self.template_id = template_id
        super().__init__(
            f"Template not found: name='{template_name}' id='{template_id}'"
        )


class ValidationError(SDWANError):
    """Raised when input validation fails before any API call is made."""

    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed — field='{field}' value='{value}': {reason}")


class DuplicateVariableError(ValidationError):
    """Raised when duplicate variable keys are detected in the input data."""

    def __init__(self, variable_key: str):
        super().__init__(
            field="variable",
            value=variable_key,
            reason="Duplicate variable key detected — will not silently overwrite"
        )


class DeploymentError(SDWANError):
    """Raised when a vManage template deployment fails on the device."""

    def __init__(self, message: str, action_id: str = "", device: str = ""):
        self.action_id = action_id
        self.device = device
        super().__init__(f"{message} [action_id={action_id}] [device={device}]")


class RollbackError(SDWANError):
    """Raised when rollback itself fails — requires manual intervention."""
    pass


class ProfileNotFoundError(SDWANError):
    """Raised when no site profile matches the given region/metallic_type."""

    def __init__(self, region: str, metallic_type: str, design_type: str = ""):
        self.region = region
        self.metallic_type = metallic_type
        self.design_type = design_type
        super().__init__(
            f"No profile found for region='{region}' metallic_type='{metallic_type}' "
            f"design_type='{design_type}' — using default profile"
        )


class SiteConfigError(SDWANError):
    """Raised when a site's configuration is missing required fields."""
    pass


class BackupError(SDWANError):
    """Raised when template backup creation fails."""
    pass


class IdempotencySkip(Exception):
    """
    Raised (not an error) when a use case is skipped due to idempotency.
    Catch this to log a skip rather than treating it as a failure.
    """

    def __init__(self, uc_key: str, deployed_at: str = ""):
        self.uc_key = uc_key
        self.deployed_at = deployed_at
        super().__init__(
            f"{uc_key} already deployed at {deployed_at} — use --force to override"
        )
