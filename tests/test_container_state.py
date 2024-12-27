import pytest
import time
from anvil_testcontainer.container import (
    AnvilContainer,
    ContainerState,
    ContainerConfig,
)


@pytest.fixture
def container(
    container_config: ContainerConfig,
):
    container = AnvilContainer(container_config)
    yield container
    if container.get_state() != ContainerState.STOPPED:
        container.stop()


def test_initial_state(container: AnvilContainer):
    assert container.get_state() == ContainerState.STOPPED


def test_start_state_transition(container: AnvilContainer):
    assert container.get_state() == ContainerState.STOPPED

    container.start()
    assert container.get_state() == ContainerState.RUNNING

    container.stop()
    assert container.get_state() == ContainerState.STOPPED


def test_error_state_transition(container: AnvilContainer):
    # Force error by stopping container that's already stopped
    assert container.get_state() == ContainerState.STOPPED

    with pytest.raises(RuntimeError, match="Cannot stop a container that is already stopped"):
        container.stop()
    assert container.get_state() == ContainerState.ERROR


def test_state_in_context_manager(container_config: ContainerConfig):
    with AnvilContainer(container_config) as container:
        assert container.get_state() == ContainerState.RUNNING

    assert container.get_state() == ContainerState.STOPPED


def test_failed_start_state(container: AnvilContainer, monkeypatch: pytest.MonkeyPatch):
    def mock_verify_health(*args):
        time.sleep(0.1)
        return False

    monkeypatch.setattr(container, "verify_health", mock_verify_health)

    with pytest.raises(TimeoutError):
        container.start()

    assert container.get_state() == ContainerState.ERROR
