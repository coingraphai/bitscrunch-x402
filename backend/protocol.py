"""
x402 Protocol Core Types and Data Structures

This module defines the core data structures for the x402 payment protocol
according to the v1 specification.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PaymentScheme(str, Enum):
    """Supported payment schemes"""
    EXACT = "exact"
    # Future schemes can be added here (e.g., UPTO = "upto")


class PaymentRequirements(BaseModel):
    """
    Payment requirements that define how a client should pay for a resource.
    """
    scheme: str = Field(..., description="Scheme of the payment protocol to use")
    network: str = Field(..., description="Network of the blockchain to send payment on")
    maxAmountRequired: str = Field(..., description="Maximum amount required in atomic units")
    resource: str = Field(..., description="URL of resource to pay for")
    description: str = Field(..., description="Description of the resource")
    mimeType: str = Field(..., description="MIME type of the resource response")
    outputSchema: Optional[Dict[str, Any]] = Field(None, description="Output schema of the resource")
    payTo: str = Field(..., description="Address to pay value to")
    maxTimeoutSeconds: int = Field(..., description="Maximum timeout in seconds")
    asset: str = Field(..., description="Address of the EIP-3009 compliant ERC20 contract")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra scheme-specific information")


class PaymentRequiredResponse(BaseModel):
    """
    Response sent by resource server when payment is required (402 status).
    """
    x402Version: int = Field(1, description="Version of the x402 payment protocol")
    accepts: List[PaymentRequirements] = Field(..., description="List of accepted payment requirements")
    error: Optional[str] = Field(None, description="Error message if applicable")


class ExactPaymentPayload(BaseModel):
    """
    Payload for the 'exact' payment scheme using EIP-3009 transferWithAuthorization.
    """
    from_: str = Field(..., alias="from", description="Address sending the payment")
    to: str = Field(..., description="Address receiving the payment")
    value: str = Field(..., description="Amount to transfer in atomic units")
    validAfter: str = Field(..., description="Timestamp after which transfer is valid")
    validBefore: str = Field(..., description="Timestamp before which transfer is valid")
    nonce: str = Field(..., description="Unique nonce for the transfer")
    v: int = Field(..., description="ECDSA signature v")
    r: str = Field(..., description="ECDSA signature r")
    s: str = Field(..., description="ECDSA signature s")


class PaymentPayload(BaseModel):
    """
    Payment payload included in the X-PAYMENT header.
    """
    x402Version: int = Field(1, description="Version of the x402 payment protocol")
    scheme: str = Field(..., description="Payment scheme being used")
    network: str = Field(..., description="Network ID for the payment")
    payload: Dict[str, Any] = Field(..., description="Scheme-dependent payload data")


class VerificationRequest(BaseModel):
    """
    Request to verify a payment (sent to facilitator /verify endpoint).
    """
    x402Version: int = Field(1, description="Version of the x402 payment protocol")
    paymentHeader: str = Field(..., description="Base64 encoded payment payload")
    paymentRequirements: PaymentRequirements = Field(..., description="Payment requirements")


class VerificationResponse(BaseModel):
    """
    Response from payment verification.
    """
    isValid: bool = Field(..., description="Whether the payment is valid")
    invalidReason: Optional[str] = Field(None, description="Reason if payment is invalid")


class SettlementRequest(BaseModel):
    """
    Request to settle a payment on-chain (sent to facilitator /settle endpoint).
    """
    x402Version: int = Field(1, description="Version of the x402 payment protocol")
    paymentHeader: str = Field(..., description="Base64 encoded payment payload")
    paymentRequirements: PaymentRequirements = Field(..., description="Payment requirements")


class SettlementResponse(BaseModel):
    """
    Response from payment settlement.
    """
    success: bool = Field(..., description="Whether the payment was successful")
    error: Optional[str] = Field(None, description="Error message if applicable")
    txHash: Optional[str] = Field(None, description="Transaction hash of settled payment")
    networkId: Optional[str] = Field(None, description="Network ID of the blockchain")


class SupportedKind(BaseModel):
    """
    A supported (scheme, network) pair.
    """
    scheme: str = Field(..., description="Payment scheme")
    network: str = Field(..., description="Network ID")


class SupportedResponse(BaseModel):
    """
    Response listing supported payment schemes and networks.
    """
    kinds: List[SupportedKind] = Field(..., description="List of supported kinds")


class PaymentStatus(str, Enum):
    """Status of a payment"""
    PENDING = "pending"
    VERIFIED = "verified"
    SETTLED = "settled"
    FAILED = "failed"


# EIP-3009 Domain Separator Components
class EIP712Domain(BaseModel):
    """EIP-712 domain separator"""
    name: str
    version: str
    chainId: int
    verifyingContract: str


# Type definitions for EIP-3009
EIP3009_TRANSFER_WITH_AUTHORIZATION_TYPEHASH = (
    "TransferWithAuthorization("
    "address from,"
    "address to,"
    "uint256 value,"
    "uint256 validAfter,"
    "uint256 validBefore,"
    "bytes32 nonce)"
)

# Constants
X402_VERSION = 1
X_PAYMENT_HEADER = "X-PAYMENT"
X_PAYMENT_RESPONSE_HEADER = "X-PAYMENT-RESPONSE"
