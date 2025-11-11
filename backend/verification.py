"""
Payment Verification Module

This module handles verification of x402 payment payloads without settling them on-chain.
"""

import json
import base64
from typing import Tuple, Optional
from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address

try:
    from .protocol import (
        PaymentPayload,
        PaymentRequirements,
        ExactPaymentPayload,
        PaymentScheme,
        EIP3009_TRANSFER_WITH_AUTHORIZATION_TYPEHASH,
    )
except ImportError:
    from protocol import (
        PaymentPayload,
        PaymentRequirements,
        ExactPaymentPayload,
        PaymentScheme,
        EIP3009_TRANSFER_WITH_AUTHORIZATION_TYPEHASH,
    )


class PaymentVerifier:
    """Handles verification of x402 payment payloads"""

    def __init__(self, web3: Web3):
        self.web3 = web3

    def verify_payment(
        self,
        payment_header: str,
        payment_requirements: PaymentRequirements,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a payment without settling it.

        Args:
            payment_header: Base64 encoded payment payload
            payment_requirements: Payment requirements from resource server

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Decode payment header
            payment_data = base64.b64decode(payment_header)
            payment_payload = PaymentPayload.model_validate_json(payment_data)

            # Verify protocol version
            if payment_payload.x402Version != 1:
                return False, f"Unsupported protocol version: {payment_payload.x402Version}"

            # Verify scheme matches
            if payment_payload.scheme != payment_requirements.scheme:
                return False, f"Scheme mismatch: expected {payment_requirements.scheme}, got {payment_payload.scheme}"

            # Verify network matches
            if payment_payload.network != payment_requirements.network:
                return False, f"Network mismatch: expected {payment_requirements.network}, got {payment_payload.network}"

            # Scheme-specific verification
            if payment_payload.scheme == PaymentScheme.EXACT:
                return self._verify_exact_scheme(payment_payload, payment_requirements)
            else:
                return False, f"Unsupported payment scheme: {payment_payload.scheme}"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in payment header: {str(e)}"
        except base64.binascii.Error as e:
            return False, f"Invalid base64 encoding: {str(e)}"
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def _verify_exact_scheme(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify an 'exact' scheme payment using EIP-3009.

        Args:
            payment_payload: Decoded payment payload
            payment_requirements: Payment requirements

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse the payload
            exact_payload = ExactPaymentPayload(**payment_payload.payload)

            # Verify addresses
            try:
                from_address = to_checksum_address(exact_payload.from_)
                to_address = to_checksum_address(exact_payload.to)
                required_to_address = to_checksum_address(payment_requirements.payTo)
            except ValueError as e:
                return False, f"Invalid address format: {str(e)}"

            # Verify recipient matches
            if to_address != required_to_address:
                return False, f"Recipient mismatch: expected {required_to_address}, got {to_address}"

            # Verify amount matches
            if exact_payload.value != payment_requirements.maxAmountRequired:
                return False, f"Amount mismatch: expected {payment_requirements.maxAmountRequired}, got {exact_payload.value}"

            # Verify timestamps
            current_time = self.web3.eth.get_block('latest')['timestamp']
            valid_after = int(exact_payload.validAfter)
            valid_before = int(exact_payload.validBefore)

            if current_time < valid_after:
                return False, f"Payment not yet valid: current time {current_time} < validAfter {valid_after}"

            if current_time > valid_before:
                return False, f"Payment expired: current time {current_time} > validBefore {valid_before}"

            # Verify EIP-3009 signature
            is_valid_sig, sig_error = self._verify_eip3009_signature(
                exact_payload,
                payment_requirements,
                from_address,
            )

            if not is_valid_sig:
                return False, sig_error

            return True, None

        except Exception as e:
            return False, f"Exact scheme verification error: {str(e)}"

    def _verify_eip3009_signature(
        self,
        exact_payload: ExactPaymentPayload,
        payment_requirements: PaymentRequirements,
        from_address: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify EIP-3009 transferWithAuthorization signature.

        Args:
            exact_payload: The exact payment payload
            payment_requirements: Payment requirements
            from_address: The sender's address

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get EIP-712 domain parameters from extra
            if not payment_requirements.extra:
                return False, "Missing EIP-712 domain parameters in extra"

            name = payment_requirements.extra.get("name")
            version = payment_requirements.extra.get("version")

            if not name or not version:
                return False, "Missing name or version in extra"

            # Extract chain ID from network string (e.g., "eip155:84532" -> 84532)
            try:
                chain_id = int(payment_requirements.network.split(":")[-1])
            except (ValueError, IndexError):
                return False, f"Invalid network format: {payment_requirements.network}"

            # Build EIP-712 typed data structure
            domain_data = {
                "name": name,
                "version": version,
                "chainId": chain_id,
                "verifyingContract": payment_requirements.asset,
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
                "from": exact_payload.from_,
                "to": exact_payload.to,
                "value": int(exact_payload.value),
                "validAfter": int(exact_payload.validAfter),
                "validBefore": int(exact_payload.validBefore),
                "nonce": exact_payload.nonce,
            }

            # Encode using eth-account 0.13.0+ API
            # Use full_message format as that's what the API supports
            typed_data = {
                "types": message_types,
                "primaryType": "TransferWithAuthorization",
                "domain": domain_data,
                "message": message_data,
            }
            
            from eth_account.messages import encode_typed_data
            encoded_data = encode_typed_data(full_message=typed_data)
            
            # Reconstruct signature from v, r, s components
            # EIP-712 signatures use v = 27 or 28
            v = exact_payload.v
            r = int(exact_payload.r, 16)
            s = int(exact_payload.s, 16)
            
            # Create signature bytes (r + s + v format, 65 bytes total)
            # r and s are 32 bytes each, v is 1 byte
            signature_bytes = r.to_bytes(32, 'big') + s.to_bytes(32, 'big') + bytes([v])

            # Recover address from signature
            recovered_address = Account.recover_message(
                encoded_data,
                signature=signature_bytes
            )

            # Verify recovered address matches from address
            if recovered_address.lower() != from_address.lower():
                return False, f"Signature verification failed: recovered {recovered_address}, expected {from_address}"

            return True, None

        except Exception as e:
            return False, f"Signature verification error: {str(e)}"


def create_payment_verifier(rpc_url: str) -> PaymentVerifier:
    """
    Factory function to create a PaymentVerifier instance.

    Args:
        rpc_url: RPC URL for blockchain connection

    Returns:
        PaymentVerifier instance
    """
    # Create Web3 instance with timeout settings
    from web3.providers import HTTPProvider
    
    provider = HTTPProvider(
        rpc_url,
        request_kwargs={'timeout': 30}
    )
    web3 = Web3(provider)
    
    # Try to connect with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if web3.is_connected():
                # Test the connection by getting chain ID
                chain_id = web3.eth.chain_id
                print(f"✅ Connected to blockchain (Chain ID: {chain_id})")
                return PaymentVerifier(web3)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Connection attempt {attempt + 1} failed, retrying...")
                import time
                time.sleep(2)
            else:
                raise ConnectionError(f"Failed to connect to blockchain at {rpc_url} after {max_retries} attempts: {str(e)}")
    
    raise ConnectionError(f"Failed to connect to blockchain at {rpc_url}")
