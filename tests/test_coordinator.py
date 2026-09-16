"""Refresh pacing of the coordinator.

Loads coordinator.py against a throwaway Home Assistant stub that records what the
coordinator hands to DataUpdateCoordinator, so the debouncer settings can be
checked without a full HA install.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "viark"

#: Home Assistant's own default, which left channel changes up to 10 s behind.
HA_DEFAULT_COOLDOWN = 10


class _Debouncer:
    def __init__(self, hass, logger, *, cooldown, immediate, function=None):
        self.cooldown = cooldown
        self.immediate = immediate
        self.function = function


class _DataUpdateCoordinator:
    def __class_getitem__(cls, _item):
        return cls

    def __init__(self, hass, logger, **kwargs):
        self.hass = hass
        self.kwargs = kwargs

    async def async_request_refresh(self) -> None:
        """Never awaited here; the tests drive _async_update_data directly."""


class _Hass:
    def __init__(self) -> None:
        self.later: list[tuple[float, object]] = []

    def async_create_task(self, coro):
        coro.close()


CHANNELS = [{"ServiceID": "A"}, {"ServiceID": "B"}]


class FakeClient:
    """Answers the coordinator's requests; tunes to B mid-fetch when asked.

    ``push_during_fetch`` is how many passes see a notification arrive between
    reading the state and reading the playing channel -- the window in which a
    real 2001 would otherwise be lost.
    """

    def __init__(self, push_during_fetch: int = 0) -> None:
        self.on_notification = None
        self.playing = "A"
        self.push_during_fetch = push_during_fetch
        self.passes = 0

    async def state(self):
        self.passes += 1
        if self.push_during_fetch:
            self.push_during_fetch -= 1
            # The box changes channel after state() but before request 3 is read.
            self._pending_switch = True
        else:
            self._pending_switch = False
        return {"ChannelNum": len(CHANNELS), "PowerMode": 1}

    async def channels(self, start, end):
        return CHANNELS

    async def playing_program_id(self, *, strict=False):
        playing = self.playing
        if self._pending_switch:
            self.playing = "B"
            self.on_notification(2001)
        return playing

    async def mute_state(self):
        return False


@pytest.fixture
def coordinator_module(monkeypatch):
    """Import coordinator.py with stubs that vanish after the test.

    monkeypatch restores sys.modules, so the stubs in test_diagnostics (which
    skip themselves if "homeassistant" is already present) are unaffected.
    """

    def module(name: str, **attrs) -> ModuleType:
        mod = ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        monkeypatch.setitem(sys.modules, name, mod)
        return mod

    module("homeassistant")
    module("homeassistant.core", HomeAssistant=object, callback=lambda f: f)
    module("homeassistant.helpers")
    module("homeassistant.helpers.debounce", Debouncer=_Debouncer)
    module(
        "homeassistant.helpers.event",
        async_call_later=lambda hass, delay, action: hass.later.append((delay, action)),
    )
    module(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=_DataUpdateCoordinator,
        UpdateFailed=Exception,
    )

    pkg = module("viark_coord_pkg")
    pkg.__path__ = [str(ROOT)]

    def load(name: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location(
            f"viark_coord_pkg.{name}", ROOT / f"{name}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, mod)
        spec.loader.exec_module(mod)
        return mod

    load("const")
    load("protocol")
    return load("coordinator")


def make(coordinator_module, client):
    return coordinator_module.ViarkCoordinator(_Hass(), client)


def test_push_refreshes_use_a_short_cooldown(coordinator_module):
    client = SimpleNamespace(on_notification=None)
    coordinator = make(coordinator_module, client)

    debouncer = coordinator.kwargs.get("request_refresh_debouncer")
    assert debouncer is not None, "falling back to HA's default debouncer"
    # The receiver sends 2001 about a second apart per channel change; a cooldown
    # much longer than that is what made the entity lag the TV.
    assert debouncer.cooldown <= 2
    assert debouncer.cooldown < HA_DEFAULT_COOLDOWN
    # The first notification must still refresh at once, not after the cooldown.
    assert debouncer.immediate is True


def test_notifications_are_wired_to_the_coordinator(coordinator_module):
    client = SimpleNamespace(on_notification=None)
    coordinator = make(coordinator_module, client)
    assert client.on_notification == coordinator._handle_notification


async def test_a_quiet_fetch_reads_once(coordinator_module):
    client = FakeClient()
    coordinator = make(coordinator_module, client)
    state = await coordinator._async_update_data()
    assert client.passes == 1
    assert state.current == {"ServiceID": "A"}
    assert coordinator.hass.later == []


async def test_a_push_during_a_fetch_is_not_lost(coordinator_module):
    """HA drops refresh requests made mid-refresh, so the coordinator re-reads.

    Without the re-read the result would be the channel read before the switch,
    and it would stay that way until the next push or the 2-minute poll.
    """
    client = FakeClient(push_during_fetch=1)
    coordinator = make(coordinator_module, client)
    state = await coordinator._async_update_data()
    assert client.passes == 2
    assert state.current == {"ServiceID": "B"}
    # Settled within the pass limit, so no follow-up is needed.
    assert coordinator.hass.later == []


async def test_re_reads_are_bounded(coordinator_module):
    client = FakeClient(push_during_fetch=100)
    await make(coordinator_module, client)._async_update_data()
    assert client.passes == coordinator_module.MAX_FETCH_PASSES


async def test_hitting_the_limit_schedules_a_follow_up(coordinator_module, monkeypatch):
    """A push read on the last pass must not be dropped with it.

    A refresh requested from inside the update is discarded by HA, so the
    follow-up is deferred past the cooldown, when the lock is free.
    """
    limit = coordinator_module.MAX_FETCH_PASSES
    client = FakeClient(push_during_fetch=limit)
    coordinator = make(coordinator_module, client)
    await coordinator._async_update_data()

    assert client.passes == limit
    assert len(coordinator.hass.later) == 1
    delay, action = coordinator.hass.later[0]
    assert delay >= coordinator_module.REFRESH_COOLDOWN_SECONDS

    requested = []

    async def request_refresh():
        requested.append(True)

    monkeypatch.setattr(coordinator, "async_request_refresh", request_refresh)
    tasks = []
    monkeypatch.setattr(coordinator.hass, "async_create_task", tasks.append)
    action(None)
    await tasks[0]
    assert requested == [True]


class RefusingClient(FakeClient):
    """Request 3 answers from a script: a ProgramId, "" or a refusal."""

    def __init__(self, answers, channels) -> None:
        super().__init__()
        self.answers = list(answers)
        self.listed = channels

    async def state(self):
        self.passes += 1
        return {"ChannelNum": len(self.listed), "PowerMode": 1}

    async def channels(self, start, end):
        return self.listed

    async def playing_program_id(self, *, strict=False):
        assert strict, "the coordinator must be told about refusals"
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer or None


def refusal(coordinator_module):
    return coordinator_module.ViarkError("request 3 failed: receiver timed out")


# The cached list still flags the channel that was on when it was read.
STALE_LIST = [{"ServiceID": "A", "Playing": True}, {"ServiceID": "B"}]


async def test_a_refused_lookup_keeps_the_last_reported_channel(coordinator_module):
    """Mid-zap the receiver refuses request 3; the stale Playing flag is wrong."""
    client = RefusingClient(["B", refusal(coordinator_module)], STALE_LIST)
    coordinator = make(coordinator_module, client)

    assert (await coordinator._async_update_data()).current["ServiceID"] == "B"
    assert (await coordinator._async_update_data()).current["ServiceID"] == "B"


async def test_without_a_reported_channel_a_refusal_uses_the_flag(coordinator_module):
    """Firmware that never answers request 3 keeps the Playing-flag fallback."""
    client = RefusingClient([refusal(coordinator_module)] * 2, STALE_LIST)
    coordinator = make(coordinator_module, client)

    for _ in range(2):
        assert (await coordinator._async_update_data()).current["ServiceID"] == "A"


async def test_an_empty_answer_still_uses_the_flag(coordinator_module):
    """Only a refusal keeps the old channel; "nothing playing" is taken as said."""
    client = RefusingClient(["B", ""], STALE_LIST)
    coordinator = make(coordinator_module, client)

    await coordinator._async_update_data()
    assert (await coordinator._async_update_data()).current["ServiceID"] == "A"
