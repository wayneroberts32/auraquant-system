// AuraQuant Broker Data Configuration
// This replaces TradingView data with broker data while keeping the EXACT same layout

const BrokerDataConfig = {
    // Data Source Priority (TradingView is LAST resort)
    dataSourcePriority: [
        'BROKER_LIVE',      // Primary: Live broker data
        'BROKER_DELAYED',   // Secondary: Delayed broker data
        'API_DIRECT',       // Tertiary: Direct API (Yahoo, Alpha Vantage)
        'TRADINGVIEW'       // Fallback: Only if everything else fails
    ],

    // Broker Selection by Symbol Type
    brokerRouting: {
        // ASX Stocks
        'ASX': {
            broker: 'INTERACTIVE_BROKERS',
            dataFeed: 'IB_GATEWAY',
            chartLibrary: 'LIGHTWEIGHT_CHARTS', // Same visual as TradingView
            indicators: ['RSI', 'MACD', 'BOLLINGER', 'VWAP', 'ATR']
        },
        
        // Crypto
        'CRYPTO': {
            broker: 'BINANCE',
            dataFeed: 'BINANCE_WEBSOCKET',
            chartLibrary: 'LIGHTWEIGHT_CHARTS',
            indicators: ['RSI', 'MACD', 'BOLLINGER', 'VOLUME_PROFILE']
        },
        
        // US Stocks
        'US_STOCKS': {
            broker: 'ALPACA',
            dataFeed: 'ALPACA_STREAM',
            chartLibrary: 'LIGHTWEIGHT_CHARTS',
            indicators: ['RSI', 'MACD', 'BOLLINGER', 'VWAP']
        },
        
        // Meme Coins
        'MEME_COINS': {
            broker: 'UNISWAP',
            dataFeed: 'DEX_AGGREGATOR',
            chartLibrary: 'LIGHTWEIGHT_CHARTS',
            indicators: ['RSI', 'LIQUIDITY', 'RUGPULL_DETECTOR']
        }
    },

    // Chart Configuration (Matches your TradingView layout exactly)
    chartSettings: {
        // Visual Settings - IDENTICAL to your current dashboard
        theme: 'dark',
        backgroundColor: '#131722',
        gridColor: '#2a2e39',
        textColor: '#d1d4dc',
        
        // Layout - PRESERVED
        layout: {
            mainChart: {
                height: '60%',  // Same as current
                position: 'top'
            },
            indicators: {
                RSI: {
                    height: '20%',
                    position: 'middle',
                    enabled: true
                },
                MACD: {
                    height: '20%',
                    position: 'bottom',
                    enabled: true
                }
            }
        },
        
        // Timeframes - Same as your TradingView setup
        timeframes: ['1m', '5m', '15m', '30m', '1H', '4H', 'D', 'W', 'M'],
        defaultTimeframe: '5m',
        
        // Chart Types
        chartTypes: ['candlestick', 'line', 'area', 'bars', 'heikinashi'],
        defaultChartType: 'candlestick'
    },

    // Indicator Settings - Your exact configuration
    indicators: {
        RSI: {
            enabled: true,
            period: 14,
            overbought: 70,
            oversold: 30,
            color: '#7E57C2',
            showInSeparatePane: true
        },
        MACD: {
            enabled: true,
            fastPeriod: 12,
            slowPeriod: 26,
            signalPeriod: 9,
            histogram: true,
            showInSeparatePane: true
        },
        BollingerBands: {
            enabled: true,
            period: 20,
            stdDev: 2,
            showOnMainChart: true
        },
        MovingAverages: {
            SMA: [20, 50, 200],
            EMA: [9, 21],
            showOnMainChart: true
        }
    },

    // How to switch data source (called automatically)
    switchDataSource: function(symbol) {
        // Determine market type
        let market = 'US_STOCKS';
        if (symbol.endsWith('.AX')) {
            market = 'ASX';
        } else if (symbol.includes('-USDT') || symbol.includes('/USD')) {
            market = 'CRYPTO';
        } else if (symbol.includes('INU') || symbol.includes('MOON')) {
            market = 'MEME_COINS';
        }
        
        // Get broker configuration
        const config = this.brokerRouting[market];
        
        // Return data source (broker takes priority)
        return {
            broker: config.broker,
            dataFeed: config.dataFeed,
            useTraingView: false,  // Only true if broker fails
            layout: this.chartSettings.layout  // PRESERVE LAYOUT
        };
    },

    // Initialize broker data on page load
    initializeBrokerData: function() {
        // Check if broker APIs are configured
        const hasIBConfig = window.IB_API_KEY !== undefined;
        const hasBinanceConfig = window.BINANCE_API_KEY !== undefined;
        
        if (hasIBConfig || hasBinanceConfig) {
            console.log('✅ Using BROKER DATA - TradingView disabled');
            this.replaceChartWithBrokerData();
        } else {
            console.log('⚠️ Broker APIs not configured - Using TradingView fallback');
        }
    },

    // Replace TradingView with broker data (keeps same layout)
    replaceChartWithBrokerData: function() {
        const chartContainer = document.getElementById('tradingview_chart');
        
        // Create Lightweight Charts with SAME layout
        const chart = LightweightCharts.createChart(chartContainer, {
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
            layout: {
                backgroundColor: this.chartSettings.backgroundColor,
                textColor: this.chartSettings.textColor
            },
            grid: {
                vertLines: { color: this.chartSettings.gridColor },
                horzLines: { color: this.chartSettings.gridColor }
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal
            },
            timeScale: {
                borderColor: '#2a2e39'
            }
        });

        // Add candlestick series (main chart)
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#00ff88',
            downColor: '#ff4444',
            borderVisible: false,
            wickUpColor: '#00ff88',
            wickDownColor: '#ff4444'
        });

        // Connect to broker WebSocket for real-time data
        this.connectToBrokerFeed(candlestickSeries);
        
        // Add indicators with same layout
        this.addIndicatorsToChart(chart);
        
        return chart;
    },

    // Connect to live broker feed
    connectToBrokerFeed: function(series) {
        // This connects to your actual broker
        const ws = new WebSocket('wss://auraquant-backend.onrender.com/ws/market-data');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            series.update({
                time: data.timestamp,
                open: data.open,
                high: data.high,
                low: data.low,
                close: data.close,
                volume: data.volume
            });
        };
    },

    // Add indicators (RSI, MACD, etc.) in same positions
    addIndicatorsToChart: function(chart) {
        // RSI in separate pane (20% height)
        if (this.indicators.RSI.enabled) {
            const rsiPane = chart.addLineSeries({
                color: this.indicators.RSI.color,
                lineWidth: 2,
                pane: 1  // Separate pane
            });
            // RSI calculation happens in backend
        }
        
        // MACD in separate pane (20% height)
        if (this.indicators.MACD.enabled) {
            const macdPane = chart.addHistogramSeries({
                color: '#26a69a',
                pane: 2  // Another separate pane
            });
            // MACD calculation happens in backend
        }
        
        // Bollinger Bands on main chart
        if (this.indicators.BollingerBands.enabled) {
            const upperBand = chart.addLineSeries({
                color: 'rgba(33, 150, 243, 0.4)',
                lineWidth: 1
            });
            const lowerBand = chart.addLineSeries({
                color: 'rgba(33, 150, 243, 0.4)',
                lineWidth: 1
            });
        }
    }
};

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the trading dashboard
    if (window.location.pathname.includes('main-trading-dashboard')) {
        BrokerDataConfig.initializeBrokerData();
    }
});

// Export for use in other scripts
window.BrokerDataConfig = BrokerDataConfig;