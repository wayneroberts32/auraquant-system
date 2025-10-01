/**
 * AuraQuant API Service Layer
 * Handles all communication with backend endpoints
 */

class ApiService {
    constructor() {
        // Use AuraQuant configuration for dynamic backend URL
        if (window.AuraQuantConfig) {
            this.baseUrl = window.AuraQuantConfig.getApiUrl();
        } else {
            // Fallback to direct Render URL if config not loaded
            this.baseUrl = window.location.hostname === 'localhost' 
                ? 'http://localhost:8000/api' 
                : 'https://auraquant-system.onrender.com/api';
        }
        
        this.token = localStorage.getItem('auraquant_token');
        this.userId = localStorage.getItem('auraquant_user_id');
        
        console.log('🧠 AuraQuant Brain API connected to:', this.baseUrl);
    }

    // =====================
    // Authentication
    // =====================
    
    async login(email, password, twoFactorCode = null) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, twoFactorCode })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.token = data.token;
                this.userId = data.userId;
                localStorage.setItem('auraquant_token', data.token);
                localStorage.setItem('auraquant_user_id', data.userId);
                localStorage.setItem('auraquant_user', JSON.stringify(data.user));
            }
            
            return data;
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    async logout() {
        localStorage.removeItem('auraquant_token');
        localStorage.removeItem('auraquant_user_id');
        localStorage.removeItem('auraquant_user');
        this.token = null;
        this.userId = null;
        return { success: true };
    }

    // =====================
    // Trading APIs
    // =====================
    
    async getMarketDepth(symbol) {
        return this.makeRequest(`/market-depth/${symbol}`);
    }

    async getScreenerData(filters = {}) {
        return this.makeRequest('/screener', 'POST', filters);
    }

    async placeManualTrade(tradeData) {
        return this.makeRequest('/manual-trade', 'POST', tradeData);
    }

    async getPaperTradingSession() {
        return this.makeRequest('/paper-trading/session');
    }

    async startPaperTrading() {
        return this.makeRequest('/paper-trading/start', 'POST');
    }

    async getBalance() {
        return this.makeRequest('/balance');
    }

    // =====================
    // AI & Automation
    // =====================
    
    async getAIWorkers() {
        return this.makeRequest('/ai-workers');
    }

    async toggleAIWorker(workerId) {
        return this.makeRequest(`/ai-workers/${workerId}/toggle`, 'POST');
    }

    async sendAIPrompt(workerId, prompt) {
        return this.makeRequest(`/ai-workers/${workerId}/prompt`, 'POST', { prompt });
    }

    async getBotStatus() {
        return this.makeRequest('/bot-status');
    }

    async getGrowthProfile() {
        return this.makeRequest('/growth-selector/profile');
    }

    async setGrowthProfile(profile) {
        return this.makeRequest('/growth-selector/profile', 'POST', profile);
    }

    // =====================
    // Portfolio & Analytics
    // =====================
    
    async getPortfolio() {
        return this.makeRequest('/portfolio');
    }

    async getPositions() {
        return this.makeRequest('/positions');
    }

    async getPnL(period = 'daily') {
        return this.makeRequest(`/pnl?period=${period}`);
    }

    async getPerformance(period = '1M') {
        return this.makeRequest(`/performance?period=${period}`);
    }

    async getHeatmaps(type = 'sectors') {
        return this.makeRequest(`/heatmaps/${type}`);
    }

    // =====================
    // Brokers & Banks
    // =====================
    
    async getBrokers() {
        return this.makeRequest('/brokers');
    }

    async connectBroker(brokerId, credentials) {
        return this.makeRequest(`/brokers/${brokerId}/connect`, 'POST', credentials);
    }

    async disconnectBroker(brokerId) {
        return this.makeRequest(`/brokers/${brokerId}/disconnect`, 'POST');
    }

    async getManualAPILoaders() {
        return this.makeRequest('/manual-api-loaders');
    }

    async addManualAPILoader(config) {
        return this.makeRequest('/manual-api-loaders', 'POST', config);
    }

    // =====================
    // Tools & Calculators
    // =====================
    
    async calculateTax(data) {
        return this.makeRequest('/tax-calculator', 'POST', data);
    }

    async getExchangeRates() {
        return this.makeRequest('/exchange-rates');
    }

    async getFees(broker = null) {
        const url = broker ? `/fees?broker=${broker}` : '/fees';
        return this.makeRequest(url);
    }

    async getLibraries(category = null) {
        const url = category ? `/libraries?category=${category}` : '/libraries';
        return this.makeRequest(url);
    }

    async getAllMarkets() {
        return this.makeRequest('/all-markets');
    }

    // =====================
    // Community & Help
    // =====================
    
    async getHelpArticles(query = null) {
        const url = query ? `/help-centre?q=${encodeURIComponent(query)}` : '/help-centre';
        return this.makeRequest(url);
    }

    async getCommunityStats() {
        return this.makeRequest('/community');
    }

    // =====================
    // Admin Functions
    // =====================
    
    async getDeploymentStatus() {
        return this.makeRequest('/deployment-verification');
    }

    async getGlobalView() {
        return this.makeRequest('/admin/global-view');
    }

    // =====================
    // Helper Methods
    // =====================
    
    async makeRequest(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        const options = {
            method,
            headers
        };
        
        if (body && method !== 'GET') {
            options.body = JSON.stringify(body);
        }
        
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    isAuthenticated() {
        return !!this.token;
    }

    getCurrentUser() {
        const userStr = localStorage.getItem('auraquant_user');
        return userStr ? JSON.parse(userStr) : null;
    }
}

// Create global instance
window.apiService = new ApiService();