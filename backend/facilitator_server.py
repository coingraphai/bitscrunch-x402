"""
Facilitator Server

FastAPI server that provides /verify, /settle, and /supported endpoints
for the x402 payment protocol.
"""

import os
import sys
import json
import base64
import logging
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol import (
    VerificationRequest,
    VerificationResponse,
    SettlementRequest,
    SettlementResponse,
    SupportedResponse,
    SupportedKind,
    PaymentPayload,
)
from verification import create_payment_verifier
from settlement import create_payment_settler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/x402_protocol.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("facilitator_server")

# Initialize FastAPI app
app = FastAPI(
    title="x402 Facilitator Server",
    description="Facilitator server for x402 payment protocol verification and settlement",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for verifier and settler
payment_verifier: Optional[object] = None
payment_settler: Optional[object] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global payment_verifier, payment_settler

    try:
        # Create logs directory
        os.makedirs("logs", exist_ok=True)

        # Get configuration
        rpc_url = os.getenv("RPC_URL")
        private_key = os.getenv("FACILITATOR_PRIVATE_KEY")
        network = os.getenv("NETWORK", "base-sepolia")

        if not rpc_url:
            raise ValueError("RPC_URL not set in environment")
        if not private_key:
            raise ValueError("FACILITATOR_PRIVATE_KEY not set in environment")

        # Initialize verifier
        logger.info(f"Initializing payment verifier for network: {network}")
        payment_verifier = create_payment_verifier(rpc_url)
        logger.info("Payment verifier initialized successfully")

        # Initialize settler
        logger.info("Initializing payment settler")
        payment_settler = create_payment_settler(rpc_url, private_key)
        logger.info(f"Payment settler initialized with address: {payment_settler.account.address}")

    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "x402 Facilitator Server",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "verifier_initialized": payment_verifier is not None,
        "settler_initialized": payment_settler is not None,
    }


@app.post("/verify", response_model=VerificationResponse)
async def verify_payment(request: VerificationRequest):
    """
    Verify a payment without settling it on-chain.

    Args:
        request: Verification request containing payment header and requirements

    Returns:
        VerificationResponse indicating if payment is valid
    """
    try:
        logger.info(f"Received verification request for resource: {request.paymentRequirements.resource}")

        if not payment_verifier:
            raise HTTPException(status_code=503, detail="Payment verifier not initialized")

        # Verify the payment
        is_valid, error = payment_verifier.verify_payment(
            request.paymentHeader,
            request.paymentRequirements,
        )

        logger.info(f"Verification result: valid={is_valid}, error={error}")

        return VerificationResponse(
            isValid=is_valid,
            invalidReason=error,
        )

    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/settle", response_model=SettlementResponse)
async def settle_payment(request: SettlementRequest):
    """
    Verify and settle a payment on the blockchain.

    Args:
        request: Settlement request containing payment header and requirements

    Returns:
        SettlementResponse with transaction details
    """
    try:
        logger.info(f"Received settlement request for resource: {request.paymentRequirements.resource}")

        if not payment_verifier or not payment_settler:
            raise HTTPException(status_code=503, detail="Services not initialized")

        # First verify the payment
        is_valid, error = payment_verifier.verify_payment(
            request.paymentHeader,
            request.paymentRequirements,
        )

        if not is_valid:
            logger.warning(f"Payment verification failed: {error}")
            return SettlementResponse(
                success=False,
                error=f"Verification failed: {error}",
                txHash=None,
                networkId=None,
            )

        # Decode payment payload
        payment_data = base64.b64decode(request.paymentHeader)
        payment_payload = PaymentPayload.model_validate_json(payment_data)

        # Settle the payment
        logger.info("Payment verified, proceeding with settlement")
        success, error, tx_hash = payment_settler.settle_payment(
            payment_payload,
            request.paymentRequirements,
            wait_for_confirmation=True,
            timeout=120,
        )

        if success:
            logger.info(f"Payment settled successfully: tx_hash={tx_hash}")
        else:
            logger.error(f"Payment settlement failed: {error}")

        return SettlementResponse(
            success=success,
            error=error,
            txHash=tx_hash,
            networkId=request.paymentRequirements.network if success else None,
        )

    except Exception as e:
        logger.error(f"Settlement error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Settlement failed: {str(e)}")


@app.get("/supported", response_model=SupportedResponse)
async def get_supported():
    """
    Get list of supported payment schemes and networks.

    Returns:
        SupportedResponse with list of supported (scheme, network) pairs
    """
    try:
        network = os.getenv("NETWORK", "base-sepolia")
        chain_id = os.getenv("CHAIN_ID", "84532")
        network_id = f"eip155:{chain_id}"

        supported_kinds = [
            SupportedKind(
                scheme="exact",
                network=network_id,
            ),
            # Add more supported schemes here
        ]

        logger.info(f"Returning {len(supported_kinds)} supported kinds")

        return SupportedResponse(kinds=supported_kinds)

    except Exception as e:
        logger.error(f"Error getting supported kinds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported kinds: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def main():
    """Main entry point"""
    port = int(os.getenv("FACILITATOR_SERVER_PORT", 8000))
    
    logger.info(f"Starting facilitator server on port {port}")
    
    uvicorn.run(
        "facilitator_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
