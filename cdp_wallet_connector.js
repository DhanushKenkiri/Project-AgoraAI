// CDP Wallet Integration for NFT Payments
// This file provides a secure client-side interface for connecting to CDP wallets
// and processing payments through the X402 payment gateway

class CDPWalletConnector {
  constructor(apiEndpoint) {
    this.apiEndpoint = apiEndpoint;
    this.walletAddress = null;
    this.sessionToken = null;
    this.isConnected = false;
    this.sessionExpiration = null;
    
    // Security features
    this.nonceValue = this.generateNonce();
    this.transactionQueue = [];
    this.pendingTransactionHashes = new Set();
  }
  
  /**
   * Generates a cryptographically secure nonce for transaction security
   */
  generateNonce() {
    const array = new Uint32Array(4);
    window.crypto.getRandomValues(array);
    return Array.from(array, dec => ('0' + dec.toString(16)).substr(-2)).join('');
  }
  
  /**
   * Refreshes the security nonce
   */
  refreshNonce() {
    this.nonceValue = this.generateNonce();
    return this.nonceValue;
  }
  
  /**
   * Establishes connection with CDP wallet
   */
  async connectWallet() {
    try {
      if (!window.ethereum && !window.cdpWallet) {
        throw new Error("No compatible wallet found. Please install CDP Wallet extension.");
      }
      
      // Determine which wallet provider to use
      const provider = window.cdpWallet || window.ethereum;
      
      // Request wallet connection
      const accounts = await provider.request({ 
        method: 'eth_requestAccounts',
        params: [{
          securityToken: this.nonceValue
        }]
      });
      
      if (!accounts || accounts.length === 0) {
        throw new Error("No accounts found or user denied connection request");
      }
      
      this.walletAddress = accounts[0];
      
      // Register the wallet connection with the backend
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'connect_wallet',
          wallet_address: this.walletAddress,
          nonce: this.nonceValue,
          timestamp: Math.floor(Date.now() / 1000)
        })
      });
      
      if (!response.ok) {
        throw new Error("Failed to register wallet with backend");
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || "Failed to establish wallet session");
      }
      
      // Store session information
      this.sessionToken = result.session_token;
      this.isConnected = true;
      this.sessionExpiration = result.expiration * 1000; // Convert to milliseconds
      
      // Set a timer to warn about expiring session
      if (this.sessionExpiration) {
        const timeUntilExpiration = this.sessionExpiration - Date.now();
        if (timeUntilExpiration > 0) {
          setTimeout(() => {
            if (this.isConnected) {
              console.warn("Wallet session expiring soon. Please reconnect.");
              // Emit event for UI to notify user
              const event = new CustomEvent('walletSessionExpiring');
              document.dispatchEvent(event);
            }
          }, timeUntilExpiration - (5 * 60 * 1000)); // Warn 5 minutes before expiration
        }
      }
      
      // Emit connected event
      const event = new CustomEvent('walletConnected', { 
        detail: { 
          address: this.walletAddress,
          expiration: this.sessionExpiration
        } 
      });
      document.dispatchEvent(event);
      
      return {
        success: true,
        address: this.walletAddress
      };
    } catch (error) {
      console.error("Error connecting wallet:", error);
      
      // Emit error event
      const event = new CustomEvent('walletError', { 
        detail: { error: error.message } 
      });
      document.dispatchEvent(event);
      
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  /**
   * Disconnects the CDP wallet
   */
  disconnectWallet() {
    this.walletAddress = null;
    this.sessionToken = null;
    this.isConnected = false;
    this.sessionExpiration = null;
    this.refreshNonce();
    this.transactionQueue = [];
    
    // Emit disconnected event
    const event = new CustomEvent('walletDisconnected');
    document.dispatchEvent(event);
    
    return {
      success: true
    };
  }
  
  /**
   * Verifies if wallet is connected and session is valid
   */
  async verifyWalletConnection() {
    if (!this.isConnected || !this.walletAddress || !this.sessionToken) {
      return false;
    }
    
    // Check if session has expired
    if (this.sessionExpiration && Date.now() >= this.sessionExpiration) {
      this.disconnectWallet();
      return false;
    }
    
    return true;
  }
  
  /**
   * Initiates a payment for an NFT
   * @param {Object} paymentDetails - The payment details
   */
  async initiatePayment(paymentDetails) {
    try {
      // Verify wallet connection
      if (!await this.verifyWalletConnection()) {
        throw new Error("Wallet not connected. Please connect your wallet first.");
      }
      
      // Validate required payment parameters
      if (!paymentDetails.amount || !paymentDetails.nft_contract) {
        throw new Error("Missing required payment parameters");
      }
      
      // Add wallet address if not provided
      if (!paymentDetails.wallet_address) {
        paymentDetails.wallet_address = this.walletAddress;
      }
      
      // Submit payment initiation to backend
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.sessionToken}`
        },
        body: JSON.stringify({
          action: 'initiate_payment',
          wallet_address: this.walletAddress,
          amount: paymentDetails.amount,
          currency: paymentDetails.currency || 'ETH',
          nft_contract: paymentDetails.nft_contract,
          nft_token_id: paymentDetails.nft_token_id,
          nonce: this.nonceValue,
          timestamp: Math.floor(Date.now() / 1000)
        })
      });
      
      if (!response.ok) {
        throw new Error(`Payment initiation failed: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || "Failed to initiate payment");
      }
      
      // Store payment ID for future reference
      this.currentPaymentId = result.payment_id;
      
      // Refresh security nonce after each transaction
      this.refreshNonce();
      
      // Emit payment initiated event
      const event = new CustomEvent('paymentInitiated', { 
        detail: { 
          paymentId: result.payment_id,
          paymentUrl: result.payment_url,
          status: result.status
        } 
      });
      document.dispatchEvent(event);
      
      return result;
    } catch (error) {
      console.error("Error initiating payment:", error);
      
      // Emit payment error event
      const event = new CustomEvent('paymentError', { 
        detail: { error: error.message } 
      });
      document.dispatchEvent(event);
      
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  /**
   * Confirms a payment using a transaction hash
   * @param {String} paymentId - The payment ID
   * @param {String} transactionHash - The blockchain transaction hash
   */
  async confirmPayment(paymentId, transactionHash) {
    try {
      // Verify wallet connection
      if (!await this.verifyWalletConnection()) {
        throw new Error("Wallet not connected. Please connect your wallet first.");
      }
      
      // Validate parameters
      if (!paymentId || !transactionHash) {
        throw new Error("Payment ID and transaction hash are required");
      }
      
      // Prevent duplicate confirmations
      if (this.pendingTransactionHashes.has(transactionHash)) {
        throw new Error("This transaction is already being processed");
      }
      
      this.pendingTransactionHashes.add(transactionHash);
      
      // Submit payment confirmation to backend
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.sessionToken}`
        },
        body: JSON.stringify({
          action: 'confirm_payment',
          wallet_address: this.walletAddress,
          payment_id: paymentId,
          transaction_hash: transactionHash,
          nonce: this.nonceValue,
          timestamp: Math.floor(Date.now() / 1000)
        })
      });
      
      if (!response.ok) {
        this.pendingTransactionHashes.delete(transactionHash);
        throw new Error(`Payment confirmation failed: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Refresh nonce after transaction
      this.refreshNonce();
      
      if (!result.success) {
        this.pendingTransactionHashes.delete(transactionHash);
        throw new Error(result.error || "Failed to confirm payment");
      }
      
      // Clean up after successful confirmation
      this.pendingTransactionHashes.delete(transactionHash);
      
      // Emit payment confirmed event
      const event = new CustomEvent('paymentConfirmed', { 
        detail: { 
          paymentId: result.payment_id,
          transactionHash: result.transaction_hash,
          status: result.status
        } 
      });
      document.dispatchEvent(event);
      
      return result;
    } catch (error) {
      console.error("Error confirming payment:", error);
      
      // Emit payment error event
      const event = new CustomEvent('paymentError', { 
        detail: { error: error.message } 
      });
      document.dispatchEvent(event);
      
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  /**
   * Checks the status of a payment
   * @param {String} paymentId - The payment ID
   */
  async checkPaymentStatus(paymentId) {
    try {
      // Verify wallet connection
      if (!await this.verifyWalletConnection()) {
        throw new Error("Wallet not connected. Please connect your wallet first.");
      }
      
      // Validate parameters
      if (!paymentId) {
        throw new Error("Payment ID is required");
      }
      
      // Submit status request to backend
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.sessionToken}`
        },
        body: JSON.stringify({
          action: 'check_status',
          wallet_address: this.walletAddress,
          payment_id: paymentId,
          nonce: this.nonceValue,
          timestamp: Math.floor(Date.now() / 1000)
        })
      });
      
      if (!response.ok) {
        throw new Error(`Payment status check failed: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || "Failed to check payment status");
      }
      
      // Emit payment status event
      const event = new CustomEvent('paymentStatus', { 
        detail: { 
          paymentId: result.payment_id,
          status: result.status,
          transactionHash: result.transaction_hash,
          completedAt: result.completed_at
        } 
      });
      document.dispatchEvent(event);
      
      return result;
    } catch (error) {
      console.error("Error checking payment status:", error);
      
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Export the connector class
export default CDPWalletConnector;
