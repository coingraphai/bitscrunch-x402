"""
Resource Server

Flask server that provides protected resources requiring x402 payment.
Includes payment middleware for automatic payment verification.
"""

import os
import sys
import json
import base64
import logging
import ssl
from functools import wraps
from typing import Optional, Dict, Callable
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol import (
    PaymentRequirements,
    PaymentRequiredResponse,
    X_PAYMENT_HEADER,
    X_PAYMENT_RESPONSE_HEADER,
)

# Load environment variables
load_dotenv()

# Custom SSL adapter to handle TLS version issues
class SSLAdapter(HTTPAdapter):
    """Custom adapter to handle SSL/TLS issues with older OpenSSL versions"""
    def init_poolmanager(self, *args, **kwargs):
        try:
            # Create a custom SSL context that supports modern TLS
            context = create_urllib3_context()
            # Allow TLS 1.2 and above
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            kwargs['ssl_context'] = context
        except Exception:
            # If SSL context creation fails, continue without custom context
            pass
        return super().init_poolmanager(*args, **kwargs)

# Create a requests session with the custom SSL adapter
def get_secure_session():
    """Create a requests session with proper SSL configuration"""
    session = requests.Session()
    try:
        session.mount('https://', SSLAdapter())
    except Exception as e:
        logger.warning(f"Could not configure custom SSL adapter: {e}")
        # Fall back to default session
        pass
    return session

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/x402_protocol.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("resource_server")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "http://localhost:8000")
RESOURCE_SERVER_ADDRESS = os.getenv("RESOURCE_SERVER_ADDRESS")
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")
NETWORK = os.getenv("NETWORK", "base-sepolia")
CHAIN_ID = os.getenv("CHAIN_ID", "84532")
TOKEN_DECIMALS = int(os.getenv("TOKEN_DECIMALS", "6"))


def create_payment_requirements(
    amount_usd: str,
    resource_path: str,
    description: str,
    mime_type: str = "application/json",
) -> PaymentRequirements:
    """
    Create payment requirements for a resource.

    Args:
        amount_usd: Amount in USD (e.g., "0.01")
        resource_path: Path to the resource
        description: Description of the resource
        mime_type: MIME type of the response

    Returns:
        PaymentRequirements object
    """
    # Convert USD to atomic units (assuming USDC with 6 decimals)
    amount_float = float(amount_usd.replace("$", ""))
    amount_atomic = int(amount_float * (10 ** TOKEN_DECIMALS))

    network_id = f"eip155:{CHAIN_ID}"

    return PaymentRequirements(
        scheme="exact",
        network=network_id,
        maxAmountRequired=str(amount_atomic),
        resource=resource_path,
        description=description,
        mimeType=mime_type,
        payTo=RESOURCE_SERVER_ADDRESS,
        maxTimeoutSeconds=60,
        asset=TOKEN_CONTRACT_ADDRESS,
        extra={
            "name": "USDC",  # Token name for EIP-712 (must match contract)
            "version": "2",  # Token version for EIP-712
        },
    )


def require_payment(amount_usd: str, description: str):
    """
    Decorator to require payment for a route.

    Args:
        amount_usd: Amount required (e.g., "$0.01")
        description: Description of the resource

    Returns:
        Decorated function
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for payment header
            payment_header = request.headers.get(X_PAYMENT_HEADER)

            if not payment_header:
                # No payment provided, return 402 with payment requirements
                logger.info(f"Payment required for {request.path}")
                
                payment_reqs = create_payment_requirements(
                    amount_usd=amount_usd,
                    resource_path=request.path,
                    description=description,
                    mime_type="application/json",
                )

                response_data = PaymentRequiredResponse(
                    x402Version=1,
                    accepts=[payment_reqs],
                )

                return jsonify(response_data.model_dump(by_alias=True)), 402

            # Payment provided, verify it
            logger.info(f"Verifying payment for {request.path}")

            payment_reqs = create_payment_requirements(
                amount_usd=amount_usd,
                resource_path=request.path,
                description=description,
            )

            try:
                # Call facilitator to settle payment
                settle_response = requests.post(
                    f"{FACILITATOR_URL}/settle",
                    json={
                        "x402Version": 1,
                        "paymentHeader": payment_header,
                        "paymentRequirements": payment_reqs.model_dump(by_alias=True),
                    },
                    timeout=120,
                )

                if settle_response.status_code != 200:
                    logger.error(f"Facilitator error: {settle_response.text}")
                    return jsonify({
                        "error": "Payment settlement failed",
                        "details": settle_response.text,
                    }), 402

                settle_data = settle_response.json()

                if not settle_data.get("success"):
                    logger.warning(f"Payment settlement failed: {settle_data.get('error')}")
                    response_data = PaymentRequiredResponse(
                        x402Version=1,
                        accepts=[payment_reqs],
                        error=settle_data.get("error", "Payment failed"),
                    )
                    return jsonify(response_data.model_dump(by_alias=True)), 402

                # Payment successful, call the original function
                logger.info(f"Payment successful for {request.path}, tx: {settle_data.get('txHash')}")
                
                result = f(*args, **kwargs)

                # Add payment response header if we got a transaction hash
                if settle_data.get("txHash"):
                    payment_response = {
                        "txHash": settle_data["txHash"],
                        "networkId": settle_data.get("networkId"),
                    }
                    
                    # If result is a Response object, add header to it
                    if isinstance(result, Response):
                        result.headers[X_PAYMENT_RESPONSE_HEADER] = base64.b64encode(
                            json.dumps(payment_response).encode()
                        ).decode()
                        return result
                    
                    # If result is a tuple (data, status_code), create response
                    if isinstance(result, tuple):
                        data, status_code = result
                        response = jsonify(data)
                        response.status_code = status_code
                        response.headers[X_PAYMENT_RESPONSE_HEADER] = base64.b64encode(
                            json.dumps(payment_response).encode()
                        ).decode()
                        return response
                    
                    # Otherwise, wrap in response
                    response = jsonify(result)
                    response.headers[X_PAYMENT_RESPONSE_HEADER] = base64.b64encode(
                        json.dumps(payment_response).encode()
                    ).decode()
                    return response

                return result

            except requests.Timeout:
                logger.error("Facilitator request timeout")
                return jsonify({"error": "Payment verification timeout"}), 408

            except Exception as e:
                logger.error(f"Payment verification error: {str(e)}")
                return jsonify({"error": f"Payment verification failed: {str(e)}"}), 500

        return decorated_function
    return decorator


# Routes

@app.route("/")
def root():
    """Root endpoint"""
    return jsonify({
        "service": "x402 Resource Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            {"path": "/weather", "price": "$0.01", "description": "Weather information"},
            {"path": "/article", "price": "$0.05", "description": "Premium article content"},
            {"path": "/data", "price": "$0.10", "description": "Analytics data"},
            {"path": "/unleashnfts/blockchains", "price": "$0.02", "description": "UnleashNFTs - Supported blockchains"},
            {"path": "/unleashnfts/market-insights", "price": "$0.05", "description": "UnleashNFTs - NFT market insights"},
            {"path": "/unleashnfts/supported-collections/{blockchain}", "price": "$0.03", "description": "UnleashNFTs - Supported collections for AI NFT valuation"},
            {"path": "/unleashnfts/nft-valuation/{blockchain}/{address}/{token}", "price": "$0.08", "description": "UnleashNFTs - AI powered NFT valuation"},
            {"path": "/unleashnfts/collection-scores", "price": "$0.04", "description": "UnleashNFTs - Collection scores and metrics"},
            {"path": "/unleashnfts/collection-washtrade", "price": "$0.06", "description": "UnleashNFTs - Collection washtrade analysis"},
            {"path": "/unleashnfts/floor-price", "price": "$0.03", "description": "UnleashNFTs - Collection floor price"},
        ],
    })


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


@app.route("/weather")
@require_payment("$0.01", "Current weather information")
def get_weather():
    """Example protected endpoint - weather data"""
    return jsonify({
        "location": "San Francisco, CA",
        "temperature": "68°F",
        "conditions": "Partly Cloudy",
        "humidity": "65%",
        "wind": "10 mph NW",
        "timestamp": "2025-10-31T12:00:00Z",
    })


@app.route("/article")
@require_payment("$0.05", "Premium article content")
def get_article():
    """Example protected endpoint - article content"""
    return jsonify({
        "title": "The Future of Internet Payments",
        "author": "Blockchain Enthusiast",
        "date": "2025-10-31",
        "content": (
            "The x402 protocol represents a paradigm shift in how we think about "
            "payments on the internet. By leveraging blockchain technology and "
            "integrating seamlessly with HTTP, x402 enables micropayments with "
            "minimal friction. This opens up new business models and use cases "
            "that were previously impractical due to high transaction fees and "
            "minimum payment amounts."
        ),
        "tags": ["payments", "blockchain", "web3"],
    })


@app.route("/data")
@require_payment("$0.10", "Analytics and insights data")
def get_data():
    """Example protected endpoint - analytics data"""
    return jsonify({
        "report_type": "User Analytics",
        "period": "October 2025",
        "metrics": {
            "total_users": 15420,
            "active_users": 8932,
            "new_signups": 1205,
            "retention_rate": 0.78,
            "avg_session_duration": "12m 34s",
        },
        "trends": {
            "user_growth": "+15.3%",
            "engagement": "+8.7%",
            "revenue": "+22.1%",
        },
    })


# ============================================
# bitsCrunch API Endpoints
# ============================================

@app.route("/unleashnfts/blockchains")
@require_payment("$0.02", "UnleashNFTs - Get supported blockchains")
def get_blockchains():
    """Protected endpoint - UnleashNFTs supported blockchains"""
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Get query parameters
        sort_by = request.args.get('sort_by', 'blockchain_name')
        offset = request.args.get('offset', '0')
        limit = request.args.get('limit', '10')
        
        # Make request to UnleashNFTs API using secure session
        url = "https://api.unleashnfts.com/api/v2/blockchains"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        params = {
            'sort_by': sort_by,
            'offset': offset,
            'limit': limit
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, params=params, timeout=10)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.route("/unleashnfts/market-insights")
@require_payment("$0.05", "UnleashNFTs - NFT market insights and analytics")
def get_market_insights():
    """Protected endpoint - UnleashNFTs NFT market insights"""
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Get query parameters
        blockchain = request.args.get('blockchain', 'ethereum')
        time_range = request.args.get('time_range', '24h')
        
        # Make request to UnleashNFTs API - correct endpoint path
        url = "https://api.unleashnfts.com/api/v2/nft/market-insights/analytics"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        params = {
            'blockchain': blockchain,
            'time_range': time_range
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, params=params, timeout=10)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.route("/unleashnfts/supported-collections/<int:blockchain>")
@require_payment("$0.03", "UnleashNFTs - Get supported collections for AI NFT valuation")
def get_supported_collections(blockchain):
    """Protected endpoint - UnleashNFTs supported collections for NFT valuation
    
    Args:
        blockchain: Chain ID (e.g., 1 for Ethereum, 137 for Polygon)
    """
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Make request to UnleashNFTs API v1 endpoint
        url = f"https://api.unleashnfts.com/api/v1/collections/{blockchain}/price_estimate/supported_collections"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, timeout=10)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.route("/unleashnfts/nft-valuation/<int:blockchain>/<address>/<token>")
@require_payment("$0.08", "UnleashNFTs - AI powered NFT valuation by token")
def get_nft_valuation(blockchain, address, token):
    """Protected endpoint - UnleashNFTs AI-powered NFT valuation
    
    Args:
        blockchain: Chain ID (e.g., 1 for Ethereum, 137 for Polygon)
        address: NFT contract address
        token: Token ID
    """
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Make request to UnleashNFTs API v1 endpoint
        url = f"https://api.unleashnfts.com/api/v1/nft/{blockchain}/{address}/{token}/price-estimate"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, timeout=15)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.route("/unleashnfts/collection-scores")
@require_payment("$0.04", "UnleashNFTs - Get collection scores and metrics")
def get_collection_scores():
    """Protected endpoint - UnleashNFTs collection scores and trends
    
    Query params:
        collection_address: NFT collection contract address
        blockchain: Chain ID (e.g., 1 for Ethereum)
        days: Number of days (optional)
    """
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Get query parameters
        collection_address = request.args.get('collection_address')
        blockchain = request.args.get('blockchain')
        days = request.args.get('days', '30')
        sort_by = request.args.get('sort_by', 'marketcap')  # Valid default
        
        if not collection_address or not blockchain:
            return {
                "error": "Missing required parameters",
                "message": "collection_address and blockchain are required"
            }, 400
        
        # Make request to UnleashNFTs API v2 endpoint
        url = "https://api.unleashnfts.com/api/v2/nft/collection/scores"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        params = {
            'collection_address': collection_address,
            'blockchain': blockchain,
            'days': days,
            'sort_by': sort_by
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, params=params, timeout=15)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.route("/unleashnfts/collection-washtrade")
@require_payment("$0.06", "UnleashNFTs - Get collection washtrade metrics")
def get_collection_washtrade():
    """Protected endpoint - UnleashNFTs collection washtrading analysis
    
    Query params:
        collection_address: NFT collection contract address
        blockchain: Chain ID (e.g., 1 for Ethereum)
    """
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Get query parameters
        collection_address = request.args.get('collection_address')
        blockchain = request.args.get('blockchain')
        sort_by = request.args.get('sort_by', 'washtrade_volume')  # Valid default
        
        if not collection_address or not blockchain:
            return {
                "error": "Missing required parameters",
                "message": "collection_address and blockchain are required"
            }, 400
        
        # Make request to UnleashNFTs API v2 endpoint
        url = "https://api.unleashnfts.com/api/v2/nft/collection/washtrade"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        params = {
            'collection_address': collection_address,
            'blockchain': blockchain,
            'sort_by': sort_by
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, params=params, timeout=15)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.route("/unleashnfts/floor-price")
@require_payment("$0.03", "UnleashNFTs - Get NFT collection floor price")
def get_floor_price():
    """Protected endpoint - UnleashNFTs collection floor price across marketplaces
    
    Query params:
        collection_address: NFT collection contract address
        blockchain: Chain ID (e.g., 1 for Ethereum)
    """
    try:
        api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not api_key or api_key == "your_bitscrunch_api_key_here":
            return {
                "error": "UnleashNFTs API key not configured",
                "message": "Please set BITSCRUNCH_API_KEY in .env file"
            }, 503
        
        # Get query parameters
        collection_address = request.args.get('collection_address')
        blockchain = request.args.get('blockchain')
        
        if not collection_address or not blockchain:
            return {
                "error": "Missing required parameters",
                "message": "collection_address and blockchain are required"
            }, 400
        
        # Make request to UnleashNFTs API v2 endpoint
        url = "https://api.unleashnfts.com/api/v2/nft/floor_price"
        headers = {
            'accept': 'application/json',
            'x-api-key': api_key
        }
        params = {
            'collection_address': collection_address,
            'blockchain': blockchain
        }
        
        # Use secure session to handle SSL/TLS properly
        session = get_secure_session()
        api_response = session.get(url, headers=headers, params=params, timeout=10)
        
        if api_response.status_code == 200:
            return api_response.json()
        else:
            return {
                "error": "UnleashNFTs API error",
                "status_code": api_response.status_code,
                "message": api_response.text
            }, api_response.status_code
            
    except requests.Timeout:
        return {"error": "Request timeout to UnleashNFTs API"}, 408
    except Exception as e:
        logger.error(f"Error calling UnleashNFTs API: {str(e)}")
        return {"error": f"Failed to fetch data: {str(e)}"}, 500


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


def main():
    """Main entry point"""
    port = int(os.getenv("RESOURCE_SERVER_PORT", 8001))
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    logger.info(f"Starting resource server on port {port}")
    logger.info(f"Payment address: {RESOURCE_SERVER_ADDRESS}")
    logger.info(f"Token contract: {TOKEN_CONTRACT_ADDRESS}")
    logger.info(f"Facilitator URL: {FACILITATOR_URL}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )


if __name__ == "__main__":
    main()
