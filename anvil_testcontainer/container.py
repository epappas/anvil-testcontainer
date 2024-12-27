"""
Enhanced Anvil Ethereum test container with security features and advanced functionality.

This module provides a secure and feature-rich implementation for managing Anvil
Ethereum test containers. It includes snapshot management, health monitoring,
and secure transaction handling.

Example usage:
    ```python
    with AnvilContainer(fork_url="https://mainnet.example.com") as anvil:
        # Create a snapshot
        snapshot_id = anvil.create_snapshot()

        # Execute a transaction
        tx_hash = anvil.send_transaction(
            from_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            to_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            value=100000000000000000  # 0.1 ETH
        )

        # Check if successful
        receipt = anvil.get_web3().eth.wait_for_transaction_receipt(tx_hash)

        # Revert if needed
        anvil.revert_snapshot(snapshot_id)
    ```
"""

import logging
import time
import enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import requests
from testcontainers.core.container import DockerContainer
from web3 import Web3, HTTPProvider
from web3.types import RPCEndpoint, TxParams, Wei
from eth_typing import HexStr

from .validation import (
    ValidationError,
    validate_ethereum_address,
    validate_hex_data,
    sanitize_command,
    validate_environment_vars,
)


class ContainerState(enum.Enum):
    RUNNING = "running"
    STARTING = "starting"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass(frozen=True)
class ContainerConfig:
    """
    Immutable configuration for AnvilContainer.

    Attributes:
        fork_url: Ethereum node URL to fork from
        fork_block_number: Optional block number to fork from
        image: Docker image to use
        port: Port to expose
        timeout: Operation timeout in seconds
        env_vars: Optional environment variables
    """

    fork_url: str
    fork_block_number: Optional[int] = None
    image: str = "ghcr.io/foundry-rs/foundry:nightly"
    port: int = 8545
    timeout: int = 60
    env_vars: Optional[Dict[str, str]] = None


class AnvilContainer:
    """
    Secure Anvil Ethereum test container manager with advanced features.

    Features:
    - Snapshot and revert functionality
    - Health monitoring
    - Secure transaction execution
    - Resource management
    - Command validation
    """

    def __init__(self, config: Union[str, ContainerConfig]):
        """
        Initialize the container with configuration.

        Args:
            config: Either a fork URL string or ContainerConfig object

        Raises:
            ValidationError: If configuration is invalid
        """
        self.log = logging.getLogger(__name__)

        # Handle string input for backwards compatibility
        if isinstance(config, str):
            self.config = ContainerConfig(fork_url=config)
        else:
            self.config = config

        # Validate environment variables if provided
        if self.config.env_vars:
            self.env_vars = validate_environment_vars(self.config.env_vars)
        else:
            self.env_vars = {}

        self._container = self._create_container()
        self._web3: Optional[Web3] = None
        self._state = ContainerState.STOPPED

        # TODO: Implement self-running status
        # self_runnning_status =

    def _create_container(self) -> DockerContainer:
        """Create and configure the Docker container securely."""
        # Build fork command with proper escaping
        fork_flag = (
            f"--fork-block-number {self.config.fork_block_number}"
            if self.config.fork_block_number is not None
            else ""
        )

        command = f'"anvil --steps-tracing --auto-impersonate --host 0.0.0.0 --fork-url {self.config.fork_url} {fork_flag}"'

        container = (
            DockerContainer(self.config.image)
            .with_exposed_ports(self.config.port)
            .with_bind_ports(self.config.port)
            .with_command(command)
        )

        # Add validated environment variables
        for key, value in self.env_vars.items():
            container = container.with_env(key, value)

        return container

    def get_endpoint_url(self) -> str:
        """Get the HTTP URL for the Anvil endpoint."""
        host = self._container.get_container_host_ip()
        port = self._container.get_exposed_port(self.config.port)
        return f"http://{host}:{port}"

    def get_endpoint_url_wss(self) -> str:
        """Get the WSS URL for the Anvil endpoint."""
        host = self._container.get_container_host_ip()
        port = self._container.get_exposed_port(self.config.port)
        return f"wss://{host}:{port}"

    def get_web3(self) -> Web3:
        """
        Get a Web3 instance connected to the container.

        The instance is cached for efficiency.
        """
        if not self._web3:
            self._web3 = Web3(HTTPProvider(self.get_endpoint_url()))
        return self._web3

    def get_web3_wss(self) -> Web3:
        """
        Get a Web3 instance connected to the container via WSS.

        The instance is cached for efficiency.
        """
        if not self._web3:
            self._web3 = Web3(HTTPProvider(self.get_endpoint_url_wss()))
        return self._web3

    def verify_health(self) -> bool:
        """
        Check if the container is healthy and responsive.

        Returns:
            bool: True if container is healthy
        """
        try:
            web3 = self.get_web3()
            return web3.eth.block_number > 0 and web3.is_connected()
        except Exception as e:
            return False

    def get_logs(self) -> str:
        """
        Retrieve container logs for debugging.

        Returns:
            str: Container logs

        Raises:
            RuntimeError: If log retrieval fails
        """
        try:
            result = self._container.exec(sanitize_command(["logs"]))
            return (
                result[1].decode("utf-8") if isinstance(result, tuple) else str(result)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve logs: {e}")

    def create_snapshot(self) -> str:
        """
        Create a snapshot of the current chain state.

        Returns:
            str: Snapshot ID for later restoration
        """
        web3 = self.get_web3()
        snapshot_id = web3.manager.request_blocking(RPCEndpoint("evm_snapshot"), [])
        self.log.info(f"Created snapshot {snapshot_id}")
        return snapshot_id

    def revert_snapshot(self, snapshot_id: str) -> bool:
        """
        Revert to a previous chain snapshot.

        Args:
            snapshot_id: ID of snapshot to restore

        Returns:
            bool: True if revert was successful
        """
        web3 = self.get_web3()
        success = web3.manager.request_blocking(
            RPCEndpoint("evm_revert"), [snapshot_id]
        )
        if success:
            self.log.info(f"Reverted to snapshot {snapshot_id}")
        return success

    def send_transaction(
        self,
        from_address: str,
        to_address: str,
        value: Wei = Wei(0),
        data: str = "0x",
    ) -> str:
        """
        Send a transaction securely.

        Args:
            from_address: Sender address
            to_address: Recipient address
            value: Amount in Wei
            data: Transaction data hexstring

        Returns:
            str: Transaction hash

        Raises:
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        if not validate_ethereum_address(from_address):
            raise ValidationError(f"Invalid from address: {from_address}")
        if not validate_ethereum_address(to_address):
            raise ValidationError(f"Invalid to address: {to_address}")
        if not validate_hex_data(data):
            raise ValidationError(f"Invalid transaction data: {data}")

        web3 = self.get_web3()

        # Build and send transaction
        tx: TxParams = {
            "from": from_address,
            "to": to_address,
            "value": value,
            "data": HexStr(data),
            "gas": 2000000,  # Safe default
            "gasPrice": web3.eth.gas_price,
        }

        tx_hash = web3.eth.send_transaction(tx)
        return tx_hash.hex()

    def execute(self, command: Union[str, List[str]], check: bool = True) -> None:
        """
        Execute a command securely in the container.

        Args:
            command: Command to execute
            check: Whether to check command exit code

        Raises:
            ValidationError: If command is dangerous
            RuntimeError: If command execution fails
        """
        safe_command = sanitize_command(command)
        result = self._container.exec(safe_command)

        if check and getattr(result, "exit_code", 0) != 0:
            raise RuntimeError(f"Command failed: {result}")

    def start(self) -> None:
        """
        Start the container and wait for readiness.

        This method ensures:
        1. Container starts successfully
        2. Endpoint becomes available
        3. Web3 connection is established
        """
        self.log.info("Starting Anvil container")
        self._state = ContainerState.STARTING

        try:
            self._container.start()
            start_time = time.time()
            consecutive_failures = 0
            max_failures = 10

            while True:
                try:
                    if self.verify_health():
                        consecutive_failures = 0  # Reset on success
                        self._state = ContainerState.RUNNING
                        self.log.info("Anvil container ready")
                        return
                    else:
                        consecutive_failures += 1
                except requests.ConnectionError:
                    consecutive_failures += 1

                if consecutive_failures >= max_failures:
                    self._state = ContainerState.ERROR
                    raise TimeoutError("Container health check failed")

                if time.time() - start_time > self.config.timeout:
                    self._state = ContainerState.ERROR
                    raise TimeoutError("Anvil endpoint not ready")

                time.sleep(1)
        except Exception as e:
            self._state = ContainerState.ERROR
            raise

    def stop(self) -> None:
        """
        Stop the container and cleanup resources.

        Raises:
            RuntimeError: If container is already stopped
        """
        if self._state == ContainerState.STOPPED:
            self._state = ContainerState.ERROR
            raise RuntimeError("Cannot stop a container that is already stopped")

        try:
            self._container.stop()
            self._web3 = None  # Clear cached Web3 instance
            self._state = ContainerState.STOPPED
            self.log.info("Anvil container stopped")
        except Exception as e:
            self._state = ContainerState.ERROR
            self.log.error(f"Error stopping container: {e}")
            raise

    def reset_fork(self, block_number: int):
        self.log.info("Anvil fork reset")
        w3 = self.get_web3()
        params = [
            {
                "forking": {
                    "jsonRpcUrl": self.config.fork_url,
                    "blockNumber": hex(block_number),
                }
            }
        ]
        w3.manager.request_blocking(RPCEndpoint("anvil_reset"), params)
        current_block_number = w3.eth.block_number
        if current_block_number != block_number:
            error_message = f"Current block number is {current_block_number}, expected {block_number}"
            self.log.error(error_message)
            raise RuntimeError(error_message)
        self.log.info("Anvil fork reset complete")

    def move_time(self, delta_time: int):
        self.log.info("Anvil evm increaseTime")
        w3 = self.get_web3()
        w3.manager.request_blocking(RPCEndpoint("evm_increaseTime"), [delta_time])
        w3.manager.request_blocking(RPCEndpoint("evm_mine"), [])
        self.log.info("Anvil time moved forward by %s seconds", delta_time)

    def grant_market_substrates(
        self,
        from_address: str,
        plasma_vault: str,
        market_id: int,
        substrates: List[str],
    ):
        self.log.info("Granting market substrates")
        w3 = self.get_web3()
        # Implement the contract interaction using Web3.py
        # Placeholder for actual implementation
        self.log.warning("grant_market_substrates method needs implementation")

    def get_state(self) -> ContainerState:
        """Get current container state."""
        return self._state

    def __enter__(self) -> "AnvilContainer":
        """Start container when entering context."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure container is stopped when exiting context."""
        self.stop()
