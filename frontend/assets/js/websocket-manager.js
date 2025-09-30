/**
 * AuraQuant WebSocket Manager
 * Ultra-sophisticated real-time data streaming system
 * Handles multiple exchanges, auto-reconnection, and message queuing
 */

class AuraQuantWebSocketManager {
    constructor(config = {}) {
        // Configuration
        this.config = {
            reconnectDelay: 1000,
            maxReconnectDelay: 30000,
            reconnectDecay: 1.5,
            messageQueueSize: 10000,
            heartbeatInterval: 30000,
            responseTimeout: 5000,
            ...config
        };

        // WebSocket connections
        this.connections = new Map();
        this.subscriptions = new Map();
        this.messageQueue = [];
        this.callbacks = new Map();
        this.heartbeatTimers = new Map();
        
        // State management
        this.connectionStates = new Map();
        this.reconnectAttempts = new Map();
        this.lastMessageTimes = new Map();
        
        // Performance metrics
        this.metrics = {
            messagesReceived: 0,
            messagesSent: 0,
            bytesReceived: 0,
            bytesSent: 0,
            latency: new Map(),
            connectionUptime: new Map()
        };

        // Event emitter
        this.eventHandlers = new Map();
        
        // Color scheme for visual indicators
        this.colors = {
            connected: '#00ff88',
            connecting: '#00ffff',
            disconnected: '#ff00ff',
            error: '#ff0066',
            warning: '#ffaa00'
        };

        // Exchange configurations
        this.exchanges = {
            binance: {
                spot: 'wss://stream.binance.com:9443/ws',
                futures: 'wss://fstream.binance.com/ws',
                options: {
                    perMessageDeflate: false,
                    handshakeTimeout: 5000
                }
            },
            coinbase: {
                main: 'wss://ws-feed.exchange.coinbase.com',
                sandbox: 'wss://ws-feed-public.sandbox.exchange.coinbase.com',
                options: {
                    perMessageDeflate: true
                }
            },
            kraken: {
                public: 'wss://ws.kraken.com',
                private: 'wss://ws-auth.kraken.com',
                options: {}
            },
            bybit: {
                spot: 'wss://stream.bybit.com/v5/public/spot',
                futures: 'wss://stream.bybit.com/v5/public/linear',
                options: {}
            },
            okx: {
                public: 'wss://ws.okx.com:8443/ws/v5/public',
                private: 'wss://ws.okx.com:8443/ws/v5/private',
                options: {}
            }
        };

        // Initialize
        this.initialize();
    }

    initialize() {
        // Setup global error handlers
        if (typeof window !== 'undefined') {
            window.addEventListener('online', () => this.handleNetworkChange(true));
            window.addEventListener('offline', () => this.handleNetworkChange(false));
        }

        // Start metrics collection
        this.startMetricsCollection();
    }

    /**
     * Connect to exchange WebSocket
     */
    async connect(exchangeId, endpoint = 'main', customUrl = null) {
        try {
            const url = customUrl || this.getExchangeUrl(exchangeId, endpoint);
            if (!url) {
                throw new Error(`Invalid exchange or endpoint: ${exchangeId}/${endpoint}`);
            }

            // Check if already connected
            const connId = `${exchangeId}_${endpoint}`;
            if (this.connections.has(connId)) {
                console.warn(`Already connected to ${connId}`);
                return this.connections.get(connId);
            }

            // Create WebSocket connection
            const options = this.exchanges[exchangeId]?.options || {};
            const ws = new WebSocket(url);
            
            // Store connection
            this.connections.set(connId, ws);
            this.connectionStates.set(connId, 'connecting');
            this.reconnectAttempts.set(connId, 0);

            // Setup event handlers
            this.setupWebSocketHandlers(ws, connId);

            // Wait for connection
            await this.waitForConnection(connId);

            // Start heartbeat
            this.startHeartbeat(connId);

            // Emit connected event
            this.emit('connected', { exchangeId, endpoint, connId });

            return ws;

        } catch (error) {
            console.error(`Failed to connect to ${exchangeId}/${endpoint}:`, error);
            this.emit('error', { exchangeId, endpoint, error });
            throw error;
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupWebSocketHandlers(ws, connId) {
        ws.onopen = () => {
            console.log(`WebSocket connected: ${connId}`);
            this.connectionStates.set(connId, 'connected');
            this.reconnectAttempts.set(connId, 0);
            this.metrics.connectionUptime.set(connId, Date.now());
            
            // Process queued messages
            this.processMessageQueue(connId);
            
            // Resubscribe to channels
            this.resubscribe(connId);
        };

        ws.onmessage = (event) => {
            this.handleMessage(connId, event);
        };

        ws.onerror = (error) => {
            console.error(`WebSocket error on ${connId}:`, error);
            this.connectionStates.set(connId, 'error');
            this.emit('error', { connId, error });
        };

        ws.onclose = (event) => {
            console.log(`WebSocket closed: ${connId}`, event.code, event.reason);
            this.handleDisconnection(connId, event);
        };
    }

    /**
     * Handle incoming messages
     */
    handleMessage(connId, event) {
        try {
            // Update metrics
            this.metrics.messagesReceived++;
            this.metrics.bytesReceived += event.data.length;
            this.lastMessageTimes.set(connId, Date.now());

            // Parse message
            let data;
            if (typeof event.data === 'string') {
                data = JSON.parse(event.data);
            } else {
                // Handle binary data
                data = this.decodeBinaryMessage(event.data);
            }

            // Check for ping/pong
            if (this.isPingMessage(data)) {
                this.handlePing(connId, data);
                return;
            }

            // Process subscription responses
            if (this.isSubscriptionResponse(data)) {
                this.handleSubscriptionResponse(connId, data);
                return;
            }

            // Route to appropriate handler
            this.routeMessage(connId, data);

            // Emit message event
            this.emit('message', { connId, data });

        } catch (error) {
            console.error(`Error handling message from ${connId}:`, error);
            this.emit('error', { connId, error, rawData: event.data });
        }
    }

    /**
     * Subscribe to market data streams
     */
    subscribe(connId, channels, callback = null) {
        const ws = this.connections.get(connId);
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            // Queue subscription for when connected
            this.queueMessage(connId, { action: 'subscribe', channels, callback });
            return;
        }

        // Store subscription
        if (!this.subscriptions.has(connId)) {
            this.subscriptions.set(connId, new Set());
        }
        
        channels.forEach(channel => {
            this.subscriptions.get(connId).add(channel);
            if (callback) {
                this.callbacks.set(`${connId}_${channel}`, callback);
            }
        });

        // Format subscription message based on exchange
        const [exchangeId] = connId.split('_');
        const message = this.formatSubscriptionMessage(exchangeId, channels);

        // Send subscription
        this.send(connId, message);
    }

    /**
     * Unsubscribe from channels
     */
    unsubscribe(connId, channels) {
        const ws = this.connections.get(connId);
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            return;
        }

        // Remove from subscriptions
        const subs = this.subscriptions.get(connId);
        if (subs) {
            channels.forEach(channel => {
                subs.delete(channel);
                this.callbacks.delete(`${connId}_${channel}`);
            });
        }

        // Format unsubscription message
        const [exchangeId] = connId.split('_');
        const message = this.formatUnsubscriptionMessage(exchangeId, channels);

        // Send unsubscription
        this.send(connId, message);
    }

    /**
     * Send message through WebSocket
     */
    send(connId, message) {
        const ws = this.connections.get(connId);
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            this.queueMessage(connId, message);
            return false;
        }

        try {
            const data = typeof message === 'string' ? message : JSON.stringify(message);
            ws.send(data);
            
            // Update metrics
            this.metrics.messagesSent++;
            this.metrics.bytesSent += data.length;
            
            return true;
        } catch (error) {
            console.error(`Failed to send message on ${connId}:`, error);
            this.emit('error', { connId, error, message });
            return false;
        }
    }

    /**
     * Format subscription message based on exchange
     */
    formatSubscriptionMessage(exchangeId, channels) {
        switch (exchangeId) {
            case 'binance':
                return {
                    method: 'SUBSCRIBE',
                    params: channels,
                    id: Date.now()
                };
            
            case 'coinbase':
                return {
                    type: 'subscribe',
                    channels: channels.map(ch => ({
                        name: ch.split('@')[0],
                        product_ids: [ch.split('@')[1]]
                    }))
                };
            
            case 'kraken':
                return {
                    event: 'subscribe',
                    pair: channels.map(ch => ch.split('@')[1]),
                    subscription: { name: channels[0].split('@')[0] }
                };
            
            case 'bybit':
                return {
                    op: 'subscribe',
                    args: channels
                };
            
            case 'okx':
                return {
                    op: 'subscribe',
                    args: channels.map(ch => ({ channel: ch }))
                };
            
            default:
                return { subscribe: channels };
        }
    }

    /**
     * Handle disconnection and auto-reconnect
     */
    handleDisconnection(connId, event) {
        // Clear heartbeat
        this.stopHeartbeat(connId);
        
        // Update state
        this.connectionStates.set(connId, 'disconnected');
        this.connections.delete(connId);

        // Check if should reconnect
        if (event.code !== 1000 && event.code !== 1001) {
            // Abnormal closure, attempt reconnect
            this.scheduleReconnect(connId);
        }

        // Emit disconnected event
        this.emit('disconnected', { connId, code: event.code, reason: event.reason });
    }

    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect(connId) {
        const attempts = this.reconnectAttempts.get(connId) || 0;
        const delay = Math.min(
            this.config.reconnectDelay * Math.pow(this.config.reconnectDecay, attempts),
            this.config.maxReconnectDelay
        );

        console.log(`Scheduling reconnect for ${connId} in ${delay}ms (attempt ${attempts + 1})`);
        
        setTimeout(() => {
            if (this.connectionStates.get(connId) !== 'connected') {
                this.reconnectAttempts.set(connId, attempts + 1);
                const [exchangeId, endpoint] = connId.split('_');
                this.connect(exchangeId, endpoint);
            }
        }, delay);
    }

    /**
     * Start heartbeat/ping mechanism
     */
    startHeartbeat(connId) {
        const timer = setInterval(() => {
            const ws = this.connections.get(connId);
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Send ping based on exchange format
                const [exchangeId] = connId.split('_');
                const pingMessage = this.formatPingMessage(exchangeId);
                this.send(connId, pingMessage);
                
                // Check for stale connection
                const lastMessage = this.lastMessageTimes.get(connId) || Date.now();
                if (Date.now() - lastMessage > this.config.heartbeatInterval * 2) {
                    console.warn(`Connection ${connId} appears stale, reconnecting...`);
                    ws.close();
                }
            }
        }, this.config.heartbeatInterval);

        this.heartbeatTimers.set(connId, timer);
    }

    /**
     * Stop heartbeat timer
     */
    stopHeartbeat(connId) {
        const timer = this.heartbeatTimers.get(connId);
        if (timer) {
            clearInterval(timer);
            this.heartbeatTimers.delete(connId);
        }
    }

    /**
     * Get connection statistics
     */
    getStatistics() {
        const stats = {
            connections: {},
            metrics: this.metrics,
            subscriptions: {}
        };

        this.connections.forEach((ws, connId) => {
            stats.connections[connId] = {
                state: this.connectionStates.get(connId),
                readyState: ws.readyState,
                uptime: Date.now() - (this.metrics.connectionUptime.get(connId) || 0),
                lastMessage: this.lastMessageTimes.get(connId),
                reconnectAttempts: this.reconnectAttempts.get(connId) || 0
            };
        });

        this.subscriptions.forEach((subs, connId) => {
            stats.subscriptions[connId] = Array.from(subs);
        });

        return stats;
    }

    /**
     * Disconnect from exchange
     */
    disconnect(connId = null) {
        if (connId) {
            const ws = this.connections.get(connId);
            if (ws) {
                ws.close(1000, 'Normal closure');
                this.connections.delete(connId);
                this.stopHeartbeat(connId);
            }
        } else {
            // Disconnect all
            this.connections.forEach((ws, id) => {
                ws.close(1000, 'Normal closure');
                this.stopHeartbeat(id);
            });
            this.connections.clear();
        }
    }

    /**
     * Event emitter methods
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }

    off(event, handler) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.delete(handler);
        }
    }

    emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Queue message for later sending
     */
    queueMessage(connId, message) {
        this.messageQueue.push({ connId, message, timestamp: Date.now() });
        
        // Trim queue if too large
        if (this.messageQueue.length > this.config.messageQueueSize) {
            this.messageQueue.shift();
        }
    }

    /**
     * Process queued messages
     */
    processMessageQueue(connId) {
        const messages = this.messageQueue.filter(m => m.connId === connId);
        messages.forEach(({ message }) => {
            if (message.action === 'subscribe') {
                this.subscribe(connId, message.channels, message.callback);
            } else {
                this.send(connId, message);
            }
        });
        
        // Remove processed messages
        this.messageQueue = this.messageQueue.filter(m => m.connId !== connId);
    }

    /**
     * Resubscribe to channels after reconnection
     */
    resubscribe(connId) {
        const subs = this.subscriptions.get(connId);
        if (subs && subs.size > 0) {
            const channels = Array.from(subs);
            console.log(`Resubscribing to ${channels.length} channels on ${connId}`);
            
            // Clear and resubscribe
            subs.clear();
            this.subscribe(connId, channels);
        }
    }

    /**
     * Wait for connection to be established
     */
    waitForConnection(connId, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const checkInterval = 100;
            let elapsed = 0;
            
            const check = () => {
                const state = this.connectionStates.get(connId);
                if (state === 'connected') {
                    resolve();
                } else if (state === 'error' || elapsed >= timeout) {
                    reject(new Error(`Connection timeout for ${connId}`));
                } else {
                    elapsed += checkInterval;
                    setTimeout(check, checkInterval);
                }
            };
            
            check();
        });
    }

    /**
     * Get exchange WebSocket URL
     */
    getExchangeUrl(exchangeId, endpoint) {
        const exchange = this.exchanges[exchangeId];
        if (!exchange) return null;
        return exchange[endpoint] || exchange.main || exchange.public;
    }

    /**
     * Check if message is ping
     */
    isPingMessage(data) {
        return data.ping || data.event === 'ping' || data.type === 'ping';
    }

    /**
     * Handle ping message
     */
    handlePing(connId, data) {
        const [exchangeId] = connId.split('_');
        let pongMessage;

        switch (exchangeId) {
            case 'binance':
                if (data.ping) {
                    pongMessage = { pong: data.ping };
                }
                break;
            case 'okx':
                if (data.op === 'ping') {
                    pongMessage = { op: 'pong' };
                }
                break;
            default:
                pongMessage = { pong: Date.now() };
        }

        if (pongMessage) {
            this.send(connId, pongMessage);
        }
    }

    /**
     * Format ping message based on exchange
     */
    formatPingMessage(exchangeId) {
        switch (exchangeId) {
            case 'binance':
                return { ping: Date.now() };
            case 'okx':
                return { op: 'ping' };
            case 'bybit':
                return { op: 'ping' };
            default:
                return { type: 'ping' };
        }
    }

    /**
     * Check if message is subscription response
     */
    isSubscriptionResponse(data) {
        return data.result !== undefined || 
               data.event === 'subscribe' || 
               data.type === 'subscriptions' ||
               data.success !== undefined;
    }

    /**
     * Handle subscription response
     */
    handleSubscriptionResponse(connId, data) {
        console.log(`Subscription response on ${connId}:`, data);
        this.emit('subscription', { connId, data });
    }

    /**
     * Route message to appropriate handler
     */
    routeMessage(connId, data) {
        // Check for channel-specific callback
        const channel = this.extractChannel(data);
        if (channel) {
            const callback = this.callbacks.get(`${connId}_${channel}`);
            if (callback) {
                callback(data);
            }
        }

        // Emit channel-specific event
        if (channel) {
            this.emit(`data:${channel}`, data);
        }

        // Emit exchange-specific event
        const [exchangeId] = connId.split('_');
        this.emit(`data:${exchangeId}`, data);
    }

    /**
     * Extract channel from message
     */
    extractChannel(data) {
        // Try different formats
        return data.stream || data.channel || data.topic || data.subject || null;
    }

    /**
     * Handle network change
     */
    handleNetworkChange(online) {
        console.log(`Network status changed: ${online ? 'online' : 'offline'}`);
        
        if (online) {
            // Reconnect all disconnected connections
            this.connectionStates.forEach((state, connId) => {
                if (state === 'disconnected' || state === 'error') {
                    const [exchangeId, endpoint] = connId.split('_');
                    this.connect(exchangeId, endpoint);
                }
            });
        }
    }

    /**
     * Start metrics collection
     */
    startMetricsCollection() {
        setInterval(() => {
            // Calculate average latency
            this.connections.forEach((ws, connId) => {
                if (ws.readyState === WebSocket.OPEN) {
                    const start = Date.now();
                    const [exchangeId] = connId.split('_');
                    const pingMessage = this.formatPingMessage(exchangeId);
                    
                    // Measure round-trip time
                    this.send(connId, pingMessage);
                    // Note: Actual latency calculation would need response tracking
                }
            });

            // Emit metrics event
            this.emit('metrics', this.getStatistics());
        }, 10000); // Every 10 seconds
    }

    /**
     * Decode binary message (for exchanges that use binary protocol)
     */
    decodeBinaryMessage(data) {
        // Implementation would depend on specific exchange protocol
        // This is a placeholder for binary message handling
        return { binary: true, data: Array.from(new Uint8Array(data)) };
    }

    /**
     * Format unsubscription message
     */
    formatUnsubscriptionMessage(exchangeId, channels) {
        switch (exchangeId) {
            case 'binance':
                return {
                    method: 'UNSUBSCRIBE',
                    params: channels,
                    id: Date.now()
                };
            
            case 'coinbase':
                return {
                    type: 'unsubscribe',
                    channels: channels.map(ch => ({
                        name: ch.split('@')[0],
                        product_ids: [ch.split('@')[1]]
                    }))
                };
            
            case 'bybit':
                return {
                    op: 'unsubscribe',
                    args: channels
                };
            
            default:
                return { unsubscribe: channels };
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuraQuantWebSocketManager;
}
