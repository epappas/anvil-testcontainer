import os

from anvil_testcontainer import AnvilContainer
from web3.types import BlockData


def test_time_manipulation():
    FORK_URL = os.getenv(
        "ETH_RPC_URL", "https://eth-mainnet.alchemyapi.io/v2/your-api-key"
    )

    with AnvilContainer(FORK_URL) as anvil:
        w3 = anvil.get_web3()

        # Get initial timestamp
        initial_block: BlockData = w3.eth.get_block("latest")
        initial_time = initial_block.get("timestamp", 0)
        print(f"Initial block timestamp: {initial_time}")

        # Move time forward by 1 day
        ONE_DAY = 24 * 60 * 60
        anvil.move_time(ONE_DAY)

        # Get new timestamp
        new_block = w3.eth.get_block("latest")
        new_time = new_block.get("timestamp", 0)
        print(f"New block timestamp: {new_time}")

        # Verify time difference
        assert new_time >= initial_time + ONE_DAY, "Time manipulation failed"
        print(f"Successfully moved time forward by {ONE_DAY} seconds")


if __name__ == "__main__":
    test_time_manipulation()
