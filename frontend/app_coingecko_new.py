"""
Streamlit Frontend for x402 Protocol with UnleashNFTs API Integration

Simplified UI for testing UnleashNFTs Analytics endpoints.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import time
import subprocess

# Fix asyncio event loop issue
if sys.platform == 'darwin':
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Page configuration
st.set_page_config(
    page_title="x402 Protocol - UnleashNFTs API",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .demo-output {
        background-color: #1e1e1e;
        color: #00ff00;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "http://localhost:8002")
RESOURCE_URL = os.getenv("RESOURCE_URL", "http://localhost:8001")

# Header
st.markdown('<div class="main-header">💳 x402 Protocol - UnleashNFTs API</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">HTTP-Native Payments for NFT Analytics</div>', unsafe_allow_html=True)

# Helper Functions
def check_server_health(url, name):
    """Check if server is online"""
    try:
        response = requests.get(f"{url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def run_single_endpoint(endpoint_url, endpoint_name):
    """Run payment for a single endpoint and capture output"""
    try:
        # Get environment variables
        private_key = os.getenv("CLIENT_PRIVATE_KEY")
        rpc_url = os.getenv("RPC_URL")
        
        if not private_key or not rpc_url:
            return None, "Environment variables not configured", 1
        
        # Create a temporary Python script to run the payment
        script_content = f"""
import sys
import os
import asyncio
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore')

# Fix asyncio event loop for macOS
if sys.platform == 'darwin':
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# Set working directory and add to path
os.chdir('/Users/ajayprashanth/Documents/bitsCrunch/bitsCrunch-x402')
sys.path.insert(0, '/Users/ajayprashanth/Documents/bitsCrunch/bitsCrunch-x402')
sys.path.insert(0, '/Users/ajayprashanth/Documents/bitsCrunch/bitsCrunch-x402/backend')

from dotenv import load_dotenv
load_dotenv()

# Import the client module
import client as client_module

private_key = os.getenv("CLIENT_PRIVATE_KEY")
rpc_url = os.getenv("RPC_URL")
endpoint_url = "{endpoint_url}"

try:
    print(f"Initializing client...")
    client = client_module.create_client(private_key, rpc_url)
    print(f"Client Address: {{client.account.address}}")
    print(f"Requesting: {{endpoint_url}}")
    print("-" * 60)
    
    response = client.request_resource(endpoint_url, auto_pay=True)
    print(f"Status Code: {{response.status_code}}")
    
    if response.status_code == 200:
        print("✅ Payment successful!")
        
        # Decode payment response to get transaction hash
        payment_info = client.decode_payment_response(response)
        if payment_info:
            tx_hash = payment_info.get('txHash', 'Not available')
            network = payment_info.get('networkId', 'Not available')
            print(f"Transaction Hash: {{tx_hash}}")
            print(f"Network: {{network}}")
        else:
            print("Transaction Hash: Not available")
            print("Network: Not available")
        
        print()
        print("Response Data:")
        import json
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Payment failed with status code: {{response.status_code}}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error occurred: {{str(e)}}")
    import traceback
    traceback.print_exc()
"""
        
        # Write to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                ['./venv-py311/bin/python', temp_script],
                cwd='/Users/ajayprashanth/Documents/bitsCrunch/bitsCrunch-x402',
                capture_output=True,
                text=True,
                timeout=30,
                env=dict(os.environ, PYTHONPATH='/Users/ajayprashanth/Documents/bitsCrunch/bitsCrunch-x402')
            )
            return result.stdout, result.stderr, result.returncode
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_script)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return None, "Timeout: Request took too long (>30s)", 1
    except Exception as e:
        return None, str(e), 1

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.markdown("### 🔧 Server Endpoints")
    facilitator_url = st.text_input("Facilitator", FACILITATOR_URL)
    resource_url = st.text_input("Resource", RESOURCE_URL)
    
    st.markdown("---")
    st.markdown("### 📊 Server Status")
    
    facilitator_online = check_server_health(facilitator_url, "Facilitator")
    resource_online = check_server_health(resource_url, "Resource")
    
    if facilitator_online:
        st.success("✅ Facilitator Online")
    else:
        st.error("❌ Facilitator Offline")
    
    if resource_online:
        st.success("✅ Resource Server Online")
    else:
        st.error("❌ Resource Server Offline")
    
    st.markdown("---")
    st.markdown("### 💰 Wallet Info")
    
    client_pk = os.getenv("CLIENT_PRIVATE_KEY", "")
    if client_pk:
        st.success("✅ Wallet Configured")
    else:
        st.warning("⚠️ Wallet Not Set")

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Overview",
    "🎮 Test Endpoints",
    "🤖 AI Assistant",
    "📚 Documentation"
])

# Tab 1: Overview
with tab1:
    st.header("🏠 Welcome to x402 Protocol")
    
    st.subheader("🌐 What is x402?")
    st.markdown("""
    The **x402 protocol** enables HTTP-native payments with blockchain settlement:
    
    - 💰 **Micropayments** for web resources
    - 🔐 **Cryptographic** payment verification
    - ⚡ **Fast** blockchain settlement on Base Sepolia
    - 🌐 **Open standard** for internet payments
    
    ### How It Works
    
    1. Client requests protected resource
    2. Server responds with 402 Payment Required
    3. Client creates signed payment authorization
    4. Facilitator verifies and settles on blockchain
    5. Client receives protected content
    """)
    
    if facilitator_online and resource_online:
        st.success("✅ All systems operational! Go to **Test Endpoints** tab to test UnleashNFTs API.")
    else:
        st.error("⚠️ Some services are offline. Please check server status.")

# Tab 2: Test Endpoints - Individual UnleashNFTs API Testing
with tab2:
    st.header("🎮 Test UnleashNFTs API Endpoints")
    
    st.markdown("""
    Select and test individual UnleashNFTs endpoints. Each payment creates a real blockchain transaction on Base Sepolia.
    """)
    
    if not (facilitator_online and resource_online):
        st.error("⚠️ Both servers must be online to test endpoints")
    elif not client_pk:
        st.error("⚠️ CLIENT_PRIVATE_KEY not configured in .env file")
    else:
        st.success("✅ Ready to test UnleashNFTs API endpoints!")
        
        # Define UnleashNFTs endpoints only
        unleash_endpoints = [
            {
                "name": "Supported Blockchains",
                "icon": "⛓️",
                "url": "http://localhost:8001/unleashnfts/blockchains",
                "price": "$0.02",
                "description": "Get list of all supported blockchains (Ethereum, Polygon, BSC, Solana, etc.)",
                "key": "unleashnfts_blockchains",
                "example": "Returns: Base, BSC, Ethereum, Ordinals, Polygon, Solana"
            },
            {
                "name": "Market Insights",
                "icon": "📈",
                "url": "http://localhost:8001/unleashnfts/market-insights?blockchain=ethereum&time_range=24h",
                "price": "$0.05",
                "description": "NFT market analytics including volume, sales, and trends for Ethereum (24h)",
                "key": "unleashnfts_market",
                "example": "Parameters: blockchain=ethereum, time_range=24h"
            },
            {
                "name": "Supported Collections",
                "icon": "🖼️",
                "url": "http://localhost:8001/unleashnfts/supported-collections/1",
                "price": "$0.03",
                "description": "Get NFT collections with AI-powered valuation support on Ethereum (Chain ID: 1)",
                "key": "unleashnfts_collections",
                "example": "Returns: 30+ collections including BAYC, CryptoPunks, Azuki, etc."
            },
            {
                "name": "NFT Valuation",
                "icon": "💎",
                "url": "http://localhost:8001/unleashnfts/nft-valuation/1/0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d/1",
                "price": "$0.08",
                "description": "AI-powered price estimation for BAYC #1 on Ethereum",
                "key": "unleashnfts_valuation",
                "example": "BAYC #1 - AI estimates value based on traits, rarity, market trends"
            },
            {
                "name": "Collection Scores",
                "icon": "📊",
                "url": "http://localhost:8001/unleashnfts/collection-scores?collection_address=0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d&blockchain=ethereum&days=30",
                "price": "$0.04",
                "description": "Comprehensive scores and metrics for BAYC collection (30 days)",
                "key": "unleashnfts_scores",
                "example": "Includes: Market cap, price averages, minting revenue, royalties"
            },
            {
                "name": "Washtrade Analysis",
                "icon": "🔍",
                "url": "http://localhost:8001/unleashnfts/collection-washtrade?collection_address=0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d&blockchain=ethereum",
                "price": "$0.06",
                "description": "Detect suspicious wash trading activity for BAYC collection",
                "key": "unleashnfts_washtrade",
                "example": "Analyzes: Suspect sales, washtrade volume, affected wallets"
            },
            {
                "name": "Floor Price",
                "icon": "💰",
                "url": "http://localhost:8001/unleashnfts/floor-price?collection_address=0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d&blockchain=ethereum",
                "price": "$0.03",
                "description": "Real-time floor price for BAYC across 30+ marketplaces",
                "key": "unleashnfts_floor",
                "example": "Compares prices: OpenSea, Blur, LooksRare, X2Y2, and more"
            }
        ]
        
        st.markdown("### 🚀 Select an Endpoint to Test")
        st.markdown("---")
        
        # Display each endpoint as an expandable card
        for idx, endpoint in enumerate(unleash_endpoints):
            with st.expander(f"{endpoint['icon']} **{endpoint['name']}** - {endpoint['price']}", expanded=False):
                # Header row
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {endpoint['icon']} {endpoint['name']}")
                    st.markdown(f"**{endpoint['description']}**")
                
                with col2:
                    st.markdown(f"### {endpoint['price']}")
                    st.markdown("**USDC**")
                
                st.markdown("---")
                
                # Details
                st.markdown(f"**📍 Endpoint URL:**")
                st.code(endpoint['url'], language=None)
                
                st.markdown(f"**💡 Example:**")
                st.info(endpoint['example'])
                
                st.markdown("---")
                
                # Test button
                col1, col2, col3 = st.columns([2, 3, 2])
                
                with col2:
                    test_button = st.button(
                        f"🚀 Test {endpoint['name']}", 
                        key=f"test_{endpoint['key']}",
                        use_container_width=True,
                        type="primary"
                    )
                
                # Handle button click
                if test_button:
                    st.markdown("---")
                    st.markdown(f"### 🔄 Processing Payment for {endpoint['name']}...")
                    
                    with st.spinner(f"Making payment and fetching data... (10-15 seconds)"):
                        stdout, stderr, returncode = run_single_endpoint(endpoint['url'], endpoint['name'])
                    
                    # Process output
                    full_output = ""
                    
                    if stderr:
                        # Filter out warnings
                        stderr_lines = stderr.split('\n')
                        filtered_stderr = [line for line in stderr_lines 
                                         if "NotOpenSSLWarning" not in line 
                                         and "urllib3" not in line 
                                         and "warnings.warn" not in line 
                                         and line.strip()]
                        if filtered_stderr:
                            full_output += '\n'.join(filtered_stderr) + "\n"
                    
                    if stdout:
                        full_output += stdout
                    
                    # Check for success
                    has_success = ("✅ Payment successful!" in full_output or 
                                 "Status Code: 200" in full_output)
                    
                    if has_success:
                        st.success(f"✅ Payment to **{endpoint['name']}** successful!")
                        
                        # Extract transaction details
                        tx_hash = None
                        network = None
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if "Transaction Hash:" in full_output:
                                lines = full_output.split('\n')
                                for line in lines:
                                    if "Transaction Hash:" in line:
                                        tx_hash = line.split("Transaction Hash:")[-1].strip()
                                        if tx_hash and tx_hash != "Not available":
                                            st.markdown("**🔗 Transaction Hash:**")
                                            st.code(tx_hash, language=None)
                                            break
                        
                        with col2:
                            if "Network:" in full_output:
                                lines = full_output.split('\n')
                                for line in lines:
                                    if "Network:" in line and "Transaction" not in line:
                                        network = line.split("Network:")[-1].strip()
                                        if network and network != "Not available":
                                            st.markdown("**🌐 Network:**")
                                            st.code(network, language=None)
                                            break
                        
                        # BaseScan link
                        if tx_hash and tx_hash != "Not available" and tx_hash.startswith("0x"):
                            st.markdown(f"### 🔍 [View Transaction on BaseScan ↗](https://sepolia.basescan.org/tx/{tx_hash})")
                        
                        # Response data
                        st.markdown("### 📦 Response Data")
                        with st.expander("Click to view full API response", expanded=True):
                            if "Response Data:" in full_output:
                                response_start = full_output.find("Response Data:")
                                response_data = full_output[response_start:]
                                st.code(response_data, language="json")
                            else:
                                st.code(full_output, language=None)
                    
                    else:
                        st.error(f"❌ Payment to **{endpoint['name']}** failed")
                        st.markdown("**Error Details:**")
                        st.code(full_output if full_output else "No output received", language=None)
                        
                        st.warning("""
                        **Troubleshooting:**
                        - Ensure Facilitator and Resource servers are running
                        - Check USDC balance in your wallet
                        - Verify enough ETH for gas fees
                        - Check server logs for detailed errors
                        """)

# Tab 3: AI Assistant
with tab3:
    st.header("🤖 AI Assistant")
    
    st.markdown("""
    Ask questions about x402 protocol, UnleashNFTs API, or blockchain payments!
    """)
    
    # Chat interface
    user_question = st.text_input("Ask a question:", placeholder="e.g., How does x402 work?")
    
    if st.button("Ask AI"):
        if user_question:
            with st.spinner("AI is thinking..."):
                # Simulated AI responses
                ai_responses = {
                    "how does x402 work": "x402 is an HTTP-native payment protocol that integrates blockchain payments directly into web requests. When you request a protected resource, the server responds with 402 Payment Required, you sign a payment authorization, and the facilitator settles it on-chain.",
                    "what is eip-3009": "EIP-3009 introduces transferWithAuthorization, allowing token transfers to be authorized via signatures. This enables gas-less token transfers where a relayer can submit the transaction on behalf of the token holder.",
                    "base sepolia": "Base Sepolia is the testnet for Base, Coinbase's Ethereum L2. It uses Chain ID 84532 and allows developers to test applications without spending real ETH or tokens.",
                    "usdc": "USDC is a stablecoin pegged to the US Dollar (1 USDC = $1 USD). It's widely used for payments and DeFi applications. The x402 protocol uses USDC for micropayments.",
                    "unleashnfts": "UnleashNFTs provides advanced NFT analytics including AI-powered valuations, wash trade detection, collection scores, and floor price tracking across 30+ marketplaces.",
                }
                
                response = "I'm an AI assistant specialized in x402 protocol and UnleashNFTs API. "
                
                question_lower = user_question.lower()
                found = False
                
                for key, value in ai_responses.items():
                    if key in question_lower:
                        response = value
                        found = True
                        break
                
                if not found:
                    response += "Try asking about x402 protocol, UnleashNFTs endpoints, or blockchain payments!"
                
                st.success(f"🤖 **AI Response:**\n\n{response}")
        else:
            st.warning("Please enter a question")
    
    st.markdown("---")
    
    st.subheader("💡 Quick Tips")
    
    tips = [
        "💰 Always ensure you have enough USDC and ETH for gas on Base Sepolia testnet",
        "🔐 Never share your private keys - they're stored securely in .env file",
        "⚡ Transactions on Base Sepolia usually confirm in 2-3 seconds",
        "🎮 Use the Test Endpoints tab to try UnleashNFTs API with real payments",
        "📊 Each endpoint provides unique NFT analytics and insights",
    ]
    
    for tip in tips:
        st.info(tip)

# Tab 4: Documentation
with tab4:
    st.header("📚 Documentation")
    
    st.subheader("🚀 Quick Start")
    st.code("""
# 1. Start all servers
./start_servers.sh

# 2. Open frontend
streamlit run frontend/app_coingecko.py

# 3. Go to Test Endpoints tab and select an endpoint
    """, language="bash")
    
    st.markdown("---")
    
    st.subheader("📡 UnleashNFTs API Endpoints")
    
    with st.expander("Available Endpoints"):
        st.markdown("""
        **Standard Endpoints:**
        - **GET /unleashnfts/blockchains** - Supported blockchains ($0.02)
        - **GET /unleashnfts/market-insights** - NFT market analytics ($0.05)
        - **GET /unleashnfts/supported-collections/{blockchain_id}** - Collections with AI valuation ($0.03)
        - **GET /unleashnfts/nft-valuation/{blockchain_id}/{contract}/{token}** - AI price estimate ($0.08)
        - **GET /unleashnfts/collection-scores** - Collection metrics ($0.04)
        - **GET /unleashnfts/collection-washtrade** - Wash trade detection ($0.06)
        - **GET /unleashnfts/floor-price** - Floor prices across marketplaces ($0.03)
        """)
    
    with st.expander("Example: Test BAYC Floor Price"):
        st.code("""
# Request
GET /unleashnfts/floor-price?collection_address=0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d&blockchain=ethereum

# Response
{
  "data": [
    {
      "marketplace": "OpenSea",
      "floor_price": "32.5 ETH"
    },
    {
      "marketplace": "Blur",
      "floor_price": "32.3 ETH"
    },
    ...
  ]
}
        """, language="json")
    
    st.markdown("---")
    
    st.subheader("🔗 Useful Links")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - [x402 Protocol](https://x402.org)
        - [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009)
        - [Base Sepolia](https://base.org)
        """)
    
    with col2:
        st.markdown("""
        - [UnleashNFTs API](https://unleashnfts.com)
        - [USDC Info](https://www.circle.com/usdc)
        - [GitHub Repo](https://github.com/coinbase/x402)
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>💳 x402 Protocol Dashboard | UnleashNFTs API Integration</p>
    <p>Powered by Base Sepolia Testnet</p>
</div>
""", unsafe_allow_html=True)
