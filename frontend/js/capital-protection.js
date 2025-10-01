/**
 * AuraQuant Capital Protection Module
 * Defense-in-depth implementation for protecting user capital
 * ADD-ONLY • NO REBUILD • HARD SAFETY RAILS
 */

class CapitalProtection {
    constructor() {
        this.engineMode = 'INITIALIZING';
        this.dataSource = 'PRIMARY';
        this.riskLimits = {};
        this.circuitBreakers = new Map();
        this.orderIdempotency = new Map();
        this.reconciliationState = {};
        this.wsConnection = null;
        this.heartbeatInterval = null;
        this.API_BASE = window.location.hostname === 'localhost' ? 
            'http://localhost:8000' : 'https://auraquant-backend.onrender.com';
        
        this.init();
    }
    
    async init() {
        console.log('🛡️ Initializing Capital Protection System');
        await this.loadRiskLimits();
        this.startHeartbeat();
        this.setupWebSocket();
        this.setupEventListeners();
        this.restoreSession();
    }
    
    // ========== RISK LIMITS & GUARDS ==========
    async loadRiskLimits() {
        try {
            const response = await fetch(`${this.API_BASE}/api/risk/limits`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            
            if (response.ok) {
                this.riskLimits = await response.json();
            } else {
                // Default conservative limits
                this.riskLimits = {
                    maxDrawdown: 0.20,
                    maxPositionSize: 0.10,
                    maxDailyLoss: 0.05,
                    maxOrdersPerMinute: 10,
                    staleDataThreshold: 5000, // 5 seconds
                    slippageThreshold: 0.02
                };
            }
        } catch (error) {
            console.error('Failed to load risk limits, using defaults:', error);
        }
    }
    
    // ========== KILL SWITCH ==========
    async triggerKillSwitch(reason = 'Manual trigger') {
        console.error('🚨 KILL SWITCH ACTIVATED:', reason);
        
        this.engineMode = 'PAUSED';
        this.updateStatusDisplay('KILL SWITCH ACTIVE', 'error');
        
        try {
            // Cancel all pending orders
            await fetch(`${this.API_BASE}/api/risk/kill-switch`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reason, timestamp: new Date().toISOString() })
            });
            
            // Notify all channels
            this.notifyAllChannels('KILL SWITCH ACTIVATED', reason, 'critical');
            
            // Log to audit
            this.auditLog('KILL_SWITCH', { reason, mode: this.engineMode });
            
        } catch (error) {
            console.error('Kill switch execution error:', error);
        }
    }
    
    // ========== CIRCUIT BREAKERS ==========
    checkCircuitBreaker(symbol, metrics) {
        const breaker = this.circuitBreakers.get(symbol) || {
            rejectCount: 0,
            slippageSum: 0,
            tradeCount: 0,
            lastReset: Date.now()
        };
        
        // Reset if time window expired (1 minute)
        if (Date.now() - breaker.lastReset > 60000) {
            breaker.rejectCount = 0;
            breaker.slippageSum = 0;
            breaker.tradeCount = 0;
            breaker.lastReset = Date.now();
        }
        
        // Update metrics
        if (metrics.rejected) breaker.rejectCount++;
        if (metrics.slippage) {
            breaker.slippageSum += Math.abs(metrics.slippage);
            breaker.tradeCount++;
        }
        
        // Check thresholds
        const avgSlippage = breaker.tradeCount > 0 ? 
            breaker.slippageSum / breaker.tradeCount : 0;
        
        if (breaker.rejectCount > 5 || avgSlippage > this.riskLimits.slippageThreshold) {
            console.warn(`⚡ Circuit breaker tripped for ${symbol}`);
            this.auditLog('CIRCUIT_BREAKER_TRIPPED', { symbol, breaker });
            return false; // Block trading
        }
        
        this.circuitBreakers.set(symbol, breaker);
        return true; // Allow trading
    }
    
    // ========== IDEMPOTENCY ==========
    generateOrderId(orderData) {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        const hash = `${orderData.symbol}_${orderData.side}_${timestamp}_${random}`;
        return `AQ_${hash}`;
    }
    
    isDuplicateOrder(orderId) {
        if (this.orderIdempotency.has(orderId)) {
            const existingOrder = this.orderIdempotency.get(orderId);
            // Check if order is recent (within 5 minutes)
            if (Date.now() - existingOrder.timestamp < 300000) {
                console.warn('Duplicate order detected:', orderId);
                return true;
            }
        }
        return false;
    }
    
    recordOrder(orderId, orderData) {
        this.orderIdempotency.set(orderId, {
            ...orderData,
            timestamp: Date.now()
        });
        
        // Clean old entries (older than 1 hour)
        const oneHourAgo = Date.now() - 3600000;
        for (const [id, order] of this.orderIdempotency.entries()) {
            if (order.timestamp < oneHourAgo) {
                this.orderIdempotency.delete(id);
            }
        }
    }
    
    // ========== PRE-TRADE VALIDATION ==========
    async validateOrder(orderData) {
        const validations = [];
        
        // 1. Check engine mode
        if (!['RUNNING', 'DEGRADED'].includes(this.engineMode)) {
            validations.push({
                passed: false,
                reason: `Trading disabled in ${this.engineMode} mode`
            });
        }
        
        // 2. Check data staleness
        if (orderData.priceAge && orderData.priceAge > this.riskLimits.staleDataThreshold) {
            validations.push({
                passed: false,
                reason: 'Price data is stale'
            });
        }
        
        // 3. Check position size
        const positionValue = orderData.price * orderData.quantity;
        const accountValue = await this.getAccountValue();
        const positionPercent = positionValue / accountValue;
        
        if (positionPercent > this.riskLimits.maxPositionSize) {
            validations.push({
                passed: false,
                reason: `Position size ${(positionPercent * 100).toFixed(2)}% exceeds limit`
            });
        }
        
        // 4. Check daily loss
        const dailyPnL = await this.getDailyPnL();
        if (dailyPnL < -this.riskLimits.maxDailyLoss * accountValue) {
            validations.push({
                passed: false,
                reason: 'Daily loss limit reached'
            });
        }
        
        // 5. Check circuit breaker
        if (!this.checkCircuitBreaker(orderData.symbol, {})) {
            validations.push({
                passed: false,
                reason: 'Circuit breaker active for symbol'
            });
        }
        
        // 6. Check idempotency
        if (this.isDuplicateOrder(orderData.orderId)) {
            validations.push({
                passed: false,
                reason: 'Duplicate order detected'
            });
        }
        
        const allPassed = validations.every(v => v.passed !== false);
        
        if (!allPassed) {
            console.error('Order validation failed:', validations);
            this.auditLog('ORDER_VALIDATION_FAILED', { orderData, validations });
        }
        
        return {
            valid: allPassed,
            validations
        };
    }
    
    // ========== SAFE DEPLOYMENT ==========
    async safeDeployment(deploymentId) {
        console.log('🚀 Starting safe deployment:', deploymentId);
        const deploymentSteps = [];
        
        try {
            // Step 1: Set to DRAINING mode
            this.engineMode = 'DRAINING';
            this.updateStatusDisplay('DEPLOYMENT: Draining', 'warning');
            deploymentSteps.push({ step: 'DRAINING', status: 'SUCCESS' });
            
            // Step 2: Cancel unfilled orders
            const cancelResult = await this.cancelAllOrders();
            deploymentSteps.push({ 
                step: 'CANCEL_ORDERS', 
                status: cancelResult.success ? 'SUCCESS' : 'FAILED',
                details: cancelResult
            });
            
            // Step 3: Reconcile positions
            const reconcileResult = await this.reconcilePositions();
            deploymentSteps.push({
                step: 'RECONCILE',
                status: reconcileResult.matched ? 'SUCCESS' : 'MISMATCH',
                details: reconcileResult
            });
            
            // Step 4: Create backup
            const backupResult = await this.createBackup(deploymentId);
            deploymentSteps.push({
                step: 'BACKUP',
                status: backupResult.success ? 'SUCCESS' : 'FAILED',
                details: backupResult
            });
            
            // Check if all steps passed
            const allSuccess = deploymentSteps.every(s => 
                s.status === 'SUCCESS' || s.status === 'MISMATCH'
            );
            
            if (!allSuccess) {
                throw new Error('Deployment pre-flight checks failed');
            }
            
            // Step 5: Proceed with deployment
            this.updateStatusDisplay('DEPLOYMENT: In Progress', 'info');
            
            return {
                success: true,
                deploymentId,
                steps: deploymentSteps
            };
            
        } catch (error) {
            console.error('Safe deployment failed:', error);
            
            // Rollback
            this.engineMode = 'RECOVERING';
            this.updateStatusDisplay('DEPLOYMENT: Rolling Back', 'error');
            
            await this.rollback(deploymentId);
            
            return {
                success: false,
                error: error.message,
                steps: deploymentSteps
            };
        }
    }
    
    // ========== RECONCILIATION ==========
    async reconcilePositions() {
        try {
            const [localPositions, brokerPositions] = await Promise.all([
                this.getLocalPositions(),
                this.getBrokerPositions()
            ]);
            
            const mismatches = [];
            
            // Compare positions
            for (const symbol in localPositions) {
                const local = localPositions[symbol];
                const broker = brokerPositions[symbol] || { quantity: 0, value: 0 };
                
                if (Math.abs(local.quantity - broker.quantity) > 0.0001) {
                    mismatches.push({
                        symbol,
                        local: local.quantity,
                        broker: broker.quantity,
                        diff: local.quantity - broker.quantity
                    });
                }
            }
            
            // Check for positions in broker not in local
            for (const symbol in brokerPositions) {
                if (!localPositions[symbol]) {
                    mismatches.push({
                        symbol,
                        local: 0,
                        broker: brokerPositions[symbol].quantity,
                        diff: -brokerPositions[symbol].quantity
                    });
                }
            }
            
            const result = {
                timestamp: new Date().toISOString(),
                matched: mismatches.length === 0,
                mismatches,
                localTotal: Object.keys(localPositions).length,
                brokerTotal: Object.keys(brokerPositions).length
            };
            
            // Log reconciliation
            this.auditLog('RECONCILIATION', result);
            
            if (!result.matched) {
                console.error('Position reconciliation failed:', mismatches);
                this.notifyAllChannels('Reconciliation Mismatch', 
                    `Found ${mismatches.length} position mismatches`, 'warning');
            }
            
            return result;
        } catch (error) {
            console.error('Reconciliation error:', error);
            return {
                matched: false,
                error: error.message
            };
        }
    }
    
    // ========== HEARTBEAT & KEEP-ALIVE ==========
    startHeartbeat() {
        // Clear existing interval if any
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        // Send heartbeat every 2 minutes
        this.heartbeatInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.API_BASE}/api/health/heartbeat`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        timestamp: new Date().toISOString(),
                        engineMode: this.engineMode,
                        dataSource: this.dataSource
                    })
                });
                
                if (!response.ok) {
                    console.warn('Heartbeat failed:', response.status);
                    this.handleConnectionDegradation();
                }
            } catch (error) {
                console.error('Heartbeat error:', error);
                this.handleConnectionDegradation();
            }
        }, 120000); // 2 minutes
    }
    
    // ========== WEBSOCKET & SESSION ==========
    setupWebSocket() {
        const wsUrl = this.API_BASE.replace('http', 'ws') + '/ws';
        
        const connect = () => {
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('✅ WebSocket connected');
                this.subscribeToChannels();
                this.updateConnectionStatus('connected');
            };
            
            this.wsConnection.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
            
            this.wsConnection.onclose = () => {
                console.warn('WebSocket disconnected, reconnecting...');
                this.updateConnectionStatus('disconnected');
                // Exponential backoff reconnection
                setTimeout(connect, Math.min(30000, 1000 * Math.pow(2, this.reconnectAttempts || 0)));
                this.reconnectAttempts = (this.reconnectAttempts || 0) + 1;
            };
        };
        
        connect();
    }
    
    subscribeToChannels() {
        const channels = ['orders/*', 'positions/*', 'alerts/*', 'health/*', 'risk/*'];
        
        if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
            this.wsConnection.send(JSON.stringify({
                type: 'subscribe',
                channels,
                token: this.getAuthToken()
            }));
        }
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'ENGINE_MODE':
                this.engineMode = message.mode;
                this.updateStatusDisplay(`Mode: ${message.mode}`, 
                    message.mode === 'RUNNING' ? 'success' : 'warning');
                break;
                
            case 'RISK_ALERT':
                this.handleRiskAlert(message);
                break;
                
            case 'POSITION_UPDATE':
                this.updateLocalPositions(message.positions);
                break;
                
            case 'ORDER_UPDATE':
                this.updateOrderDisplay(message.order);
                break;
                
            case 'DATA_SOURCE':
                this.handleDataSourceChange(message.source);
                break;
        }
    }
    
    // ========== SESSION MANAGEMENT ==========
    async restoreSession() {
        const sessionId = localStorage.getItem('auraquant_session');
        if (!sessionId) return;
        
        try {
            const response = await fetch(`${this.API_BASE}/api/session/restore`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sessionId })
            });
            
            if (response.ok) {
                const session = await response.json();
                console.log('✅ Session restored:', session.sessionId);
                
                // Restore UI state
                this.engineMode = session.engineMode;
                this.dataSource = session.dataSource;
                
                // Restore positions and orders
                if (session.positions) this.updateLocalPositions(session.positions);
                if (session.orders) this.updateOrderDisplay(session.orders);
                
                return session;
            }
        } catch (error) {
            console.error('Session restore failed:', error);
        }
    }
    
    // ========== FAILOVER MANAGEMENT ==========
    async handleDataSourceChange(newSource) {
        this.dataSource = newSource;
        
        if (newSource === 'FALLBACK') {
            // Switch to TradingView/Plus500 view-only mode
            this.engineMode = 'FALLBACK';
            this.disableTradingControls();
            
            this.showBanner(
                'Primary data unstable. Viewing fallback feed. Trading disabled.',
                'warning'
            );
            
            // Start recovery probe
            this.startRecoveryProbe();
        } else if (newSource === 'PRIMARY') {
            // Restored to primary
            this.engineMode = 'RECOVERING';
            
            // Verify reconciliation before resuming
            const reconciled = await this.reconcilePositions();
            
            if (reconciled.matched) {
                this.engineMode = 'RUNNING';
                this.enableTradingControls();
                this.hideBanner();
                
                this.showNotification('Primary data restored. Trading enabled.', 'success');
            } else {
                this.showNotification('Primary data restored but reconciliation failed. Manual review required.', 'error');
            }
        }
    }
    
    startRecoveryProbe() {
        const probe = setInterval(async () => {
            try {
                const response = await fetch(`${this.API_BASE}/api/health/primary`, {
                    timeout: 5000
                });
                
                if (response.ok) {
                    const health = await response.json();
                    if (health.status === 'healthy') {
                        clearInterval(probe);
                        this.handleDataSourceChange('PRIMARY');
                    }
                }
            } catch (error) {
                // Continue probing
            }
        }, 10000); // Every 10 seconds
    }
    
    // ========== UI HELPERS ==========
    updateStatusDisplay(text, type = 'info') {
        const statusBar = document.getElementById('capital-protection-status');
        if (statusBar) {
            statusBar.textContent = text;
            statusBar.className = `status-${type}`;
        }
    }
    
    showBanner(message, type = 'info') {
        const banner = document.getElementById('system-banner');
        if (banner) {
            banner.textContent = message;
            banner.className = `banner banner-${type}`;
            banner.style.display = 'block';
        }
    }
    
    hideBanner() {
        const banner = document.getElementById('system-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }
    
    disableTradingControls() {
        document.querySelectorAll('.trading-control').forEach(control => {
            control.disabled = true;
            control.classList.add('disabled');
        });
    }
    
    enableTradingControls() {
        document.querySelectorAll('.trading-control').forEach(control => {
            control.disabled = false;
            control.classList.remove('disabled');
        });
    }
    
    // ========== AUDIT & NOTIFICATION ==========
    async auditLog(action, details) {
        try {
            await fetch(`${this.API_BASE}/api/audit/log`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action,
                    details,
                    timestamp: new Date().toISOString(),
                    engineMode: this.engineMode,
                    dataSource: this.dataSource
                })
            });
        } catch (error) {
            console.error('Audit log failed:', error);
        }
    }
    
    async notifyAllChannels(title, message, severity = 'info') {
        const channels = ['telegram', 'discord', 'email', 'sms'];
        
        for (const channel of channels) {
            try {
                await fetch(`${this.API_BASE}/api/notify`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        channel,
                        title,
                        message,
                        severity,
                        timestamp: new Date().toISOString()
                    })
                });
            } catch (error) {
                console.error(`Notification to ${channel} failed:`, error);
            }
        }
    }
    
    // ========== UTILITY METHODS ==========
    getAuthToken() {
        return localStorage.getItem('auth_token') || localStorage.getItem('auraquant_token');
    }
    
    async getAccountValue() {
        try {
            const response = await fetch(`${this.API_BASE}/api/account/value`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            const data = await response.json();
            return data.value || 0;
        } catch {
            return 0;
        }
    }
    
    async getDailyPnL() {
        try {
            const response = await fetch(`${this.API_BASE}/api/account/daily-pnl`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            const data = await response.json();
            return data.pnl || 0;
        } catch {
            return 0;
        }
    }
    
    async getLocalPositions() {
        try {
            const response = await fetch(`${this.API_BASE}/api/positions`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            return await response.json();
        } catch {
            return {};
        }
    }
    
    async getBrokerPositions() {
        try {
            const response = await fetch(`${this.API_BASE}/api/broker/positions`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            return await response.json();
        } catch {
            return {};
        }
    }
    
    async cancelAllOrders() {
        try {
            const response = await fetch(`${this.API_BASE}/api/orders/cancel-all`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async createBackup(deploymentId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/backup/manual`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ deploymentId, type: 'pre-deployment' })
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async rollback(deploymentId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/deployment/rollback`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ deploymentId })
            });
            return await response.json();
        } catch (error) {
            console.error('Rollback failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    updateLocalPositions(positions) {
        // Update local state
        this.reconciliationState.localPositions = positions;
        
        // Update UI if handler exists
        if (window.updatePositionsDisplay) {
            window.updatePositionsDisplay(positions);
        }
    }
    
    updateOrderDisplay(orders) {
        // Update UI if handler exists
        if (window.updateOrdersDisplay) {
            window.updateOrdersDisplay(orders);
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element if doesn't exist
        let notification = document.getElementById('capital-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'capital-notification';
            document.body.appendChild(notification);
        }
        
        notification.textContent = message;
        notification.className = `notification notification-${type} show`;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }
    
    handleConnectionDegradation() {
        this.engineMode = 'DEGRADED';
        this.updateStatusDisplay('Connection degraded', 'warning');
    }
    
    handleRiskAlert(alert) {
        console.warn('Risk Alert:', alert);
        this.showNotification(alert.message, 'warning');
        
        if (alert.severity === 'critical') {
            this.triggerKillSwitch(alert.message);
        }
    }
    
    setupEventListeners() {
        // Listen for visibility changes to maintain connection
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Page is visible, ensure connection
                if (this.wsConnection.readyState !== WebSocket.OPEN) {
                    this.setupWebSocket();
                }
            }
        });
        
        // Listen for beforeunload to save session
        window.addEventListener('beforeunload', () => {
            const sessionData = {
                engineMode: this.engineMode,
                dataSource: this.dataSource,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('auraquant_session', JSON.stringify(sessionData));
        });
    }
}

// Initialize capital protection on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.capitalProtection = new CapitalProtection();
    });
} else {
    window.capitalProtection = new CapitalProtection();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CapitalProtection;
}