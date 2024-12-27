import os
import pytest
from anvil_testcontainer.container import ContainerConfig

@pytest.fixture
def fork_url():
    return f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['ALCHEMY_API_KEY']}"

@pytest.fixture
def container_config(fork_url):
    return ContainerConfig(fork_url=fork_url, port=8545, timeout=30)
