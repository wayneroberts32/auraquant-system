/**
 * AuraQuant Menu Registry
 * Central registry of button to page routes
 * Preserves single-tab navigation with no style changes
 */

const MenuRegistry = {
    // Page routes mapping
    routes: {
        // Trading Section
        'dashboard': 'main-trading-dashboard.html',
        'market-depth': 'market-depth-demo.html',
        'screener': 'market-depth-demo.html',
        'manual-trade': 'manual-trade.html',
        'paper-trading': 'asx-paper-trading-launcher.html',
        
        // AI & Automation
        'ai-workers': 'ai-workers-panel.html',
        'bot-status': 'bot-status.html',
        'growth-selector': 'growth-selector.html',
        
        // Portfolio & Analytics
        'portfolio': 'unified-dashboard.html',
        'pnl': 'pnl-dashboard.html',
        'performance': 'performance-monitor.html',
        'heatmaps': 'heatmaps.html',
        
        // Brokers & Tools
        'brokers': 'brokers-banks.html',
        'tax-calculator': 'tax-calculator.html',
        'fees': 'fees-display.html',
        'libraries': 'libraries.html',
        'balance': 'balance-control.html',
        
        // Community & Help
        'community': 'unified-dashboard.html',
        'help': 'help-centre.html',
        
        // Admin Only
        'deployment': 'deployment-verification.html',
        'global-view': 'unified-dashboard.html',
        
        // Login
        'login': 'login.html',
        
        // Main chart
        'auraquant': 'auraquant.html'
    },
    
    // Admin-only pages
    adminPages: ['bot-status', 'deployment', 'global-view', 'performance'],
    
    // Initialize menu registry
    init() {
        console.log('Menu Registry initialized with', Object.keys(this.routes).length, 'routes');
    },
    
    // Get page URL for a route
    getPageUrl(route) {
        const page = this.routes[route];
        return page ? `pages/${page}` : null;
    },
    
    // Check if page requires admin access
    requiresAdmin(route) {
        return this.adminPages.includes(route);
    },
    
    // Navigate to a page (used by workspace manager)
    navigate(route, userRole = 'trader') {
        // Check admin access
        if (this.requiresAdmin(route) && userRole !== 'admin') {
            console.warn('Access denied: Admin privileges required');
            return false;
        }
        
        const pageUrl = this.getPageUrl(route);
        if (pageUrl) {
            // This will be handled by workspace manager
            if (window.workspaceManager) {
                window.workspaceManager.loadPage(pageUrl);
            } else {
                // Fallback for testing
                console.log('Would navigate to:', pageUrl);
            }
            return true;
        }
        
        console.warn('Route not found:', route);
        return false;
    },
    
    // Get all routes for a section
    getRoutesForSection(section) {
        const sections = {
            trading: ['dashboard', 'market-depth', 'screener', 'manual-trade', 'paper-trading'],
            ai: ['ai-workers', 'bot-status', 'growth-selector'],
            analytics: ['portfolio', 'pnl', 'performance', 'heatmaps'],
            tools: ['brokers', 'tax-calculator', 'fees', 'libraries', 'balance'],
            community: ['community', 'help'],
            admin: ['deployment', 'global-view']
        };
        
        return sections[section] || [];
    },
    
    // Backend endpoint mapping
    getEndpoint(route) {
        const endpoints = {
            'dashboard': '/api/portfolio',
            'market-depth': '/api/market-depth',
            'screener': '/api/screener',
            'manual-trade': '/api/manual-trade',
            'paper-trading': '/api/paper-trading/session',
            'ai-workers': '/api/ai-workers',
            'bot-status': '/api/bot-status',
            'growth-selector': '/api/growth-selector/profile',
            'portfolio': '/api/portfolio',
            'pnl': '/api/pnl',
            'performance': '/api/performance',
            'heatmaps': '/api/heatmaps/sectors',
            'brokers': '/api/brokers',
            'tax-calculator': '/api/tax-calculator',
            'fees': '/api/fees',
            'libraries': '/api/libraries',
            'balance': '/api/balance',
            'community': '/api/community',
            'help': '/api/help-centre',
            'deployment': '/api/deployment-verification',
            'global-view': '/api/admin/global-view'
        };
        
        return endpoints[route] || null;
    },
    
    // WebSocket channel mapping
    getWSChannel(route) {
        const channels = {
            'market-depth': 'market-depth',
            'screener': 'screener',
            'ai-workers': 'ai-workers',
            'bot-status': 'bot-status',
            'portfolio': 'positions',
            'pnl': 'positions',
            'heatmaps': 'heatmaps'
        };
        
        return channels[route] || null;
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => MenuRegistry.init());
} else {
    MenuRegistry.init();
}

// Export for use in other modules
window.MenuRegistry = MenuRegistry;