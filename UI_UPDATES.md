# Frontend UI Updates - Parameter Input Fields

## Summary
Updated the Streamlit frontend to allow users to configure parameters before testing each UnleashNFTs API endpoint.

## Changes Made

### 1. Dynamic Parameter Input Fields
Each endpoint now displays interactive input fields based on parameter types:

- **Select/Dropdown**: For predefined options (blockchain, chain_id, time_range, days)
- **Text Input**: For contract addresses
- **Number Input**: For token IDs

### 2. Endpoint Parameter Configuration

#### Supported Blockchains
- **No parameters needed** - Direct test

#### Market Insights
- `blockchain`: Select (ethereum, polygon, bsc, base, solana) - Default: ethereum
- `time_range`: Select (24h, 7d, 30d, 90d) - Default: 24h

#### Supported Collections
- `chain_id`: Select (Ethereum=1, Polygon=137, BSC=56) - Default: 1

#### NFT Valuation
- `chain_id`: Select (1, 137, 56) - Default: 1
- `contract_address`: Text Input - Default: BAYC (0xbc4ca0...)
- `token_id`: Number Input - Default: 1

#### Collection Scores
- `collection_address`: Text Input - Default: BAYC
- `blockchain`: Select (ethereum, polygon, bsc) - Default: ethereum
- `days`: Select (7, 30, 90 days) - Default: 30

#### Washtrade Analysis
- `collection_address`: Text Input - Default: BAYC
- `blockchain`: Select (ethereum, polygon, bsc) - Default: ethereum

#### Floor Price
- `collection_address`: Text Input - Default: BAYC
- `blockchain`: Select (ethereum, polygon, bsc) - Default: ethereum

### 3. User Flow
1. Navigate to **Test Endpoints** tab
2. Click on any endpoint card
3. **Configure parameters** using dropdowns/inputs
4. View the **dynamically generated URL**
5. Click **Test** button to make payment and fetch data

### 4. Key Features
✅ Real-time URL building as parameters change
✅ Sensible defaults (BAYC collection, Ethereum network)
✅ Clear parameter descriptions
✅ Support for different parameter types
✅ Easy to test different collections/chains/timeframes

## Testing
1. Start servers: `./start_servers.sh`
2. Open frontend: http://localhost:8501
3. Go to "Test Endpoints" tab
4. Select any endpoint and modify parameters
5. Click Test to execute with custom parameters

## Examples

### Test Different NFT Collections
- CryptoPunks: `0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb`
- Azuki: `0xed5af388653567af2f388e6224dc7c4b3241c544`
- Doodles: `0x8a90cab2b38dba80c64b7734e58ee1db38b8992e`

### Test Different Blockchains
- Switch between Ethereum, Polygon, BSC
- Different chain IDs for V1 endpoints
- Different names for V2 endpoints

### Test Different Time Ranges
- 24h for recent trends
- 7d for weekly analysis
- 30d/90d for long-term insights

## Technical Details
- Uses Streamlit's `st.selectbox()`, `st.text_input()`, `st.number_input()`
- URL templates with `.format()` for dynamic building
- Unique keys per parameter to avoid state conflicts
- Labels vs values for better UX (e.g., "Ethereum (1)" instead of just "1")
