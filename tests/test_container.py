import os
import pytest

from web3 import Web3
from anvil_testcontainer.container import AnvilContainer, ContainerConfig


@pytest.fixture
def fork_url():
    return f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['ALCHEMY_API_KEY']}"


@pytest.fixture
def container_config(fork_url):
    return ContainerConfig(fork_url=fork_url, port=8545, timeout=30)


def test_container_lifecycle(container_config):
    container = AnvilContainer(container_config)

    # Test startup
    container.start()
    assert container.verify_health() == True

    # Test Web3 connection
    web3 = container.get_web3()
    assert isinstance(web3, Web3)
    assert web3.is_connected()

    # Test block number is accessible
    block_number = web3.eth.block_number
    assert block_number > 0

    # Test cleanup
    container.stop()
    with pytest.raises(Exception):
        # After stopping, Web3 connections should fail
        web3.eth.block_number


def test_container_context_manager(container_config):
    with AnvilContainer(container_config) as container:
        web3 = container.get_web3()
        assert web3.is_connected()
        assert web3.eth.block_number > 0

    # Context manager should have cleaned up
    assert not hasattr(container, "_web3") or container._web3 is None
