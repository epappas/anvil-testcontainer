"""
Anvil Test Container Library

This library provides a secure and efficient way to manage Anvil Ethereum test containers
for blockchain development and testing. It offers features like:

- Secure container management
- Chain state manipulation (time control, forking)
- Transaction handling
- Snapshot management
- Health monitoring

Basic usage:
    ```python
    from anvil_container import AnvilContainer

    with AnvilContainer("https://eth-mainnet.example.com") as anvil:
        web3 = anvil.get_web3()
        current_block = web3.eth.block_number
        print(f"Connected to block {current_block}")
    ```

Advanced usage:
    ```python
    from anvil_container import AnvilContainer, ContainerConfig

    config = ContainerConfig(
        fork_url="https://eth-mainnet.example.com",
        fork_block_number=14000000,
        timeout=30,
        env_vars={"ETHERSCAN_API_KEY": "your-key"}
    )

    with AnvilContainer(config) as anvil:
        # Create a snapshot
        snapshot_id = anvil.create_snapshot()

        # Execute a transaction
        tx_hash = anvil.send_transaction(
            from_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            to_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            value=100000000000000000  # 0.1 ETH
        )

        # Revert if needed
        anvil.revert_snapshot(snapshot_id)
    ```
"""

# Version information
__version__ = "0.1.6"
__author__ = "Evangelos Pappas <epappas@evalonlabs.com>"
__license__ = "MIT"

from .container import AnvilContainer, ContainerConfig, ContainerState

from .validation import (
    ValidationError,
    validate_ethereum_address,
    validate_hex_data,
)

__all__ = [
    # Main classes
    "AnvilContainer",
    "ContainerConfig",
    "ContainerState",
    # Exceptions
    "ValidationError",
    # Validation utilities
    "validate_ethereum_address",
    "validate_hex_data",
    # Version info
    "__version__",
    "__author__",
    "__license__",
]

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
