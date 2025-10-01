/**
 * AuraQuant Dynamic Configuration
 * The Infinity Money Synthetic Intelligence System
 * Self-evolving orchestrator connecting Frontend → Brain (Render) → MongoDB
 */

window.AuraQuantConfig = {
    // Dynamic API URL based on environment
    getApiUrl() {
        // Check if running on Cloudflare Pages
        if (window.location.hostname.includes('ai-auraquant.com') || 
            window.location.hostname.includes('pages.dev')) {
            return 'https://auraquant-system.onrender.com/api';
        }
        // Local development
        if (window.location.hostname === 'localhost' || 
            window.location.hostname === '127.0.0.1') {
            return 'http://localhost:8000/api';
        }
        // Default to production
        return 'https://auraquant-system.onrender.com/api';
    },

    // WebSocket URL for real-time data
    getWsUrl() {
        const apiUrl = this.getApiUrl();
        if (apiUrl.includes('onrender.com')) {
            return 'wss://auraquant-system.onrender.com/ws';
        }
        return 'ws://localhost:8000/ws';
    },

    // Get base URL without /api
    getBaseUrl() {
        const apiUrl = this.getApiUrl();
        return apiUrl.replace('/api', '');
    },

    // Trading configuration
    TRADING_MODE: 'PAPER',
    PAPER_BALANCE: 500,
    CURRENCY: 'AUD',
    MIN_BALANCE: 500,

    // System identity
    SYSTEM_NAME: 'AuraQuant Synthetic Intelligence',
    SYSTEM_VERSION: '1.0.0',
    SYSTEM_TAGLINE: 'The Infinity Money Orchestrator',

    // Feature flags
    ENABLE_PAPER_TRADING: true,
    ENABLE_LIVE_TRADING: false,
    ENABLE_AI_WORKERS: true,
    ENABLE_QUANTUM_BRAIN: true,

    // Authentication roles
    ROLES: {
        ADMIN: 'admin',
        TRADER: 'trader',
        VIEWER: 'viewer'
    },

    // Check if user is admin
    isAdmin() {
        const user = JSON.parse(localStorage.getItem('auraquant_user') || '{}');
        return user.role === this.ROLES.ADMIN;
    },

    // Check if user is authenticated
    isAuthenticated() {
        return !!localStorage.getItem('auraquant_token');
    },

    // Get current user
    getCurrentUser() {
        return JSON.parse(localStorage.getItem('auraquant_user') || '{}');
    },

    // Initialize system
    async init() {
        console.log('🚀 Initializing AuraQuant Synthetic Intelligence System');
        console.log(`📡 Brain (Render): ${this.getApiUrl()}`);
        console.log(`🔌 WebSocket: ${this.getWsUrl()}`);
        console.log(`💼 Trading Mode: ${this.TRADING_MODE}`);
        console.log(`💰 Paper Balance: ${this.CURRENCY} ${this.PAPER_BALANCE}`);
        
        // Test backend connection
        try {
            const response = await fetch(this.getBaseUrl() + '/health');
            if (response.ok) {
                const health = await response.json();
                console.log('✅ Brain connection successful:', health);
                return true;
            }
        } catch (error) {
            console.error('❌ Brain connection failed:', error);
            return false;
        }
    }
};

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.AuraQuantConfig.init();
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.AuraQuantConfig;
}