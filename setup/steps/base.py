"""Abstract base class for all build steps."""
from __future__ import annotations

from abc import ABC, abstractmethod

from setup.config import BoomiConfig
from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.api.datahub_api import DataHubApi
from setup.api.platform_api import PlatformApi
from setup.ui import console as ui


class BaseStep(ABC):
    """Abstract base for all build steps.

    Provides shared access to config, APIs, and UI.  Subclasses implement
    the abstract properties (step_id, name, step_type) and execute().
    """

    def __init__(
        self,
        config: BoomiConfig,
        platform_api: PlatformApi,
        datahub_api: DataHubApi,
    ) -> None:
        self.config = config
        self.platform_api = platform_api
        self.datahub_api = datahub_api

    @property
    @abstractmethod
    def step_id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def step_type(self) -> StepType: ...

    @property
    def depends_on(self) -> list[str]:
        return []

    @abstractmethod
    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus: ...
