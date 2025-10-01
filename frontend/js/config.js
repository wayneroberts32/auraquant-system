/**
 * AuraQuant Dynamic Configuration
 * Automatically switches between local and production APIs
 */

// Get environment from Cloudflare Pages or default to local
const getApiUrl = () => {
    // Check if API_URL is set in environment (Cloudflare Pages)
    if (typeof API_URL !== 'undefined' && API_URL) {
        return API_URL;
    }
    
    // Check URL parameters for override
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('api')) {
        return urlParams.get('api');
    }
    
    // Check localStorage for saved API URL
    const savedApi = localStorage.getItem('auraquant_api_url');
    if (savedApi) {
        return savedApi;
    }
    
    // Default to localhost for development
    return 'http://localhost:8000';
};

const getWsUrl = () => {
    // Check if WS_URL is set in environment
    if (typeof WS_URL !== 'undefined' && WS_URL) {
        return WS_URL;
    }
    
    // Derive from API URL
    const apiUrl = getApiUrl();
    if (apiUrl.startsWith('https://')) {
        return apiUrl.replace('https://', 'wss://');
    } else if (apiUrl.startsWith('http://')) {
        return apiUrl.replace('http://', 'ws://');
    }
    
    return 'ws://localhost:8000';
};

// Configuration object
window.AuraQuantConfig = {
    API_URL: getApiUrl(),
    WS_URL: getWsUrl(),
    
    // Trading configuration
    PAPER_BALANCE: typeof PAPER_BALANCE !== 'undefined' ? PAPER_BALANCE : 500,
    CURRENCY: typeof CURRENCY !== 'undefined' ? CURRENCY : 'AUD',
    ENABLE_LIVE_TRADING: typeof ENABLE_LIVE_TRADING !== 'undefined' ? ENABLE_LIVE_TRADING : false,
    ENABLE_PAPER_TRADING: typeof ENABLE_PAPER_TRADING !== 'undefined' ? ENABLE_PAPER_TRADING : true,
    
    // System configuration
    TRADING_MODE: typeof TRADING_MODE !== 'undefined' ? TRADING_MODE : 'FULL_SYSTEM',
    NODE_ENV: typeof NODE_ENV !== 'undefined' ? NODE_ENV : 'development',
    
    // Helper functions
    isProduction() {
        return this.NODE_ENV === 'production';
    },
    
    isPaperTrading() {
        return this.ENABLE_PAPER_TRADING && !this.ENABLE_LIVE_TRADING;
    },
    
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-Trading-Mode': this.isPaperTrading() ? 'paper' : 'live'
        };
    },
    
    // Update API URL dynamically
    setApiUrl(url) {
        this.API_URL = url;
        localStorage.setItem('auraquant_api_url', url);
        console.log(`✅ API URL updated to: ${url}`);
    },
    
    // Test connection
    async testConnection() {
        try {
            const response = await fetch(`${this.API_URL}/health`);
            if (response.ok) {
                console.log('✅ Backend connection successful');
                return true;
            }
        } catch (error) {
            console.error('❌ Backend connection failed:', error);
        }
        return false;
    }
};

// Log configuration on load
console.log('🚀 AuraQuant Configuration Loaded:');
console.log(`   API URL: ${window.AuraQuantConfig.API_URL}`);
console.log(`   WS URL: ${window.AuraQuantConfig.WS_URL}`);
console.log(`   Mode: ${window.AuraQuantConfig.isPaperTrading() ? 'Paper Trading' : 'Live Trading'}`);
console.log(`   Balance: $${window.AuraQuantConfig.PAPER_BALANCE} ${window.AuraQuantConfig.CURRENCY}`);

// Auto-test connection on load
window.AuraQuantConfig.testConnection();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.AuraQuantConfig;
}