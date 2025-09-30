/**
 * AuraQuant Alert System
 * Ultra-sophisticated alerting and notification system
 * Supports price alerts, indicator triggers, pattern recognition, and multi-channel notifications
 */

class AuraQuantAlertSystem {
    constructor(config = {}) {
        // Configuration
        this.config = {
            maxAlerts: 1000,
            checkInterval: 100, // ms
            throttleDelay: 1000, // ms between same alerts
            soundEnabled: true,
            visualEnabled: true,
            pushEnabled: true,
            emailEnabled: false,
            smsEnabled: false,
            webhookEnabled: true,
            ...config
        };

        // Alert storage
        this.alerts = new Map();
        this.activeAlerts = new Set();
        this.triggeredAlerts = new Map();
        this.alertHistory = [];
        
        // Alert types
        this.alertTypes = {
            PRICE_ABOVE: 'price_above',
            PRICE_BELOW: 'price_below',
            PRICE_CROSS: 'price_cross',
            VOLUME_SPIKE: 'volume_spike',
            INDICATOR_CROSS: 'indicator_cross',
            INDICATOR_LEVEL: 'indicator_level',
            PATTERN_DETECTED: 'pattern_detected',
            ORDER_FILLED: 'order_filled',
            POSITION_PNL: 'position_pnl',
            RISK_WARNING: 'risk_warning',
            NEWS_EVENT: 'news_event',
            CUSTOM: 'custom'
        };

        // Notification channels
        this.notificationChannels = {
            sound: this.config.soundEnabled,
            visual: this.config.visualEnabled,
            push: this.config.pushEnabled,
            email: this.config.emailEnabled,
            sms: this.config.smsEnabled,
            webhook: this.config.webhookEnabled
        };

        // Sound library
        this.sounds = {
            success: this.createSound(800, 'sine', 100),
            warning: this.createSound(600, 'square', 150),
            danger: this.createSound(400, 'sawtooth', 200),
            info: this.createSound(1000, 'sine', 50)
        };

        // Visual notification container
        this.visualContainer = null;
        this.visualQueue = [];
        
        // Performance tracking
        this.performance = {
            checksPerformed: 0,
            alertsTriggered: 0,
            notificationsSent: 0,
            averageCheckTime: 0,
            lastCheckTime: 0
        };

        // Market data connection
        this.dataProviders = new Map();
        this.priceFeeds = new Map();
        
        // Alert conditions evaluator
        this.conditionEvaluator = new AlertConditionEvaluator();
        
        // Pattern recognition engine
        this.patternEngine = new PatternRecognitionEngine();
        
        // Initialize
        this.initialize();
    }

    initialize() {
        // Create visual notification container
        this.createVisualContainer();
        
        // Start alert checking loop
        this.startAlertChecking();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize notification permissions
        this.requestNotificationPermissions();
    }

    /**
     * Create a new alert
     */
    createAlert(alertConfig) {
        const alert = {
            id: this.generateAlertId(),
            type: alertConfig.type || this.alertTypes.CUSTOM,
            symbol: alertConfig.symbol,
            name: alertConfig.name || 'Unnamed Alert',
            conditions: alertConfig.conditions || [],
            actions: alertConfig.actions || ['sound', 'visual'],
            priority: alertConfig.priority || 'medium',
            recurring: alertConfig.recurring || false,
            expiry: alertConfig.expiry || null,
            throttle: alertConfig.throttle || this.config.throttleDelay,
            metadata: alertConfig.metadata || {},
            created: Date.now(),
            lastTriggered: null,
            triggerCount: 0,
            enabled: true,
            status: 'active'
        };

        // Validate alert
        if (!this.validateAlert(alert)) {
            throw new Error('Invalid alert configuration');
        }

        // Store alert
        this.alerts.set(alert.id, alert);
        this.activeAlerts.add(alert.id);

        // Setup specific alert handlers
        this.setupAlertHandlers(alert);

        console.log(`Alert created: ${alert.name} (${alert.id})`);
        return alert;
    }

    /**
     * Setup alert handlers based on type
     */
    setupAlertHandlers(alert) {
        switch (alert.type) {
            case this.alertTypes.PRICE_ABOVE:
            case this.alertTypes.PRICE_BELOW:
            case this.alertTypes.PRICE_CROSS:
                this.setupPriceAlert(alert);
                break;
            
            case this.alertTypes.VOLUME_SPIKE:
                this.setupVolumeAlert(alert);
                break;
            
            case this.alertTypes.INDICATOR_CROSS:
            case this.alertTypes.INDICATOR_LEVEL:
                this.setupIndicatorAlert(alert);
                break;
            
            case this.alertTypes.PATTERN_DETECTED:
                this.setupPatternAlert(alert);
                break;
            
            case this.alertTypes.ORDER_FILLED:
                this.setupOrderAlert(alert);
                break;
            
            case this.alertTypes.POSITION_PNL:
                this.setupPositionAlert(alert);
                break;
            
            case this.alertTypes.RISK_WARNING:
                this.setupRiskAlert(alert);
                break;
            
            default:
                this.setupCustomAlert(alert);
        }
    }

    /**
     * Setup price-based alert
     */
    setupPriceAlert(alert) {
        const { symbol, conditions } = alert;
        
        // Subscribe to price feed
        if (!this.priceFeeds.has(symbol)) {
            this.subscribeToPriceFeed(symbol);
        }
        
        // Add to price alert watchers
        const priceWatcher = {
            alertId: alert.id,
            symbol,
            conditions,
            check: (price) => {
                return this.conditionEvaluator.evaluatePriceConditions(price, conditions);
            }
        };
        
        this.addWatcher('price', priceWatcher);
    }

    /**
     * Setup volume-based alert
     */
    setupVolumeAlert(alert) {
        const { symbol, conditions } = alert;
        
        const volumeWatcher = {
            alertId: alert.id,
            symbol,
            conditions,
            volumeHistory: [],
            check: (volume) => {
                // Track volume history
                this.volumeHistory.push({ time: Date.now(), volume });
                if (this.volumeHistory.length > 100) {
                    this.volumeHistory.shift();
                }
                
                // Check for volume spike
                const avgVolume = this.volumeHistory.reduce((sum, v) => sum + v.volume, 0) / this.volumeHistory.length;
                const spike = volume > avgVolume * (conditions.spikeMultiplier || 2);
                
                return spike;
            }
        };
        
        this.addWatcher('volume', volumeWatcher);
    }

    /**
     * Setup indicator-based alert
     */
    setupIndicatorAlert(alert) {
        const { symbol, conditions, metadata } = alert;
        const { indicator, params } = metadata;
        
        const indicatorWatcher = {
            alertId: alert.id,
            symbol,
            indicator,
            params,
            conditions,
            values: [],
            check: (data) => {
                // Calculate indicator value
                const value = this.calculateIndicator(indicator, data, params);
                this.values.push(value);
                
                // Check conditions
                return this.conditionEvaluator.evaluateIndicatorConditions(value, this.values, conditions);
            }
        };
        
        this.addWatcher('indicator', indicatorWatcher);
    }

    /**
     * Setup pattern detection alert
     */
    setupPatternAlert(alert) {
        const { symbol, metadata } = alert;
        const { patterns } = metadata;
        
        const patternWatcher = {
            alertId: alert.id,
            symbol,
            patterns,
            check: (data) => {
                // Use pattern recognition engine
                const detected = this.patternEngine.detectPatterns(data, patterns);
                return detected.length > 0;
            }
        };
        
        this.addWatcher('pattern', patternWatcher);
    }

    /**
     * Main alert checking loop
     */
    startAlertChecking() {
        setInterval(() => {
            const startTime = performance.now();
            
            // Check all active alerts
            this.activeAlerts.forEach(alertId => {
                const alert = this.alerts.get(alertId);
                if (alert && alert.enabled) {
                    this.checkAlert(alert);
                }
            });
            
            // Update performance metrics
            const checkTime = performance.now() - startTime;
            this.performance.checksPerformed++;
            this.performance.lastCheckTime = checkTime;
            this.performance.averageCheckTime = 
                (this.performance.averageCheckTime * (this.performance.checksPerformed - 1) + checkTime) / 
                this.performance.checksPerformed;
            
        }, this.config.checkInterval);
    }

    /**
     * Check if alert conditions are met
     */
    checkAlert(alert) {
        // Check if alert is throttled
        if (this.isThrottled(alert)) {
            return;
        }
        
        // Check expiry
        if (alert.expiry && Date.now() > alert.expiry) {
            this.disableAlert(alert.id);
            return;
        }
        
        // Evaluate conditions
        const triggered = this.evaluateAlertConditions(alert);
        
        if (triggered) {
            this.triggerAlert(alert);
        }
    }

    /**
     * Evaluate alert conditions
     */
    evaluateAlertConditions(alert) {
        const { type, conditions } = alert;
        
        // Get current data
        const data = this.getCurrentData(alert.symbol);
        
        // Evaluate based on alert type
        switch (type) {
            case this.alertTypes.PRICE_ABOVE:
                return data.price > conditions.threshold;
            
            case this.alertTypes.PRICE_BELOW:
                return data.price < conditions.threshold;
            
            case this.alertTypes.PRICE_CROSS:
                return this.checkPriceCross(data.price, conditions);
            
            case this.alertTypes.VOLUME_SPIKE:
                return this.checkVolumeSpike(data.volume, conditions);
            
            case this.alertTypes.INDICATOR_CROSS:
                return this.checkIndicatorCross(data, conditions);
            
            case this.alertTypes.PATTERN_DETECTED:
                return this.checkPattern(data, conditions);
            
            case this.alertTypes.CUSTOM:
                return this.evaluateCustomConditions(data, conditions);
            
            default:
                return false;
        }
    }

    /**
     * Trigger an alert
     */
    triggerAlert(alert) {
        console.log(`Alert triggered: ${alert.name}`);
        
        // Update alert stats
        alert.lastTriggered = Date.now();
        alert.triggerCount++;
        
        // Add to triggered alerts for throttling
        this.triggeredAlerts.set(alert.id, Date.now());
        
        // Add to history
        this.alertHistory.push({
            alertId: alert.id,
            name: alert.name,
            type: alert.type,
            triggeredAt: Date.now(),
            data: this.getCurrentData(alert.symbol)
        });
        
        // Limit history size
        if (this.alertHistory.length > 1000) {
            this.alertHistory.shift();
        }
        
        // Execute actions
        this.executeAlertActions(alert);
        
        // Update performance
        this.performance.alertsTriggered++;
        
        // Check if alert should be disabled (non-recurring)
        if (!alert.recurring) {
            this.disableAlert(alert.id);
        }
    }

    /**
     * Execute alert actions
     */
    executeAlertActions(alert) {
        const { actions, priority } = alert;
        
        actions.forEach(action => {
            switch (action) {
                case 'sound':
                    this.playAlertSound(priority);
                    break;
                
                case 'visual':
                    this.showVisualNotification(alert);
                    break;
                
                case 'push':
                    this.sendPushNotification(alert);
                    break;
                
                case 'email':
                    this.sendEmailNotification(alert);
                    break;
                
                case 'sms':
                    this.sendSMSNotification(alert);
                    break;
                
                case 'webhook':
                    this.sendWebhookNotification(alert);
                    break;
                
                case 'execute_trade':
                    this.executeTrade(alert);
                    break;
                
                case 'close_position':
                    this.closePosition(alert);
                    break;
                
                default:
                    if (typeof action === 'function') {
                        action(alert);
                    }
            }
        });
        
        this.performance.notificationsSent++;
    }

    /**
     * Play alert sound
     */
    playAlertSound(priority) {
        if (!this.config.soundEnabled) return;
        
        const soundType = {
            low: 'info',
            medium: 'success',
            high: 'warning',
            critical: 'danger'
        }[priority] || 'info';
        
        this.sounds[soundType].play();
    }

    /**
     * Show visual notification
     */
    showVisualNotification(alert) {
        if (!this.config.visualEnabled) return;
        
        const notification = document.createElement('div');
        notification.className = `alert-notification alert-${alert.priority}`;
        notification.innerHTML = `
            <div class="alert-header">
                <span class="alert-icon">${this.getAlertIcon(alert.type)}</span>
                <span class="alert-title">${alert.name}</span>
                <span class="alert-close" onclick="this.parentElement.parentElement.remove()">×</span>
            </div>
            <div class="alert-body">
                <div class="alert-message">${this.formatAlertMessage(alert)}</div>
                <div class="alert-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        // Style based on priority
        const colors = {
            low: '#00ff88',
            medium: '#00ffff',
            high: '#ff00ff',
            critical: '#ff0066'
        };
        
        notification.style.borderLeft = `4px solid ${colors[alert.priority]}`;
        notification.style.animation = 'slideIn 0.3s ease-out';
        
        // Add to container
        this.visualContainer.appendChild(notification);
        
        // Auto-remove after delay
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // Limit notifications on screen
        while (this.visualContainer.children.length > 5) {
            this.visualContainer.removeChild(this.visualContainer.firstChild);
        }
    }

    /**
     * Send push notification
     */
    async sendPushNotification(alert) {
        if (!this.config.pushEnabled) return;
        
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(alert.name, {
                body: this.formatAlertMessage(alert),
                icon: '/icons/alert-icon.png',
                badge: '/icons/badge-icon.png',
                tag: alert.id,
                requireInteraction: alert.priority === 'critical',
                silent: false,
                vibrate: [200, 100, 200]
            });
            
            notification.onclick = () => {
                window.focus();
                // Navigate to relevant section
                this.handleNotificationClick(alert);
            };
        }
    }

    /**
     * Send webhook notification
     */
    async sendWebhookNotification(alert) {
        if (!this.config.webhookEnabled || !this.config.webhookUrl) return;
        
        try {
            const payload = {
                alert: {
                    id: alert.id,
                    name: alert.name,
                    type: alert.type,
                    priority: alert.priority,
                    symbol: alert.symbol,
                    triggeredAt: Date.now()
                },
                data: this.getCurrentData(alert.symbol),
                message: this.formatAlertMessage(alert)
            };
            
            const response = await fetch(this.config.webhookUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Alert-Priority': alert.priority
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                console.error('Webhook notification failed:', response.statusText);
            }
        } catch (error) {
            console.error('Failed to send webhook notification:', error);
        }
    }

    /**
     * Create visual notification container
     */
    createVisualContainer() {
        if (typeof document === 'undefined') return;
        
        this.visualContainer = document.createElement('div');
        this.visualContainer.id = 'auraquant-alerts';
        this.visualContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        
        document.body.appendChild(this.visualContainer);
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .alert-notification {
                background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 51, 51, 0.9));
                border-radius: 8px;
                margin-bottom: 10px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0, 255, 255, 0.2);
                backdrop-filter: blur(10px);
            }
            
            .alert-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                color: #00ffff;
                font-weight: bold;
            }
            
            .alert-close {
                cursor: pointer;
                font-size: 20px;
                color: #ff00ff;
            }
            
            .alert-body {
                color: #ffffff;
            }
            
            .alert-time {
                font-size: 12px;
                color: #888;
                margin-top: 5px;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Create sound effect
     */
    createSound(frequency, type, duration) {
        if (typeof window === 'undefined' || !window.AudioContext) {
            return { play: () => {} };
        }
        
        return {
            play: () => {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = frequency;
                oscillator.type = type;
                
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + duration / 1000);
            }
        };
    }

    /**
     * Request notification permissions
     */
    async requestNotificationPermissions() {
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            console.log('Notification permission:', permission);
        }
    }

    /**
     * Subscribe to price feed
     */
    subscribeToPriceFeed(symbol) {
        // This would connect to your WebSocket manager
        console.log(`Subscribing to price feed for ${symbol}`);
        
        // Simulate price feed
        const feed = {
            symbol,
            price: 0,
            volume: 0,
            lastUpdate: Date.now()
        };
        
        this.priceFeeds.set(symbol, feed);
    }

    /**
     * Get current market data
     */
    getCurrentData(symbol) {
        const feed = this.priceFeeds.get(symbol) || {};
        return {
            symbol,
            price: feed.price || 0,
            volume: feed.volume || 0,
            timestamp: Date.now(),
            ...feed
        };
    }

    /**
     * Check if alert is throttled
     */
    isThrottled(alert) {
        const lastTriggered = this.triggeredAlerts.get(alert.id);
        if (!lastTriggered) return false;
        
        return Date.now() - lastTriggered < alert.throttle;
    }

    /**
     * Format alert message
     */
    formatAlertMessage(alert) {
        const data = this.getCurrentData(alert.symbol);
        const templates = {
            [this.alertTypes.PRICE_ABOVE]: `${alert.symbol} price above ${alert.conditions.threshold}: ${data.price}`,
            [this.alertTypes.PRICE_BELOW]: `${alert.symbol} price below ${alert.conditions.threshold}: ${data.price}`,
            [this.alertTypes.VOLUME_SPIKE]: `${alert.symbol} volume spike detected: ${data.volume}`,
            [this.alertTypes.PATTERN_DETECTED]: `Pattern detected on ${alert.symbol}`,
            [this.alertTypes.ORDER_FILLED]: `Order filled for ${alert.symbol}`,
            [this.alertTypes.RISK_WARNING]: `Risk warning for ${alert.symbol}`
        };
        
        return templates[alert.type] || `Alert: ${alert.name}`;
    }

    /**
     * Get alert icon
     */
    getAlertIcon(type) {
        const icons = {
            [this.alertTypes.PRICE_ABOVE]: '📈',
            [this.alertTypes.PRICE_BELOW]: '📉',
            [this.alertTypes.VOLUME_SPIKE]: '📊',
            [this.alertTypes.PATTERN_DETECTED]: '🔍',
            [this.alertTypes.ORDER_FILLED]: '✅',
            [this.alertTypes.RISK_WARNING]: '⚠️'
        };
        
        return icons[type] || '🔔';
    }

    /**
     * Generate unique alert ID
     */
    generateAlertId() {
        return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Validate alert configuration
     */
    validateAlert(alert) {
        // Check required fields
        if (!alert.symbol || !alert.type) {
            return false;
        }
        
        // Check conditions
        if (!alert.conditions || alert.conditions.length === 0) {
            return false;
        }
        
        // Check max alerts limit
        if (this.alerts.size >= this.config.maxAlerts) {
            console.warn('Maximum alerts limit reached');
            return false;
        }
        
        return true;
    }

    /**
     * Add watcher
     */
    addWatcher(type, watcher) {
        if (!this.watchers) {
            this.watchers = new Map();
        }
        
        if (!this.watchers.has(type)) {
            this.watchers.set(type, []);
        }
        
        this.watchers.get(type).push(watcher);
    }

    /**
     * Disable alert
     */
    disableAlert(alertId) {
        const alert = this.alerts.get(alertId);
        if (alert) {
            alert.enabled = false;
            alert.status = 'disabled';
            this.activeAlerts.delete(alertId);
            console.log(`Alert disabled: ${alert.name}`);
        }
    }

    /**
     * Enable alert
     */
    enableAlert(alertId) {
        const alert = this.alerts.get(alertId);
        if (alert) {
            alert.enabled = true;
            alert.status = 'active';
            this.activeAlerts.add(alertId);
            console.log(`Alert enabled: ${alert.name}`);
        }
    }

    /**
     * Delete alert
     */
    deleteAlert(alertId) {
        const alert = this.alerts.get(alertId);
        if (alert) {
            this.alerts.delete(alertId);
            this.activeAlerts.delete(alertId);
            this.triggeredAlerts.delete(alertId);
            console.log(`Alert deleted: ${alert.name}`);
        }
    }

    /**
     * Get all alerts
     */
    getAllAlerts() {
        return Array.from(this.alerts.values());
    }

    /**
     * Get alert by ID
     */
    getAlert(alertId) {
        return this.alerts.get(alertId);
    }

    /**
     * Get alert history
     */
    getAlertHistory(limit = 100) {
        return this.alertHistory.slice(-limit);
    }

    /**
     * Get performance stats
     */
    getPerformanceStats() {
        return {
            ...this.performance,
            totalAlerts: this.alerts.size,
            activeAlerts: this.activeAlerts.size,
            historySize: this.alertHistory.length
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for market data updates
        if (typeof window !== 'undefined') {
            window.addEventListener('marketUpdate', (event) => {
                this.handleMarketUpdate(event.detail);
            });
        }
    }

    /**
     * Handle market update
     */
    handleMarketUpdate(data) {
        const { symbol, price, volume } = data;
        
        // Update price feed
        if (this.priceFeeds.has(symbol)) {
            const feed = this.priceFeeds.get(symbol);
            feed.price = price;
            feed.volume = volume;
            feed.lastUpdate = Date.now();
        }
    }
}

/**
 * Alert Condition Evaluator
 */
class AlertConditionEvaluator {
    evaluatePriceConditions(price, conditions) {
        return conditions.every(condition => {
            switch (condition.operator) {
                case '>':
                    return price > condition.value;
                case '<':
                    return price < condition.value;
                case '>=':
                    return price >= condition.value;
                case '<=':
                    return price <= condition.value;
                case '==':
                    return price === condition.value;
                case 'between':
                    return price >= condition.min && price <= condition.max;
                default:
                    return false;
            }
        });
    }

    evaluateIndicatorConditions(value, history, conditions) {
        // Implement indicator condition evaluation
        return true;
    }

    evaluateCustomConditions(data, conditions) {
        // Evaluate custom conditions
        if (typeof conditions === 'function') {
            return conditions(data);
        }
        return true;
    }
}

/**
 * Pattern Recognition Engine
 */
class PatternRecognitionEngine {
    detectPatterns(data, patterns) {
        const detected = [];
        
        patterns.forEach(pattern => {
            if (this.detectPattern(data, pattern)) {
                detected.push(pattern);
            }
        });
        
        return detected;
    }

    detectPattern(data, pattern) {
        // Implement pattern detection logic
        // This would include various chart patterns like head and shoulders, triangles, etc.
        return false;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuraQuantAlertSystem;
}
