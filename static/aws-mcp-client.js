/**
 * AWS NFT Payment MCP Client
 * 
 * This script helps to integrate the AWS MCP server with frontend applications.
 * It provides utility functions for wallet login, payment popups, and interacting with the MCP API.
 */

class AWSMCPClient {
    /**
     * Initialize the AWS MCP client
     * 
     * @param {string} serverUrl - The base URL of the MCP server
     */
    constructor(serverUrl) {
        this.serverUrl = serverUrl || (window.location.hostname === 'localhost' ? 
            'http://localhost:8000' : `https://${window.location.hostname}`);
        this.sessionData = null;
        
        // Check if we're running in AWS
        this.isAWS = serverUrl && serverUrl.includes('amazonaws.com');
    }
    
    /**
     * Open a wallet connection popup
     * 
     * @param {Object} options - Options for the wallet popup
     * @param {string} options.redirectUrl - URL to redirect after successful connection
     * @param {string} options.callbackUrl - URL to call with result
     * @param {string} options.cancelUrl - URL to redirect if cancelled
     * @returns {Promise<Object>} - Wallet connection result
     */
    async openWalletPopup(options = {}) {
        try {
            const response = await fetch(`${this.serverUrl}/mcp/popup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    function_name: 'wallet_popup',
                    parameters: {
                        redirect_url: options.redirectUrl || '',
                        callback_url: options.callbackUrl || '',
                        cancel_url: options.cancelUrl || ''
                    }
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to create wallet popup');
            }
            
            // Store session ID
            this.sessionData = {
                sessionId: data.session_id,
                popupType: 'wallet'
            };
            
            // Open popup
            const popup = window.open(data.url, 'WalletConnection', 'width=500,height=600');
            
            if (!popup) {
                throw new Error('Popup blocked. Please allow popups for this site.');
            }
            
            // Return promise that resolves when wallet is connected
            return new Promise((resolve, reject) => {
                // Poll for wallet connection
                const checkInterval = setInterval(async () => {
                    try {
                        const statusResponse = await fetch(`${this.serverUrl}/ui/wallet/status?session_id=${data.session_id}`);
                        const statusData = await statusResponse.json();
                        
                        if (statusData.success && statusData.status === 'connected') {
                            clearInterval(checkInterval);
                            popup.close();
                            resolve({
                                success: true,
                                wallet_address: statusData.wallet_address,
                                wallet_type: statusData.wallet_type
                            });
                        }
                    } catch (e) {
                        console.error('Error checking wallet status:', e);
                    }
                }, 1000);
                
                // Handle popup closing
                const popupCheckInterval = setInterval(() => {
                    if (popup.closed) {
                        clearInterval(popupCheckInterval);
                        clearInterval(checkInterval);
                        reject(new Error('Wallet connection cancelled'));
                    }
                }, 500);
            });
        } catch (error) {
            console.error('Error opening wallet popup:', error);
            throw error;
        }
    }
    
    /**
     * Open a payment popup
     * 
     * @param {Object} options - Payment options
     * @param {string} options.amount - Payment amount
     * @param {string} options.currency - Payment currency
     * @param {string} options.paymentReason - Reason for payment
     * @param {string} options.redirectUrl - URL to redirect after payment
     * @param {string} options.callbackUrl - URL to call with payment result
     * @param {string} options.cancelUrl - URL to redirect if payment cancelled
     * @returns {Promise<Object>} - Payment result
     */
    async openPaymentPopup(options = {}) {
        try {
            const response = await fetch(`${this.serverUrl}/mcp/popup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    function_name: 'payment_popup',
                    parameters: {
                        amount: options.amount || '0.01',
                        currency: options.currency || 'ETH',
                        payment_reason: options.paymentReason || 'NFT Payment',
                        redirect_url: options.redirectUrl || '',
                        callback_url: options.callbackUrl || '',
                        cancel_url: options.cancelUrl || ''
                    }
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to create payment popup');
            }
            
            // Open popup
            const popup = window.open(data.url, 'NFTPayment', 'width=500,height=700');
            
            if (!popup) {
                throw new Error('Popup blocked. Please allow popups for this site.');
            }
            
            // Return promise that resolves when payment is completed
            return new Promise((resolve, reject) => {
                // Listen for message from popup
                window.addEventListener('message', function messageHandler(event) {
                    // Check if message is from our popup
                    if (event.data && event.data.type === 'payment_completed') {
                        window.removeEventListener('message', messageHandler);
                        resolve(event.data);
                    }
                });
                
                // Handle popup closing
                const popupCheckInterval = setInterval(() => {
                    if (popup.closed) {
                        clearInterval(popupCheckInterval);
                        reject(new Error('Payment cancelled'));
                    }
                }, 500);
            });
        } catch (error) {
            console.error('Error opening payment popup:', error);
            throw error;
        }
    }
    
    /**
     * Call an MCP function directly
     * 
     * @param {string} functionName - Name of the function to call
     * @param {Object} parameters - Function parameters
     * @returns {Promise<Object>} - Function result
     */
    async callMCPFunction(functionName, parameters = {}) {
        try {
            const response = await fetch(`${this.serverUrl}/mcp/call`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    function_name: functionName,
                    parameters
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error(`Error calling MCP function ${functionName}:`, error);
            throw error;
        }
    }
    
    /**
     * Get wallet information
     * 
     * @param {string} walletAddress - Wallet address
     * @returns {Promise<Object>} - Wallet info
     */
    async getWalletInfo(walletAddress) {
        return this.callMCPFunction('get_wallet_info', { wallet_address: walletAddress });
    }
    
    /**
     * Get wallet NFTs
     * 
     * @param {string} walletAddress - Wallet address
     * @returns {Promise<Object>} - Wallet NFTs
     */
    async getWalletNFTs(walletAddress) {
        return this.callMCPFunction('get_wallet_nfts', { wallet_address: walletAddress });
    }
    
    /**
     * Process a payment directly (without popup)
     * 
     * @param {Object} payment - Payment details
     * @returns {Promise<Object>} - Payment result
     */
    async processPayment(payment) {
        return this.callMCPFunction('process_payment', {
            amount: payment.amount,
            currency: payment.currency || 'ETH',
            payment_reason: payment.paymentReason,
            wallet_address: payment.walletAddress,
            contract_address: payment.contractAddress
        });
    }
}

// Check if we're in a browser environment and export
if (typeof window !== 'undefined') {
    window.AWSMCPClient = AWSMCPClient;
}

// Check if we're in Node.js and export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AWSMCPClient };
}
