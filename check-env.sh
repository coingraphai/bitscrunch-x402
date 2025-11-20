#!/bin/bash
# Verify and display .env configuration for production

echo "=============================================="
echo "x402 Production Environment Check"
echo "Server: 159.89.170.85"
echo "=============================================="
echo ""

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Create it from template:"
    echo "  cp .env.production.template .env"
    echo "  nano .env"
    exit 1
fi

echo "✅ .env file exists"
echo ""

# Check critical URLs
echo "🔍 Checking configuration..."
echo ""

RESOURCE_URL=$(grep "^RESOURCE_URL=" .env | cut -d'=' -f2)
FACILITATOR_URL=$(grep "^FACILITATOR_URL=" .env | cut -d'=' -f2)

echo "Resource URL: $RESOURCE_URL"
echo "Facilitator URL: $FACILITATOR_URL"
echo ""

# Warn if localhost is found
if echo "$RESOURCE_URL" | grep -q "localhost"; then
    echo "⚠️  WARNING: RESOURCE_URL contains 'localhost'"
    echo "   For production, it should be:"
    echo "   RESOURCE_URL=http://159.89.170.85/api/resource"
    echo ""
fi

if echo "$FACILITATOR_URL" | grep -q "localhost"; then
    echo "⚠️  WARNING: FACILITATOR_URL contains 'localhost'"
    echo "   For production, it should be:"
    echo "   FACILITATOR_URL=http://159.89.170.85/api/facilitator"
    echo ""
fi

# Check ports
RESOURCE_PORT=$(grep "^RESOURCE_SERVER_PORT=" .env | cut -d'=' -f2)
FACILITATOR_PORT=$(grep "^FACILITATOR_SERVER_PORT=" .env | cut -d'=' -f2)
STREAMLIT_PORT=$(grep "^STREAMLIT_PORT=" .env | cut -d'=' -f2)

echo "Ports configured:"
echo "  Resource: $RESOURCE_PORT (should be 3000)"
echo "  Facilitator: $FACILITATOR_PORT (should be 3001)"
echo "  Streamlit: $STREAMLIT_PORT (should be 4000)"
echo ""

# Check if ports match expected
if [ "$RESOURCE_PORT" != "3000" ] || [ "$FACILITATOR_PORT" != "3001" ] || [ "$STREAMLIT_PORT" != "4000" ]; then
    echo "⚠️  WARNING: Ports don't match production configuration!"
    echo ""
fi

# Check for placeholder values
if grep -q "your_.*_here" .env; then
    echo "⚠️  WARNING: Found placeholder values in .env"
    echo "   Make sure to replace all 'your_*_here' values with actual keys"
    echo ""
    grep "your_.*_here" .env | head -5
    echo ""
fi

echo "=============================================="
echo "💡 Production URLs should be:"
echo "=============================================="
echo "RESOURCE_URL=http://159.89.170.85/api/resource"
echo "FACILITATOR_URL=http://159.89.170.85/api/facilitator"
echo ""
echo "Ports (internal):"
echo "RESOURCE_SERVER_PORT=3000"
echo "FACILITATOR_SERVER_PORT=3001"
echo "STREAMLIT_PORT=4000"
echo ""

