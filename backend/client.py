"""
x402 Payment Client

Utilities for creating and sending x402 payment requests.
"""

import os
import json
import base64
import time
import secrets
from typing import Optional, Dict, Any, Tuple
from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address
import requests

try:
    from .protocol import (
        PaymentRequirements,
        PaymentRequiredResponse,
        PaymentPayload,
        ExactPaymentPayload,
        X_PAYMENT_HEADER,
        X_PAYMENT_RESPONSE_HEADER,
    )
except ImportError:
    from protocol import (
        PaymentRequirements,
        PaymentRequiredResponse,
        PaymentPayload,
        ExactPaymentPayload,
        X_PAYMENT_HEADER,
        X_PAYMENT_RESPONSE_HEADER,
    )


class X402Client:
    """Client for making x402 payments"""

    def __init__(
        self,
        private_key: str,
        rpc_url: Optional[str] = None,
    ):
        """
        Initialize x402 client.

        Args:
            private_key: Private key for signing payments
            rpc_url: RPC URL for blockchain connection (optional, for timestamp checks)
        """
        self.account = Account.from_key(private_key)
        self.web3 = Web3(Web3.HTTPProvider(rpc_url)) if rpc_url else None

    def request_resource(
        self,
        url: str,
        auto_pay: bool = True,
        method: str = "GET",
        **kwargs,
    ) -> requests.Response:
        """
        Request a resource, automatically handling payment if required.

        Args:
            url: URL of the resource
            auto_pay: Whether to automatically pay if 402 is returned
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests

        Returns:
            Response from the server
        """
        # Make initial request
        response = requests.request(method, url, **kwargs)

        # Check if payment is required
        if response.status_code == 402 and auto_pay:
            try:
                # Parse payment requirements
                payment_required = PaymentRequiredResponse.model_validate_json(response.text)

                if not payment_required.accepts:
                    raise ValueError("No payment methods accepted")

                # Use first accepted payment requirement
                payment_req = payment_required.accepts[0]

                # Create payment
                payment_header = self.create_payment(payment_req)

                # Retry request with payment
                headers = kwargs.get("headers", {})
                headers[X_PAYMENT_HEADER] = payment_header
                kwargs["headers"] = headers

                response = requests.request(method, url, **kwargs)

            except Exception as e:
                raise Exception(f"Payment failed: {str(e)}")

        return response

    def create_payment(
        self,
        payment_requirements: PaymentRequirements,
        valid_duration: int = 300,  # 5 minutes
    ) -> str:
        """
        Create a payment for given requirements.

        Args:
            payment_requirements: Payment requirements from server
            valid_duration: How long the payment is valid (seconds)

        Returns:
            Base64 encoded payment header
        """
        if payment_requirements.scheme == "exact":
            return self._create_exact_payment(payment_requirements, valid_duration)
        else:
            raise ValueError(f"Unsupported payment scheme: {payment_requirements.scheme}")

    def _create_exact_payment(
        self,
        payment_requirements: PaymentRequirements,
        valid_duration: int,
    ) -> str:
        """
        Create an 'exact' scheme payment using EIP-3009.

        Args:
            payment_requirements: Payment requirements
            valid_duration: Validity duration in seconds

        Returns:
            Base64 encoded payment header
        """
        # Get current timestamp
        if self.web3 and self.web3.is_connected():
            current_time = self.web3.eth.get_block('latest')['timestamp']
        else:
            current_time = int(time.time())

        # Generate nonce (32 bytes)
        nonce = "0x" + secrets.token_hex(32)

        # Set validity window with buffer for clock skew
        # Subtract 10 seconds from validAfter to account for timing differences
        valid_after = current_time - 10
        valid_before = current_time + valid_duration

        # Get EIP-712 domain parameters
        if not payment_requirements.extra:
            raise ValueError("Missing EIP-712 domain parameters in extra")

        name = payment_requirements.extra.get("name")
        version = payment_requirements.extra.get("version")

        if not name or not version:
            raise ValueError("Missing name or version in extra")

        # Extract chain ID from network
        try:
            chain_id = int(payment_requirements.network.split(":")[-1])
        except (ValueError, IndexError):
            raise ValueError(f"Invalid network format: {payment_requirements.network}")

        # Build EIP-712 typed data structure
        # Ensure all addresses are checksummed
        from_address = to_checksum_address(self.account.address)
        to_address = to_checksum_address(payment_requirements.payTo)
        verifying_contract = to_checksum_address(payment_requirements.asset)
        
        domain_data = {
            "name": name,
            "version": version,
            "chainId": chain_id,
            "verifyingContract": verifying_contract,
        }
        
        message_types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        }
        
        message_data = {
            "from": from_address,
            "to": to_address,
            "value": int(payment_requirements.maxAmountRequired),
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": nonce,
        }

        # Sign the message using eth-account 0.13.0+ API
        # The new API doesn't use primaryType separately, so we use full_message format
        typed_data = {
            "types": message_types,
            "primaryType": "TransferWithAuthorization",
            "domain": domain_data,
            "message": message_data,
        }
        
        from eth_account.messages import encode_typed_data
        encoded_data = encode_typed_data(full_message=typed_data)
        signed_message = self.account.sign_message(encoded_data)

        # Create exact payment payload with checksummed addresses
        # Note: r and s need 0x prefix for proper hex string format
        exact_payload = ExactPaymentPayload(
            **{
                "from": from_address,
                "to": to_address,
                "value": payment_requirements.maxAmountRequired,
                "validAfter": str(valid_after),
                "validBefore": str(valid_before),
                "nonce": nonce,
                "v": signed_message.v,
                "r": "0x" + signed_message.r.to_bytes(32, 'big').hex(),
                "s": "0x" + signed_message.s.to_bytes(32, 'big').hex(),
            }
        )

        # Create payment payload
        payment_payload = PaymentPayload(
            x402Version=1,
            scheme=payment_requirements.scheme,
            network=payment_requirements.network,
            payload=exact_payload.model_dump(by_alias=True),
        )

        # Encode as base64
        payment_json = payment_payload.model_dump_json()
        payment_b64 = base64.b64encode(payment_json.encode()).decode()

        return payment_b64

    def decode_payment_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """
        Decode the X-PAYMENT-RESPONSE header from a response.

        Args:
            response: HTTP response

        Returns:
            Decoded payment response or None
        """
        payment_response_header = response.headers.get(X_PAYMENT_RESPONSE_HEADER)
        
        if not payment_response_header:
            return None

        try:
            decoded = base64.b64decode(payment_response_header)
            return json.loads(decoded)
        except Exception:
            return None


def create_client(private_key: Optional[str] = None, rpc_url: Optional[str] = None) -> X402Client:
    """
    Factory function to create an X402Client.

    Args:
        private_key: Private key (if None, loads from env)
        rpc_url: RPC URL (if None, loads from env)

    Returns:
        X402Client instance
    """
    if not private_key:
        private_key = os.getenv("CLIENT_PRIVATE_KEY")
        if not private_key:
            raise ValueError("CLIENT_PRIVATE_KEY not set")

    if not rpc_url:
        rpc_url = os.getenv("RPC_URL")

    return X402Client(private_key, rpc_url)
