/**
 * CDP Wallet and X402 Payment Frontend Integration
 * 
 * This file provides the frontend code for connecting to CDP wallets
 * and making X402 payments through your Lambda API.
 */

// CDP Wallet Connection and Payment Handler
class CDPWalletHandler {
  constructor(apiEndpoint) {
    this.apiEndpoint = apiEndpoint;
    this.sessionId = localStorage.getItem('cdp_session_id') || null;
    this.walletAddress = localStorage.getItem('cdp_wallet_address') || null;
    this.walletConnected = false;
    this.paymentHeader = null;
  }

  /**
   * Initialize the wallet handler and check connection status
   */
  async initialize() {
    // Check if we have a stored session
    if (this.sessionId) {
      await this.checkWalletStatus();
    }
    return this.walletConnected;
  }

  /**
   * Check current wallet connection status
   */
  async checkWalletStatus() {
    try {
      const response = await fetch(`${this.apiEndpoint}/cdp/wallet/status?session_id=${this.sessionId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': this.sessionId
        }
      });
      
      const result = await response.json();
      
      if (result.success && result.connected) {
        this.walletConnected = true;
        this.walletAddress = result.wallet_address;
        localStorage.setItem('cdp_wallet_address', this.walletAddress);
        return {
          connected: true,
          walletAddress: this.walletAddress,
          expiresAt: result.expiration
        };
      } else {
        this.walletConnected = false;
        return { connected: false };
      }
    } catch (error) {
      console.error('Error checking wallet status:', error);
      return { connected: false, error: error.message };
    }
  }

  /**
   * Connect to CDP wallet
   * @param {string} walletAddress - The wallet address to connect
   * @param {string} signature - Optional signature for verification
   * @param {string} message - Message that was signed
   */
  async connectWallet(walletAddress, signature = null, message = null) {
    try {
      const payload = {
        wallet_address: walletAddress,
        wallet_type: 'cdp'
      };
      
      // Add signature if provided
      if (signature && message) {
        payload.signature = signature;
        payload.message = message;
      }
      
      const response = await fetch(`${this.apiEndpoint}/cdp/wallet/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': this.sessionId || '' // Send empty if we don't have one yet
        },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      
      if (result.success) {
        this.sessionId = result.session_id;
        this.walletAddress = walletAddress;
        this.walletConnected = true;
        
        // Store in local storage
        localStorage.setItem('cdp_session_id', this.sessionId);
        localStorage.setItem('cdp_wallet_address', this.walletAddress);
        
        return {
          success: true,
          sessionId: this.sessionId,
          walletAddress: this.walletAddress,
          expiresAt: result.expiration
        };
      } else {
        return {
          success: false,
          error: result.error || 'Connection failed'
        };
      }
    } catch (error) {
      console.error('Error connecting wallet:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Disconnect CDP wallet
   */
  async disconnectWallet() {
    try {
      const response = await fetch(`${this.apiEndpoint}/cdp/wallet/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': this.sessionId
        },
        body: JSON.stringify({})
      });
      
      const result = await response.json();
      
      // Clear local storage and reset properties
      localStorage.removeItem('cdp_session_id');
      localStorage.removeItem('cdp_wallet_address');
      this.walletAddress = null;
      this.walletConnected = false;
      this.paymentHeader = null;
      
      return { success: true };
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Sign a message using CDP wallet
   * @param {string} message - The message to sign
   */
  async signMessage(message) {
    if (!this.walletConnected) {
      throw new Error('Wallet not connected');
    }
    
    try {
      // This is where you would typically use a web3 provider or CDP SDK
      // For this example, we'll simulate it
      const mockSignature = await this._simulateMessageSigning(message, this.walletAddress);
      return {
        success: true,
        signature: mockSignature,
        message: message,
        walletAddress: this.walletAddress
      };
    } catch (error) {
      console.error('Error signing message:', error);
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Get payment requirements for accessing a resource
   * @param {string} resourceId - ID of the resource to access
   */
  async getPaymentRequirements(resourceId) {
    try {
      const response = await fetch(
        `${this.apiEndpoint}/x402/payment/requirements?resource_id=${resourceId}&session_id=${this.sessionId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'x-session-id': this.sessionId
          }
        }
      );
      
      // X402 protocol uses 402 status for Payment Required
      if (response.status === 402) {
        const result = await response.json();
        return {
          success: true,
          paymentRequired: true,
          requirements: result.requirements
        };
      } else {
        const result = await response.json();
        return {
          success: false,
          error: result.error || 'Failed to get payment requirements'
        };
      }
    } catch (error) {
      console.error('Error getting payment requirements:', error);
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Make X402 payment for a resource
   * @param {string} resourceId - ID of the resource to access
   * @param {string} amount - Payment amount
   * @param {string} currency - Currency code (default: ETH)
   */
  async makePayment(resourceId, amount, currency = 'ETH') {
    if (!this.walletConnected) {
      throw new Error('Wallet not connected');
    }
    
    try {
      const payload = {
        resource_id: resourceId,
        wallet_address: this.walletAddress,
        amount: amount,
        currency: currency
      };
      
      const response = await fetch(`${this.apiEndpoint}/x402/payment/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': this.sessionId
        },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Store payment header for future use
        this.paymentHeader = result.payment_header;
        return {
          success: true,
          transactionId: result.transaction_id,
          status: result.status,
          paymentHeader: this.paymentHeader
        };
      } else {
        return {
          success: false,
          error: result.error || 'Payment failed'
        };
      }
    } catch (error) {
      console.error('Error making payment:', error);
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Access a resource using the payment header
   * @param {string} resourceId - ID of the resource to access
   */
  async accessResource(resourceId) {
    if (!this.paymentHeader) {
      // Try to get payment requirements first
      const requirementsResult = await this.getPaymentRequirements(resourceId);
      if (requirementsResult.success && requirementsResult.paymentRequired) {
        return {
          success: false,
          paymentRequired: true,
          requirements: requirementsResult.requirements,
          error: 'Payment required before accessing this resource'
        };
      }
    }
    
    try {
      const response = await fetch(`${this.apiEndpoint}/x402/resource/${resourceId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': this.sessionId,
          'x-payment': this.paymentHeader
        }
      });
      
      // If payment is required and we don't have a valid payment header
      if (response.status === 402) {
        const result = await response.json();
        return {
          success: false,
          paymentRequired: true,
          requirements: result.requirements,
          error: 'Payment required'
        };
      }
      
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          resource: result.resource,
          paid: result.paid,
          transactionId: result.transaction_id
        };
      } else {
        return {
          success: false,
          error: result.error || 'Failed to access resource'
        };
      }
    } catch (error) {
      console.error('Error accessing resource:', error);
      return { success: false, error: error.message };
    }
  }
  
  // Helper methods
  
  /**
   * Simulate message signing (in a real app, you'd use web3.js or ethers.js)
   * @private
   */
  async _simulateMessageSigning(message, address) {
    return 'mock-signature-' + Math.random().toString(36).substring(2);
  }
}

// Example usage:
async function demonstrateWalletIntegration() {
  const apiEndpoint = 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod';
  const cdpWallet = new CDPWalletHandler(apiEndpoint);
  
  // Initialize and check existing connection
  await cdpWallet.initialize();
  
  // Connect wallet
  const walletAddress = '0x1234567890abcdef1234567890abcdef12345678';
  const connectionResult = await cdpWallet.connectWallet(walletAddress);
  console.log('Connection result:', connectionResult);
  
  // Check wallet status
  const statusResult = await cdpWallet.checkWalletStatus();
  console.log('Wallet status:', statusResult);
  
  // Get payment requirements for a resource
  const resourceId = 'premium-content-123';
  const requirementsResult = await cdpWallet.getPaymentRequirements(resourceId);
  console.log('Payment requirements:', requirementsResult);
  
  // Make payment
  const paymentAmount = '0.001'; // ETH
  const paymentResult = await cdpWallet.makePayment(resourceId, paymentAmount);
  console.log('Payment result:', paymentResult);
  
  // Access resource
  const accessResult = await cdpWallet.accessResource(resourceId);
  console.log('Resource access result:', accessResult);
  
  // Disconnect wallet
  const disconnectResult = await cdpWallet.disconnectWallet();
  console.log('Disconnect result:', disconnectResult);
}

// Expose handler for use in your application
window.CDPWalletHandler = CDPWalletHandler;
