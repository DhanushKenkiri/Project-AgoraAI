// NFT Payment Frontend Implementation
// This file provides code examples for integrating with the NFT Payment Lambda backend

/**
 * NFT Payment Frontend Integration
 * Features:
 * - User authentication
 * - NFT collection search
 * - X402 payment processing
 * - CDP Wallet integration
 */

class NFTPaymentUIHandler {
  constructor(apiEndpoint) {
    this.apiEndpoint = apiEndpoint;
    this.userToken = null;
    this.walletConnector = new CDPWalletConnector(apiEndpoint);
    this.isAuthenticated = false;
  }

  /**
   * Initialize the UI components
   */
  async initialize() {
    // Set up event listeners for UI elements
    this.setupEventListeners();
    
    // Check for existing session
    await this.checkExistingSession();
    
    console.log('NFT Payment UI initialized');
  }
  
  /**
   * Set up event listeners for UI components
   */
  setupEventListeners() {
    // Login button
    document.getElementById('login-button')?.addEventListener('click', () => this.handleLogin());
    
    // Connect wallet button
    document.getElementById('connect-wallet-button')?.addEventListener('click', () => this.connectWallet());
    
    // NFT search button
    document.getElementById('nft-search-button')?.addEventListener('click', () => this.searchNFT());
    
    // Payment button
    document.getElementById('pay-button')?.addEventListener('click', () => this.initiatePayment());
  }
  
  /**
   * Check if user has an existing session
   */
  async checkExistingSession() {
    const token = localStorage.getItem('nftPaymentUserToken');
    if (token) {
      try {
        // Validate token with backend
        const response = await fetch(`${this.apiEndpoint}/auth/validate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          this.userToken = token;
          this.isAuthenticated = true;
          this.updateUI('authenticated');
          return true;
        }
      } catch (error) {
        console.error('Error validating session:', error);
      }
      
      // Clear invalid token
      localStorage.removeItem('nftPaymentUserToken');
    }
    
    this.updateUI('unauthenticated');
    return false;
  }
  
  /**
   * Handle user login
   */
  async handleLogin() {
    // Get login credentials from form
    const email = document.getElementById('email-input')?.value;
    const password = document.getElementById('password-input')?.value;
    
    if (!email || !password) {
      this.showNotification('Please provide email and password', 'error');
      return;
    }
    
    try {
      // Call login endpoint
      const response = await fetch(`${this.apiEndpoint}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        this.userToken = data.token;
        
        // Store token in local storage
        localStorage.setItem('nftPaymentUserToken', this.userToken);
        
        this.isAuthenticated = true;
        this.updateUI('authenticated');
        this.showNotification('Login successful', 'success');
      } else {
        this.showNotification('Login failed. Please check your credentials.', 'error');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showNotification('An error occurred during login', 'error');
    }
  }
  
  /**
   * Connect to CDP Wallet
   */
  async connectWallet() {
    try {
      await this.walletConnector.connectWallet();
      
      if (this.walletConnector.isConnected) {
        // Register wallet with backend
        await this.registerWalletWithBackend();
        
        this.updateUI('wallet-connected');
        this.showNotification('Wallet connected successfully', 'success');
      }
    } catch (error) {
      console.error('Wallet connection error:', error);
      this.showNotification(error.message || 'Failed to connect wallet', 'error');
    }
  }
  
  /**
   * Register connected wallet with backend
   */
  async registerWalletWithBackend() {
    if (!this.isAuthenticated || !this.walletConnector.isConnected) {
      return false;
    }
    
    try {
      const response = await fetch(`${this.apiEndpoint}/wallet/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          wallet_address: this.walletConnector.walletAddress,
          session_id: this.walletConnector.sessionToken,
          cdp_token: this.walletConnector.cdpToken
        })
      });
      
      return response.ok;
    } catch (error) {
      console.error('Error registering wallet:', error);
      return false;
    }
  }
  
  /**
   * Search for NFT collection data
   */
  async searchNFT() {
    const collection = document.getElementById('collection-input')?.value;
    const chain = document.getElementById('chain-input')?.value || 'ethereum';
    
    if (!collection) {
      this.showNotification('Please enter a collection name', 'error');
      return;
    }
    
    try {
      // Important: Include contractAddress in the request
      // This can be the collection's contract address
      const contractAddress = document.getElementById('contract-input')?.value;
      
      if (!contractAddress) {
        this.showNotification('Contract address is required', 'error');
        return;
      }
      
      this.showNotification('Searching for collection data...', 'info');
      
      const response = await fetch(`${this.apiEndpoint}/nft/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          collection,
          chain,
          contractAddress // Include contract address here
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        this.displayNFTData(data);
        this.showNotification('Collection data retrieved', 'success');
      } else {
        this.showNotification('Failed to retrieve collection data', 'error');
      }
    } catch (error) {
      console.error('NFT search error:', error);
      this.showNotification('An error occurred during NFT search', 'error');
    }
  }
  
  /**
   * Display NFT data in the UI
   */
  displayNFTData(data) {
    const resultsContainer = document.getElementById('nft-results');
    if (!resultsContainer) return;
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Create collection info section
    const collectionInfo = document.createElement('div');
    collectionInfo.className = 'collection-info';
    
    if (data.nft_data && data.nft_data.collection) {
      const collection = data.nft_data.collection;
      
      collectionInfo.innerHTML = `
        <h2>${collection.name || 'Unknown Collection'}</h2>
        ${collection.image ? `<img src="${collection.image}" alt="${collection.name}" class="collection-image">` : ''}
        <div class="collection-stats">
          <p><strong>Floor Price:</strong> ${collection.floorAsk?.price?.amount?.native || 'Unknown'} ${collection.floorAsk?.price?.currency?.symbol || 'ETH'}</p>
          <p><strong>Items:</strong> ${collection.tokenCount || 'Unknown'}</p>
        </div>
      `;
      
      // Add "Pay for Analysis" button
      const payButton = document.createElement('button');
      payButton.id = 'pay-for-analysis';
      payButton.className = 'primary-button';
      payButton.innerText = 'Pay for Detailed Analysis';
      payButton.onclick = () => this.initiatePayment(collection);
      
      collectionInfo.appendChild(payButton);
    } else {
      collectionInfo.innerHTML = '<p>No collection data found</p>';
    }
    
    resultsContainer.appendChild(collectionInfo);
  }
  
  /**
   * Initiate payment for NFT analysis
   */
  async initiatePayment(collectionData) {
    if (!this.isAuthenticated || !this.walletConnector.isConnected) {
      this.showNotification('Please login and connect your wallet first', 'error');
      return;
    }
    
    try {
      // Get the X402 token contract address from your config
      const tokenContractAddress = this.getTokenContractAddress();
      
      if (!tokenContractAddress) {
        this.showNotification('Token contract address is not configured', 'error');
        return;
      }
      
      this.showNotification('Initiating payment...', 'info');
      
      const response = await fetch(`${this.apiEndpoint}/payment/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          amount: "0.005", // Or dynamically calculated amount
          currency: "ETH",
          paymentReason: "NFT analysis",
          contractAddress: collectionData?.id, // Include the collection contract address
          x402: {
            payment_type: "x402",
            wallet_address: this.walletConnector.walletAddress,
            redirect_url: window.location.origin + "/payment-success",
            contract_address: tokenContractAddress // X402 token contract address
          }
        })
      });
      
      if (response.ok) {
        const paymentData = await response.json();
        await this.processPayment(paymentData);
      } else {
        const errorData = await response.json();
        this.showNotification(`Payment initiation failed: ${errorData.error || 'Unknown error'}`, 'error');
      }
    } catch (error) {
      console.error('Payment initiation error:', error);
      this.showNotification('An error occurred during payment initiation', 'error');
    }
  }
  
  /**
   * Get the X402 token contract address from configuration
   */
  getTokenContractAddress() {
    // This could be loaded from your app's configuration
    // For this example, we'll return a placeholder
    return "0x123456789abcdef123456789abcdef123456789a"; // Replace with actual contract address
  }
  
  /**
   * Process the payment using CDP Wallet and X402 protocol
   */
  async processPayment(paymentData) {
    try {
      // Process the payment using CDP wallet
      const paymentResult = await this.walletConnector.sendPayment(
        paymentData.x402PaymentDetails
      );
      
      if (paymentResult.success) {
        // Register the transaction with the backend
        await this.registerTransaction(paymentResult.transactionHash);
        
        this.showNotification('Payment successful!', 'success');
        
        // Fetch the premium NFT analysis that was paid for
        await this.fetchPremiumAnalysis(paymentResult.transactionHash);
      } else {
        this.showNotification('Payment failed: ' + paymentResult.error, 'error');
      }
    } catch (error) {
      console.error('Payment processing error:', error);
      this.showNotification('An error occurred during payment processing', 'error');
    }
  }
  
  /**
   * Register successful transaction with backend
   */
  async registerTransaction(transactionHash) {
    try {
      await fetch(`${this.apiEndpoint}/transaction/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          transaction_hash: transactionHash,
          payment_type: 'x402'
        })
      });
    } catch (error) {
      console.error('Error registering transaction:', error);
    }
  }
  
  /**
   * Fetch premium NFT analysis after payment
   */
  async fetchPremiumAnalysis(transactionHash) {
    try {
      const response = await fetch(`${this.apiEndpoint}/nft/premium-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          transaction_hash: transactionHash
        })
      });
      
      if (response.ok) {
        const analysisData = await response.json();
        this.displayPremiumAnalysis(analysisData);
      }
    } catch (error) {
      console.error('Error fetching premium analysis:', error);
    }
  }
  
  /**
   * Display premium NFT analysis in the UI
   */
  displayPremiumAnalysis(data) {
    const premiumContainer = document.getElementById('premium-analysis');
    if (!premiumContainer) return;
    
    premiumContainer.innerHTML = `
      <h2>Premium NFT Analysis</h2>
      <div class="premium-content">
        ${data.analysis_html || '<p>Analysis data not available</p>'}
      </div>
    `;
    
    // Show the premium container
    premiumContainer.style.display = 'block';
    
    // Scroll to premium analysis
    premiumContainer.scrollIntoView({ behavior: 'smooth' });
  }
  
  /**
   * Update UI based on authentication state
   */
  updateUI(state) {
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const walletSection = document.getElementById('wallet-section');
    
    if (state === 'authenticated') {
      loginSection.style.display = 'none';
      dashboardSection.style.display = 'block';
      walletSection.style.display = 'block';
    } else if (state === 'wallet-connected') {
      document.getElementById('wallet-status').innerText = 
        `Connected: ${this.walletConnector.walletAddress.substring(0, 6)}...${this.walletConnector.walletAddress.substring(38)}`;
    } else {
      loginSection.style.display = 'block';
      dashboardSection.style.display = 'none';
    }
  }
  
  /**
   * Show a notification to the user
   */
  showNotification(message, type) {
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) return;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerText = message;
    
    notificationContainer.appendChild(notification);
    
    // Remove notification after 5 seconds
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => {
        notificationContainer.removeChild(notification);
      }, 500);
    }, 5000);
  }
}

// Example usage
document.addEventListener('DOMContentLoaded', async () => {
  const apiEndpoint = 'https://your-api-gateway-url.execute-api.region.amazonaws.com/prod';
  const paymentUI = new NFTPaymentUIHandler(apiEndpoint);
  await paymentUI.initialize();
});
