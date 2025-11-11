"""
Payment Settlement Module

This module handles settlement of verified payments on the blockchain.
"""

import time
from typing import Optional, Tuple
from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address

try:
    from .protocol import (
        PaymentPayload,
        PaymentRequirements,
        ExactPaymentPayload,
        PaymentScheme,
    )
except ImportError:
    from protocol import (
        PaymentPayload,
        PaymentRequirements,
        ExactPaymentPayload,
        PaymentScheme,
    )


# EIP-3009 ABI for transferWithAuthorization
EIP3009_ABI = [
    {
        "inputs": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
            {"name": "v", "type": "uint8"},
            {"name": "r", "type": "bytes32"},
            {"name": "s", "type": "bytes32"},
        ],
        "name": "transferWithAuthorization",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "authorizer", "type": "address"}, {"name": "nonce", "type": "bytes32"}],
        "name": "authorizationState",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class PaymentSettler:
    """Handles settlement of x402 payments on the blockchain"""

    def __init__(
        self,
        web3: Web3,
        private_key: str,
        max_gas_price_gwei: Optional[float] = None,
    ):
        """
        Initialize the payment settler.

        Args:
            web3: Web3 instance
            private_key: Private key for submitting transactions
            max_gas_price_gwei: Maximum gas price in Gwei (optional)
        """
        self.web3 = web3
        self.account = Account.from_key(private_key)
        self.max_gas_price_gwei = max_gas_price_gwei

    def settle_payment(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
        wait_for_confirmation: bool = True,
        timeout: int = 120,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Settle a payment on the blockchain.

        Args:
            payment_payload: Decoded payment payload
            payment_requirements: Payment requirements
            wait_for_confirmation: Whether to wait for transaction confirmation
            timeout: Timeout in seconds for confirmation

        Returns:
            Tuple of (success, error_message, tx_hash)
        """
        try:
            # Scheme-specific settlement
            if payment_payload.scheme == PaymentScheme.EXACT:
                return self._settle_exact_scheme(
                    payment_payload,
                    payment_requirements,
                    wait_for_confirmation,
                    timeout,
                )
            else:
                return False, f"Unsupported payment scheme: {payment_payload.scheme}", None

        except Exception as e:
            return False, f"Settlement error: {str(e)}", None

    def _settle_exact_scheme(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
        wait_for_confirmation: bool,
        timeout: int,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Settle an 'exact' scheme payment using EIP-3009.

        Args:
            payment_payload: Decoded payment payload
            payment_requirements: Payment requirements
            wait_for_confirmation: Whether to wait for confirmation
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, error_message, tx_hash)
        """
        try:
            # Parse payload
            exact_payload = ExactPaymentPayload(**payment_payload.payload)

            # Get token contract
            token_address = to_checksum_address(payment_requirements.asset)
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=EIP3009_ABI,
            )

            # Check if authorization has already been used
            nonce_bytes = self.web3.to_bytes(hexstr=exact_payload.nonce)
            from_address = to_checksum_address(exact_payload.from_)
            
            try:
                is_used = token_contract.functions.authorizationState(
                    from_address,
                    nonce_bytes,
                ).call()

                if is_used:
                    return False, "Authorization nonce already used", None
            except Exception as e:
                # Some tokens may not support authorizationState, continue anyway
                pass

            # Build transaction
            tx = token_contract.functions.transferWithAuthorization(
                to_checksum_address(exact_payload.from_),
                to_checksum_address(exact_payload.to),
                int(exact_payload.value),
                int(exact_payload.validAfter),
                int(exact_payload.validBefore),
                nonce_bytes,
                exact_payload.v,
                self.web3.to_bytes(hexstr=exact_payload.r),
                self.web3.to_bytes(hexstr=exact_payload.s),
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': 200000,  # Estimate, will be adjusted
            })

            # Estimate gas
            try:
                estimated_gas = self.web3.eth.estimate_gas(tx)
                tx['gas'] = int(estimated_gas * 1.2)  # Add 20% buffer
            except Exception as e:
                return False, f"Gas estimation failed: {str(e)}", None

            # Check gas price
            if self.max_gas_price_gwei:
                current_gas_price = self.web3.eth.gas_price
                max_gas_price = self.web3.to_wei(self.max_gas_price_gwei, 'gwei')
                if current_gas_price > max_gas_price:
                    return False, f"Gas price too high: {self.web3.from_wei(current_gas_price, 'gwei')} Gwei", None

            # Sign and send transaction
            signed_tx = self.account.sign_transaction(tx)
            
            # Handle both old and new web3.py versions
            # New versions use raw_transaction, old versions use rawTransaction
            raw_tx = getattr(signed_tx, 'raw_transaction', None) or getattr(signed_tx, 'rawTransaction', None)
            if raw_tx is None:
                return False, "Failed to get raw transaction from signed transaction", None
                
            tx_hash = self.web3.eth.send_raw_transaction(raw_tx)
            tx_hash_hex = tx_hash.hex()

            # Wait for confirmation if requested
            if wait_for_confirmation:
                try:
                    receipt = self.web3.eth.wait_for_transaction_receipt(
                        tx_hash,
                        timeout=timeout,
                    )

                    if receipt['status'] == 1:
                        return True, None, tx_hash_hex
                    else:
                        return False, "Transaction reverted", tx_hash_hex

                except Exception as e:
                    return False, f"Transaction confirmation timeout: {str(e)}", tx_hash_hex
            else:
                # Return immediately without waiting
                return True, None, tx_hash_hex

        except Exception as e:
            return False, f"Exact scheme settlement error: {str(e)}", None

    def get_transaction_status(self, tx_hash: str) -> dict:
        """
        Get the status of a transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dictionary with transaction status information
        """
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            
            return {
                "confirmed": True,
                "status": "success" if receipt['status'] == 1 else "failed",
                "blockNumber": receipt['blockNumber'],
                "gasUsed": receipt['gasUsed'],
            }
        except Exception as e:
            # Transaction not yet mined
            return {
                "confirmed": False,
                "status": "pending",
                "error": str(e),
            }


def create_payment_settler(
    rpc_url: str,
    private_key: str,
    max_gas_price_gwei: Optional[float] = None,
) -> PaymentSettler:
    """
    Factory function to create a PaymentSettler instance.

    Args:
        rpc_url: RPC URL for blockchain connection
        private_key: Private key for submitting transactions
        max_gas_price_gwei: Maximum gas price in Gwei (optional)

    Returns:
        PaymentSettler instance
    """
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to blockchain at {rpc_url}")
    
    return PaymentSettler(web3, private_key, max_gas_price_gwei)
