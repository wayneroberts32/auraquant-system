/**
 * AuraQuant Main Application Controller
 * Single-tab navigation with workspace management
 */

class AuraQuantApp {
    constructor() {
        this.currentView = 'dashboard';
        this.currentUser = null;
        this.isAuthenticated = false;
        this.contentCache = new Map();
        
        this.init();
    }

    async init() {
        // Setup event listeners
        this.setupEventListeners();
        
        // Check authentication status
        this.checkAuthentication();
        
        // Initialize WebSocket connection
        window.wsService.connect();
        
        // Setup WebSocket subscriptions
        this.setupWebSocketSubscriptions();
        
        // Load initial view or show login
        if (!this.isAuthenticated) {
            this.showLoginModal();
        } else {
            this.loadView('dashboard');
        }
    }

    setupEventListeners() {
        // Login form handler
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
        
        // Navigation links
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = link.getAttribute('href').substring(1);
                this.loadView(view);
            });
        });
        
        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.view) {
                this.loadView(e.state.view, false);
            }
        });
        
        // ESC key to go back
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                window.history.back();
            }
        });
    }

    setupWebSocketSubscriptions() {
        // Subscribe to ticker tape
        window.wsService.subscribeToTickerTape((data) => {
            this.updateTickerTape(data);
        });
        
        // Subscribe to alerts
        window.wsService.subscribeToAlerts((alert) => {
            this.showNotification(alert);
        });
    }

    checkAuthentication() {
        const token = localStorage.getItem('auraquant_token');
        const user = window.apiService.getCurrentUser();
        
        if (token && user) {
            this.isAuthenticated = true;
            this.currentUser = user;
            this.updateUserInterface();
            
            // Show admin section if user is admin
            if (user.role === 'admin') {
                document.getElementById('admin-section').style.display = 'block';
            }
        }
    }

    showLoginModal() {
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const twoFA = document.getElementById('2fa').value;
        
        try {
            const result = await window.apiService.login(email, password, twoFA || null);
            
            if (result.success) {
                this.isAuthenticated = true;
                this.currentUser = result.user;
                
                // Hide login modal
                const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
                loginModal.hide();
                
                // Update UI
                this.updateUserInterface();
                
                // Connect WebSocket with auth
                window.wsService.authenticate(result.token);
                
                // Load dashboard
                this.loadView('dashboard');
                
                // Show success message
                this.showNotification({
                    type: 'success',
                    message: `Welcome back, ${result.user.name}!`
                });
            } else {
                this.showNotification({
                    type: 'error',
                    message: result.error || 'Login failed'
                });
            }
        } catch (error) {
            this.showNotification({
                type: 'error',
                message: 'Network error. Please try again.'
            });
        }
    }

    async handleLogout() {
        await window.apiService.logout();
        this.isAuthenticated = false;
        this.currentUser = null;
        
        // Disconnect WebSocket
        window.wsService.disconnect();
        
        // Clear UI
        document.getElementById('main-content').innerHTML = '';
        document.getElementById('current-user').textContent = 'Guest';
        document.getElementById('admin-section').style.display = 'none';
        
        // Show login modal
        this.showLoginModal();
    }

    updateUserInterface() {
        if (this.currentUser) {
            document.getElementById('current-user').textContent = this.currentUser.name;
            
            if (this.currentUser.role === 'admin') {
                document.getElementById('admin-section').style.display = 'block';
            }
        }
    }

    async loadView(view, pushState = true) {
        // Update navigation state
        this.currentView = view;
        
        // Update active nav item
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${view}`) {
                link.classList.add('active');
            }
        });
        
        // Update browser history
        if (pushState) {
            window.history.pushState({ view }, '', `#${view}`);
        }
        
        // Load view content
        const content = await this.getViewContent(view);
        document.getElementById('main-content').innerHTML = content;
        
        // Initialize view-specific functionality
        this.initializeView(view);
    }

    async getViewContent(view) {
        // Check cache first
        if (this.contentCache.has(view)) {
            return this.contentCache.get(view);
        }
        
        // Map views to their HTML files
        const viewMap = {
            'dashboard': 'main-trading-dashboard.html',
            'market-depth': 'market-depth-demo.html',
            'screener': 'market-depth-demo.html',
            'manual-trade': 'manual-trade.html',
            'paper-trading': 'asx-paper-trading-launcher.html',
            'ai-workers': 'ai-workers-panel.html',
            'bot-status': 'bot-status.html',
            'growth-selector': 'growth-selector.html',
            'portfolio': 'portfolio.html',
            'pnl': 'pnl-dashboard.html',
            'performance': 'performance-monitor.html',
            'heatmaps': 'heatmaps.html',
            'brokers': 'brokers-banks.html',
            'tax-calculator': 'tax-calculator.html',
            'fees': 'fees-display.html',
            'libraries': 'libraries.html',
            'community': 'community.html',
            'help': 'help-centre.html',
            'deployment': 'deployment-verification.html',
            'global-view': 'unified-dashboard.html'
        };
        
        const htmlFile = viewMap[view] || 'main-trading-dashboard.html';
        
        // Try to load from pages folder
        try {
            const response = await fetch(`pages/${htmlFile}`);
            if (response.ok) {
                const html = await response.text();
                // Extract body content only
                const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
                const content = bodyMatch ? bodyMatch[1] : html;
                
                // Cache the content
                this.contentCache.set(view, content);
                return content;
            }
        } catch (error) {
            console.error(`Failed to load view: ${view}`, error);
        }
        
        // Return default content if file not found
        return this.getDefaultContent(view);
    }

    getDefaultContent(view) {
        const contents = {
            'dashboard': `
                <div class="container-fluid">
                    <h2 class="mb-4">Trading Dashboard</h2>
                    
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card bg-dark text-white">
                                <div class="card-body">
                                    <h5 class="card-title">Portfolio Value</h5>
                                    <h3 id="portfolio-value">$0.00</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-dark text-white">
                                <div class="card-body">
                                    <h5 class="card-title">Daily P&L</h5>
                                    <h3 id="daily-pnl" class="text-success">$0.00</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-dark text-white">
                                <div class="card-body">
                                    <h5 class="card-title">Open Positions</h5>
                                    <h3 id="open-positions">0</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-dark text-white">
                                <div class="card-body">
                                    <h5 class="card-title">Active Bots</h5>
                                    <h3 id="active-bots">0</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Price Chart</h5>
                                </div>
                                <div class="card-body">
                                    <div id="trading-chart" style="height: 400px;">
                                        <!-- TradingView widget would go here -->
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Positions</h5>
                                </div>
                                <div class="card-body">
                                    <div id="positions-list">
                                        <p class="text-muted">No open positions</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            'brokers': `
                <div class="container-fluid">
                    <h2 class="mb-4">Brokers & Banks</h2>
                    <div class="row" id="brokers-list">
                        <div class="col-md-4 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Interactive Brokers</h5>
                                    <p class="card-text">Full-service broker with global market access</p>
                                    <button class="btn btn-primary connect-broker" data-broker="ibkr">Connect</button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Binance</h5>
                                    <p class="card-text">Leading cryptocurrency exchange</p>
                                    <button class="btn btn-primary connect-broker" data-broker="binance">Connect</button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">ASX Paper Trading</h5>
                                    <p class="card-text">Practice trading without risk</p>
                                    <button class="btn btn-success connect-broker" data-broker="asx-paper">Start</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            'manual-trade': `
                <div class="container-fluid">
                    <h2 class="mb-4">Manual Trade Entry</h2>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <form id="manual-trade-form">
                                        <div class="mb-3">
                                            <label class="form-label">Symbol</label>
                                            <input type="text" class="form-control" id="trade-symbol" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Side</label>
                                            <select class="form-control" id="trade-side">
                                                <option value="buy">Buy</option>
                                                <option value="sell">Sell</option>
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Quantity</label>
                                            <input type="number" class="form-control" id="trade-quantity" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Order Type</label>
                                            <select class="form-control" id="trade-order-type">
                                                <option value="market">Market</option>
                                                <option value="limit">Limit</option>
                                                <option value="stop">Stop</option>
                                            </select>
                                        </div>
                                        <div class="mb-3" id="price-input" style="display: none;">
                                            <label class="form-label">Price</label>
                                            <input type="number" class="form-control" id="trade-price" step="0.01">
                                        </div>
                                        <button type="submit" class="btn btn-primary w-100">Place Order</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>AI Trade Assistant</h5>
                                </div>
                                <div class="card-body">
                                    <div id="ai-suggestions">
                                        <p class="text-muted">Enter trade details to get AI suggestions</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        };
        
        return contents[view] || `
            <div class="container-fluid">
                <h2 class="mb-4">${view.charAt(0).toUpperCase() + view.slice(1).replace(/-/g, ' ')}</h2>
                <div class="alert alert-info">
                    This panel is being loaded. Please wait...
                </div>
            </div>
        `;
    }

    async initializeView(view) {
        // Initialize view-specific functionality
        switch(view) {
            case 'dashboard':
                await this.initializeDashboard();
                break;
            case 'market-depth':
                await this.initializeMarketDepth();
                break;
            case 'ai-workers':
                await this.initializeAIWorkers();
                break;
            case 'bot-status':
                await this.initializeBotStatus();
                break;
            case 'portfolio':
                await this.initializePortfolio();
                break;
            case 'brokers':
                await this.initializeBrokers();
                break;
            case 'manual-trade':
                this.initializeManualTrade();
                break;
            case 'help':
                await this.initializeHelpCentre();
                break;
        }
    }

    async initializeDashboard() {
        try {
            const [portfolio, positions, botStatus] = await Promise.all([
                window.apiService.getPortfolio(),
                window.apiService.getPositions(),
                window.apiService.getBotStatus()
            ]);
            
            // Update dashboard values
            if (document.getElementById('portfolio-value')) {
                document.getElementById('portfolio-value').textContent = 
                    `$${(portfolio.totalValue || 0).toFixed(2)}`;
            }
            if (document.getElementById('daily-pnl')) {
                const pnl = portfolio.dailyPnL || 0;
                const pnlElement = document.getElementById('daily-pnl');
                pnlElement.textContent = `$${Math.abs(pnl).toFixed(2)}`;
                pnlElement.className = pnl >= 0 ? 'text-success' : 'text-danger';
            }
            if (document.getElementById('open-positions')) {
                document.getElementById('open-positions').textContent = positions.length || 0;
            }
            if (document.getElementById('active-bots')) {
                const activeBots = botStatus.filter(b => b.status === 'running').length;
                document.getElementById('active-bots').textContent = activeBots;
            }
            
            // Subscribe to real-time updates
            window.wsService.subscribeToPositions((data) => {
                this.updatePositions(data);
            });
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
        }
    }

    async initializeMarketDepth() {
        // Subscribe to market depth updates
        const symbol = 'AAPL'; // Default symbol
        window.wsService.subscribeToMarketDepth(symbol, (data) => {
            this.updateMarketDepth(data);
        });
    }

    async initializeAIWorkers() {
        try {
            const workers = await window.apiService.getAIWorkers();
            this.displayAIWorkers(workers);
            
            // Subscribe to AI worker updates
            window.wsService.subscribeToAIWorkers((data) => {
                this.updateAIWorkers(data);
            });
        } catch (error) {
            console.error('Failed to load AI workers:', error);
        }
    }

    async initializeBotStatus() {
        // Check if user is admin
        if (!this.currentUser || this.currentUser.role !== 'admin') {
            document.getElementById('main-content').innerHTML = `
                <div class="alert alert-danger">
                    Access denied. Admin privileges required.
                </div>
            `;
            return;
        }
        
        try {
            const botStatus = await window.apiService.getBotStatus();
            this.displayBotStatus(botStatus);
            
            // Subscribe to bot status updates
            window.wsService.subscribeToBotStatus((data) => {
                this.updateBotStatus(data);
            });
        } catch (error) {
            console.error('Failed to load bot status:', error);
        }
    }

    async initializePortfolio() {
        try {
            const portfolio = await window.apiService.getPortfolio();
            this.displayPortfolio(portfolio);
        } catch (error) {
            console.error('Failed to load portfolio:', error);
        }
    }

    async initializeBrokers() {
        // Add event listeners to connect buttons
        document.querySelectorAll('.connect-broker').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const brokerId = e.target.dataset.broker;
                await this.connectBroker(brokerId);
            });
        });
        
        // Load broker status
        try {
            const brokers = await window.apiService.getBrokers();
            this.updateBrokerStatus(brokers);
        } catch (error) {
            console.error('Failed to load brokers:', error);
        }
    }

    initializeManualTrade() {
        const orderTypeSelect = document.getElementById('trade-order-type');
        const priceInput = document.getElementById('price-input');
        
        if (orderTypeSelect) {
            orderTypeSelect.addEventListener('change', (e) => {
                if (e.target.value !== 'market') {
                    priceInput.style.display = 'block';
                } else {
                    priceInput.style.display = 'none';
                }
            });
        }
        
        const tradeForm = document.getElementById('manual-trade-form');
        if (tradeForm) {
            tradeForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.submitManualTrade();
            });
        }
    }

    async initializeHelpCentre() {
        try {
            const articles = await window.apiService.getHelpArticles();
            this.displayHelpArticles(articles);
        } catch (error) {
            console.error('Failed to load help articles:', error);
        }
    }

    async connectBroker(brokerId) {
        // Show connection modal or form
        this.showNotification({
            type: 'info',
            message: `Connecting to ${brokerId}...`
        });
        
        try {
            // In production, collect credentials via secure form
            const result = await window.apiService.connectBroker(brokerId, {});
            
            if (result.success) {
                this.showNotification({
                    type: 'success',
                    message: `Successfully connected to ${brokerId}`
                });
                
                // Refresh broker list
                await this.initializeBrokers();
            }
        } catch (error) {
            this.showNotification({
                type: 'error',
                message: `Failed to connect to ${brokerId}`
            });
        }
    }

    async submitManualTrade() {
        const tradeData = {
            symbol: document.getElementById('trade-symbol').value,
            side: document.getElementById('trade-side').value,
            quantity: parseInt(document.getElementById('trade-quantity').value),
            orderType: document.getElementById('trade-order-type').value,
            price: parseFloat(document.getElementById('trade-price').value) || null
        };
        
        try {
            const result = await window.apiService.placeManualTrade(tradeData);
            
            if (result.success) {
                this.showNotification({
                    type: 'success',
                    message: `Order placed: ${result.orderId}`
                });
                
                // Reset form
                document.getElementById('manual-trade-form').reset();
            } else {
                this.showNotification({
                    type: 'error',
                    message: result.error || 'Failed to place order'
                });
            }
        } catch (error) {
            this.showNotification({
                type: 'error',
                message: 'Failed to place order'
            });
        }
    }

    updatePositions(positions) {
        const positionsList = document.getElementById('positions-list');
        if (!positionsList) return;
        
        if (positions.length === 0) {
            positionsList.innerHTML = '<p class="text-muted">No open positions</p>';
            return;
        }
        
        let html = '<table class="table table-sm"><thead><tr>';
        html += '<th>Symbol</th><th>Qty</th><th>Avg Price</th><th>Current</th><th>P&L</th>';
        html += '</tr></thead><tbody>';
        
        positions.forEach(pos => {
            const pnlClass = pos.pnl >= 0 ? 'text-success' : 'text-danger';
            html += `<tr>
                <td>${pos.symbol}</td>
                <td>${pos.quantity}</td>
                <td>$${pos.avgPrice.toFixed(2)}</td>
                <td>$${pos.currentPrice.toFixed(2)}</td>
                <td class="${pnlClass}">$${pos.pnl.toFixed(2)}</td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        positionsList.innerHTML = html;
    }

    showNotification(notification) {
        // Create toast notification
        const toastHtml = `
            <div class="toast" role="alert">
                <div class="toast-header bg-${notification.type === 'success' ? 'success' : notification.type === 'error' ? 'danger' : 'info'} text-white">
                    <strong class="me-auto">AuraQuant</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${notification.message}
                </div>
            </div>
        `;
        
        // Add to toast container (create if doesn't exist)
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        toastContainer.appendChild(toastElement);
        
        const toast = new bootstrap.Toast(toastElement.querySelector('.toast'));
        toast.show();
        
        // Remove after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.auraquantApp = new AuraQuantApp();
});