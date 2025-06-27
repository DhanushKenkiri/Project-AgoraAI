// X402 Client Implementation for NFT Payments
// This file demonstrates how to create an X402 payment header for use with the protocol

/**
 * Creates an X402 payment header for exact payments scheme on EVM networks
 * @param {Object} paymentRequirements - The payment requirements from the 402 Payment Required response
 * @param {string} privateKey - The user's private key for signing the payment
 * @returns {string} Base64 encoded X402 payment header
 */
async function createX402PaymentHeader(paymentRequirements, privateKey) {
  try {
    // Import required libraries
    const { ethers } = require('ethers');
    
    // Extract payment details from requirements
    const {
      scheme,
      network,
      maxAmountRequired,
      payTo,
      asset,
      resource,
      extra
    } = paymentRequirements;
    
    // Only support 'exact' scheme on EVM networks for now
    if (scheme !== 'exact' || !network.includes('base') || !network.includes('ethereum')) {
      throw new Error(`Unsupported payment scheme or network: ${scheme} on ${network}`);
    }
    
    // Create a wallet from the private key
    const wallet = new ethers.Wallet(privateKey);
    
    // Determine if this is an ETH or ERC-20 payment
    const isETH = !asset || asset === '0x0000000000000000000000000000000000000000';
    
    // Get the current timestamp for the message
    const timestamp = Math.floor(Date.now() / 1000);
    
    // Create a nonce for security
    const nonce = ethers.utils.hexlify(ethers.utils.randomBytes(32));
    
    // For ERC-20 transfers, we use the EIP-3009 authorization pattern
    // For ETH transfers, we create a signed message
    let payload;
    
    if (isETH) {
      // Create the ETH payment payload
      payload = {
        type: 'native',
        from: wallet.address,
        to: payTo,
        amount: maxAmountRequired,
        timestamp,
        nonce,
        resource
      };
      
      // Create message hash
      const messageHash = ethers.utils.keccak256(
        ethers.utils.defaultAbiCoder.encode(
          ['address', 'address', 'uint256', 'uint256', 'bytes32', 'string'],
          [payload.from, payload.to, payload.amount, payload.timestamp, payload.nonce, payload.resource]
        )
      );
      
      // Sign the message
      const signature = await wallet.signMessage(ethers.utils.arrayify(messageHash));
      payload.signature = signature;
      
    } else {
      // Create the ERC-20 payment payload using EIP-3009
      // Requires the token to implement the EIP-3009 interface
      const typedData = {
        types: {
          EIP712Domain: [
            { name: 'name', type: 'string' },
            { name: 'version', type: 'string' },
            { name: 'chainId', type: 'uint256' },
            { name: 'verifyingContract', type: 'address' }
          ],
          TransferWithAuthorization: [
            { name: 'from', type: 'address' },
            { name: 'to', type: 'address' },
            { name: 'value', type: 'uint256' },
            { name: 'validAfter', type: 'uint256' },
            { name: 'validBefore', type: 'uint256' },
            { name: 'nonce', type: 'bytes32' }
          ]
        },
        primaryType: 'TransferWithAuthorization',
        domain: {
          name: extra?.name || 'Token',
          version: extra?.version || '1',
          chainId: getChainId(network),
          verifyingContract: asset
        },
        message: {
          from: wallet.address,
          to: payTo,
          value: maxAmountRequired,
          validAfter: timestamp,
          validBefore: timestamp + 3600, // Valid for 1 hour
          nonce: nonce
        }
      };
      
      // Sign the typed data
      const signature = await wallet._signTypedData(
        typedData.domain,
        { TransferWithAuthorization: typedData.types.TransferWithAuthorization },
        typedData.message
      );
      
      payload = {
        type: 'erc20-3009',
        token: asset,
        from: wallet.address,
        to: payTo,
        value: maxAmountRequired,
        validAfter: timestamp,
        validBefore: timestamp + 3600,
        nonce: nonce,
        signature,
        resource
      };
    }
    
    // Create the X402 payment header
    const x402Header = {
      x402Version: 1,
      scheme,
      network,
      payload
    };
    
    // Base64 encode the header
    const headerJson = JSON.stringify(x402Header);
    const encodedHeader = Buffer.from(headerJson).toString('base64');
    
    return encodedHeader;
    
  } catch (error) {
    console.error('Error creating X402 payment header:', error);
    throw error;
  }
}

/**
 * Get the chain ID for a given network
 */
function getChainId(network) {
  const chainIds = {
    'base-sepolia': 84532,
    'base': 8453,
    'ethereum': 1,
    'ethereum-sepolia': 11155111
  };
  
  return chainIds[network] || 1;
}

/**
 * Makes a request to a resource that requires payment
 * @param {string} url - URL of the resource
 * @param {Object} options - Request options
 * @param {string} privateKey - Private key for payment signing
 * @returns {Promise<Object>} Response data
 */
async function makePaymentRequest(url, options = {}, privateKey) {
  try {
    const axios = require('axios');
    
    // First, make a request to check if payment is required
    const response = await axios(url, { 
      ...options,
      validateStatus: status => true // Accept any status code
    });
    
    // If payment is required (402 status code)
    if (response.status === 402 && response.data.accepts) {
      console.log('Payment required for this resource');
      
      // Get the first payment requirement (you could choose based on preferred currency)
      const paymentRequirements = response.data.accepts[0];
      
      // Create the payment header
      const paymentHeader = await createX402PaymentHeader(paymentRequirements, privateKey);
      
      // Make the request again with the payment header
      const paidResponse = await axios({
        ...options,
        url,
        headers: {
          ...options.headers,
          'X-PAYMENT': paymentHeader
        }
      });
      
      // Get the payment response header if it exists
      const paymentResponseHeader = paidResponse.headers['x-payment-response'];
      if (paymentResponseHeader) {
        const paymentResponse = JSON.parse(Buffer.from(paymentResponseHeader, 'base64').toString());
        console.log('Payment processed:', paymentResponse);
      }
      
      return paidResponse.data;
    }
    
    // If no payment required, return the response data
    return response.data;
    
  } catch (error) {
    console.error('Error making payment request:', error);
    throw error;
  }
}

// Example usage:
/*
async function getExclusiveNFTData() {
  const privateKey = process.env.WALLET_PRIVATE_KEY;
  const url = 'https://api.example.com/premium-nft-data';
  
  try {
    const data = await makePaymentRequest(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    }, privateKey);
    
    console.log('Received exclusive NFT data:', data);
    return data;
  } catch (error) {
    console.error('Failed to get NFT data:', error);
  }
}
*/

module.exports = {
  createX402PaymentHeader,
  makePaymentRequest
};
