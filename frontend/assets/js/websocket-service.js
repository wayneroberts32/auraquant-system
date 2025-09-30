/**
 * AuraQuant WebSocket Service
 * Manages real-time data streaming and WebSocket connections
 */

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 5000;
        this.shouldReconnect = true;
        this.subscriptions = new Map();
        this.eventHandlers = new Map();
        this.wsUrl = window.location.hostname === 'localhost' 
            ? 'ws://localhost:8000' 
            : `wss://${window.location.host}`;
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.onConnectionOpen();
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.onConnectionClose();
                
                if (this.shouldReconnect) {
                    setTimeout(() => this.connect(), this.reconnectInterval);
                }
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    disconnect() {
        this.shouldReconnect = false;
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    onConnectionOpen() {
        // Update connection status
        const statusBadge = document.getElementById('connection-status');
        if (statusBadge) {
            statusBadge.className = 'badge bg-success me-2';
            statusBadge.innerHTML = '<i class="fas fa-circle"></i> Connected';
        }
        
        // Authenticate if token exists
        const token = localStorage.getItem('auraquant_token');
        if (token) {
            this.authenticate(token);
        }
        
        // Resubscribe to all channels
        this.subscriptions.forEach((callback, channel) => {
            this.subscribeToChannel(channel);
        });
    }

    onConnectionClose() {
        // Update connection status
        const statusBadge = document.getElementById('connection-status');
        if (statusBadge) {
            statusBadge.className = 'badge bg-danger me-2';
            statusBadge.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
        }
    }

    authenticate(token) {
        this.send({
            type: 'auth',
            token: token
        });
    }

    // =====================
    // Channel Subscriptions
    // =====================
    
    subscribe(channel, callback) {
        this.subscriptions.set(channel, callback);
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.subscribeToChannel(channel);
        }
    }

    unsubscribe(channel) {
        this.subscriptions.delete(channel);
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.send({
                type: 'unsubscribe',
                channel: channel
            });
        }
    }

    subscribeToChannel(channel) {
        this.send({
            type: 'subscribe',
            channel: channel
        });
    }

    // =====================
    // Real-time Data Channels
    // =====================
    
    subscribeToMarketDepth(symbol, callback) {
        this.subscribe(`market-depth:${symbol}`, callback);
    }

    subscribeToTickerTape(callback) {
        this.subscribe('ticker-tape', callback);
    }

    subscribeToPositions(callback) {
        this.subscribe('positions', callback);
    }

    subscribeToBotStatus(callback) {
        this.subscribe('bot-status', callback);
    }

    subscribeToAIWorkers(callback) {
        this.subscribe('ai-workers', callback);
    }

    subscribeToScreener(callback) {
        this.subscribe('screener', callback);
    }

    subscribeToAlerts(callback) {
        this.subscribe('alerts', callback);
    }

    // =====================
    // Actions
    // =====================
    
    placeMarketOrder(orderData) {
        this.send({
            type: 'action',
            action: 'market-order',
            data: orderData
        });
    }

    sendAIPrompt(workerId, prompt) {
        this.send({
            type: 'action',
            action: 'ai-prompt',
            data: {
                workerId: workerId,
                prompt: prompt
            }
        });
    }

    updateScreenerFilters(filters) {
        this.send({
            type: 'action',
            action: 'screener-filter',
            data: filters
        });
    }

    // =====================
    // Message Handling
    // =====================
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Handle different message types
            switch (message.type) {
                case 'ticker-tape':
                    this.updateTickerTape(message.data);
                    break;
                    
                case 'market-depth':
                    this.handleMarketDepth(message);
                    break;
                    
                case 'positions':
                    this.handlePositions(message.data);
                    break;
                    
                case 'bot-status':
                    this.handleBotStatus(message.data);
                    break;
                    
                case 'ai-workers':
                    this.handleAIWorkers(message.data);
                    break;
                    
                case 'screener':
                    this.handleScreener(message.data);
                    break;
                    
                case 'alert':
                    this.showAlert(message.data);
                    break;
                    
                case 'error':
                    console.error('WebSocket error:', message.error);
                    break;
            }
            
            // Call channel-specific callbacks
            if (message.channel && this.subscriptions.has(message.channel)) {
                const callback = this.subscriptions.get(message.channel);
                callback(message.data);
            }
            
            // Call event handlers
            if (message.event && this.eventHandlers.has(message.event)) {
                const handler = this.eventHandlers.get(message.event);
                handler(message.data);
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    // =====================
    // UI Updates
    // =====================
    
    updateTickerTape(data) {
        const tickerTape = document.getElementById('ticker-tape');
        if (!tickerTape) return;
        
        let html = '';
        data.forEach(item => {
            const changeClass = item.change >= 0 ? 'text-success' : 'text-danger';
            const arrow = item.change >= 0 ? '▲' : '▼';
            html += `
                <span class="ticker-item">
                    <span class="ticker-symbol">${item.symbol}</span>
                    <span class="ticker-price ${changeClass}">
                        $${item.price.toFixed(2)} ${arrow} ${Math.abs(item.change).toFixed(2)}%
                    </span>
                </span>
            `;
        });
        tickerTape.innerHTML = html;
    }

    handleMarketDepth(message) {
        // Update market depth UI component if visible
        if (window.location.hash === '#market-depth') {
            window.updateMarketDepth && window.updateMarketDepth(message.data);
        }
    }

    handlePositions(data) {
        // Update positions display
        if (window.updatePositions) {
            window.updatePositions(data);
        }
    }

    handleBotStatus(data) {
        // Update bot status panel
        if (window.updateBotStatus) {
            window.updateBotStatus(data);
        }
    }

    handleAIWorkers(data) {
        // Update AI workers panel
        if (window.updateAIWorkers) {
            window.updateAIWorkers(data);
        }
    }

    handleScreener(data) {
        // Update screener results
        if (window.updateScreenerResults) {
            window.updateScreenerResults(data);
        }
    }

    showAlert(alert) {
        // Show notification
        if (window.showNotification) {
            window.showNotification(alert);
        } else {
            console.log('Alert:', alert);
        }
    }

    // =====================
    // Event Handlers
    // =====================
    
    on(event, handler) {
        this.eventHandlers.set(event, handler);
    }

    off(event) {
        this.eventHandlers.delete(event);
    }

    // =====================
    // Utilities
    // =====================
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected');
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Create global instance
window.wsService = new WebSocketService();