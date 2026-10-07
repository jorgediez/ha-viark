"""Refresh pacing of the coordinator.

Drives the coordinator's update directly, against a scripted client, so the
debouncer settings and the re-read logic can be checked without the timing of a
real refresh.
"""

from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.viark.const import REFRESH_COOLDOWN_SECONDS
from custom_components.viark.coordinator import MAX_FETCH_PASSES, ViarkCoordinator
from custom_components.viark.protocol import ViarkError
from homeassistant.core import HomeAssistant

#: Home Assistant's own default, which left channel changes up to 10 s behind.
HA_DEFAULT_COOLDOWN = 10


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
def call_later() -> Generator[MagicMock]:
    """Capture follow-up refreshes the coordinator schedules."""
    with patch("custom_components.viark.coordinator.async_call_later") as call_later:
        yield call_later


def make(hass: HomeAssistant, client) -> ViarkCoordinator:
    """Build a coordinator whose refresh requests are recorded, not run.

    The tests call _async_update_data themselves; a refresh started by a push
    in the middle of one would run a second update alongside it.
    """
    coordinator = ViarkCoordinator(hass, client)
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


async def test_push_refreshes_use_a_short_cooldown(hass: HomeAssistant) -> None:
    coordinator = ViarkCoordinator(hass, SimpleNamespace(on_notification=None))

    debouncer = coordinator._debounced_refresh
    # The receiver sends 2001 about a second apart per channel change; a cooldown
    # much longer than that is what made the entity lag the TV.
    assert debouncer.cooldown <= 2
    assert debouncer.cooldown < HA_DEFAULT_COOLDOWN
    # The first notification must still refresh at once, not after the cooldown.
    assert debouncer.immediate is True


async def test_notifications_are_wired_to_the_coordinator(
    hass: HomeAssistant,
) -> None:
    client = SimpleNamespace(on_notification=None)
    coordinator = ViarkCoordinator(hass, client)
    assert client.on_notification == coordinator._handle_notification


async def test_a_quiet_fetch_reads_once(
    hass: HomeAssistant, call_later: MagicMock
) -> None:
    client = FakeClient()
    coordinator = make(hass, client)
    state = await coordinator._async_update_data()
    assert client.passes == 1
    assert state.current == {"ServiceID": "A"}
    call_later.assert_not_called()


async def test_a_push_during_a_fetch_is_not_lost(
    hass: HomeAssistant, call_later: MagicMock
) -> None:
    """HA drops refresh requests made mid-refresh, so the coordinator re-reads.

    Without the re-read the result would be the channel read before the switch,
    and it would stay that way until the next push or the 2-minute poll.
    """
    client = FakeClient(push_during_fetch=1)
    coordinator = make(hass, client)
    state = await coordinator._async_update_data()
    assert client.passes == 2
    assert state.current == {"ServiceID": "B"}
    # Settled within the pass limit, so no follow-up is needed.
    call_later.assert_not_called()


@pytest.mark.usefixtures("call_later")
async def test_re_reads_are_bounded(hass: HomeAssistant) -> None:
    client = FakeClient(push_during_fetch=100)
    await make(hass, client)._async_update_data()
    assert client.passes == MAX_FETCH_PASSES


async def test_hitting_the_limit_schedules_a_follow_up(
    hass: HomeAssistant, call_later: MagicMock
) -> None:
    """A push read on the last pass must not be dropped with it.

    A refresh requested from inside the update is discarded by HA, so the
    follow-up is deferred past the cooldown, when the lock is free.
    """
    client = FakeClient(push_during_fetch=MAX_FETCH_PASSES)
    coordinator = make(hass, client)
    await coordinator._async_update_data()

    assert client.passes == MAX_FETCH_PASSES
    call_later.assert_called_once()
    _, delay, action = call_later.call_args.args
    assert delay >= REFRESH_COOLDOWN_SECONDS

    requested = coordinator.async_request_refresh.await_count
    action(None)
    await hass.async_block_till_done()
    assert coordinator.async_request_refresh.await_count == requested + 1


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


def refusal() -> ViarkError:
    return ViarkError("request 3 failed: receiver timed out")


# The cached list still flags the channel that was on when it was read.
STALE_LIST = [{"ServiceID": "A", "Playing": True}, {"ServiceID": "B"}]


async def test_a_refused_lookup_keeps_the_last_reported_channel(
    hass: HomeAssistant,
) -> None:
    """Mid-zap the receiver refuses request 3; the stale Playing flag is wrong."""
    client = RefusingClient(["B", refusal()], STALE_LIST)
    coordinator = make(hass, client)

    assert (await coordinator._async_update_data()).current["ServiceID"] == "B"
    assert (await coordinator._async_update_data()).current["ServiceID"] == "B"


async def test_without_a_reported_channel_a_refusal_uses_the_flag(
    hass: HomeAssistant,
) -> None:
    """Firmware that never answers request 3 keeps the Playing-flag fallback."""
    client = RefusingClient([refusal()] * 2, STALE_LIST)
    coordinator = make(hass, client)

    for _ in range(2):
        assert (await coordinator._async_update_data()).current["ServiceID"] == "A"


async def test_an_empty_answer_still_uses_the_flag(hass: HomeAssistant) -> None:
    """Only a refusal keeps the old channel; "nothing playing" is taken as said."""
    client = RefusingClient(["B", ""], STALE_LIST)
    coordinator = make(hass, client)

    await coordinator._async_update_data()
    assert (await coordinator._async_update_data()).current["ServiceID"] == "A"
