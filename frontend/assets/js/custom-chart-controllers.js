/**
 * AuraQuant Custom Chart Controllers
 * Ultra-sophisticated Chart.js extensions for advanced trading visualizations
 */

// Import Chart.js if available
const Chart = window.Chart || {};

/**
 * Volume Profile Chart Controller
 * Shows volume distribution at different price levels
 */
class VolumeProfileController extends Chart.DatasetController {
    static id = 'volumeProfile';
    static defaults = {
        datasetElementType: false,
        dataElementType: 'bar',
        animations: {
            numbers: {
                type: 'number',
                properties: ['x', 'y', 'width', 'height', 'volumeWidth']
            }
        },
        scales: {
            x: {
                type: 'linear',
                position: 'bottom'
            },
            y: {
                type: 'linear',
                position: 'left'
            }
        }
    };

    constructor(chart, datasetIndex) {
        super(chart, datasetIndex);
        this.volumeBars = [];
        this.pocLine = null; // Point of Control
        this.valueAreas = [];
        this.colors = {
            buy: '#00ff88',
            sell: '#ff00ff',
            poc: '#00ffff',
            valueArea: 'rgba(0, 255, 255, 0.1)',
            grid: 'rgba(255, 255, 255, 0.05)'
        };
    }

    update(mode) {
        const meta = this._cachedMeta;
        const dataset = this.getDataset();
        const data = dataset.data || [];
        
        // Calculate volume profile
        const profile = this.calculateVolumeProfile(data);
        
        // Update elements
        this.updateVolumeElements(profile, mode);
        
        // Draw POC and value areas
        this.updatePOCandValueAreas(profile);
        
        super.update(mode);
    }

    calculateVolumeProfile(data) {
        const priceLevels = new Map();
        const binSize = this.options.binSize || 0.01;
        
        data.forEach(trade => {
            const price = Math.round(trade.price / binSize) * binSize;
            const current = priceLevels.get(price) || { buy: 0, sell: 0, total: 0 };
            
            if (trade.side === 'buy') {
                current.buy += trade.volume;
            } else {
                current.sell += trade.volume;
            }
            current.total += trade.volume;
            
            priceLevels.set(price, current);
        });
        
        // Find POC (Point of Control)
        let poc = null;
        let maxVolume = 0;
        priceLevels.forEach((volume, price) => {
            if (volume.total > maxVolume) {
                maxVolume = volume.total;
                poc = price;
            }
        });
        
        // Calculate value areas (70% of volume)
        const sortedLevels = Array.from(priceLevels.entries())
            .sort((a, b) => b[1].total - a[1].total);
        
        let cumulativeVolume = 0;
        const totalVolume = sortedLevels.reduce((sum, [, vol]) => sum + vol.total, 0);
        const valueAreaTarget = totalVolume * 0.7;
        const valueAreaLevels = [];
        
        for (const [price, volume] of sortedLevels) {
            cumulativeVolume += volume.total;
            valueAreaLevels.push(price);
            if (cumulativeVolume >= valueAreaTarget) break;
        }
        
        return {
            levels: priceLevels,
            poc,
            valueAreaHigh: Math.max(...valueAreaLevels),
            valueAreaLow: Math.min(...valueAreaLevels),
            maxVolume
        };
    }

    updateVolumeElements(profile, mode) {
        const { ctx, chartArea } = this.chart;
        const xScale = this._cachedMeta.xScale;
        const yScale = this._cachedMeta.yScale;
        
        ctx.save();
        
        profile.levels.forEach((volume, price) => {
            const y = yScale.getPixelForValue(price);
            const barWidth = (volume.total / profile.maxVolume) * (chartArea.width * 0.3);
            const buyWidth = (volume.buy / volume.total) * barWidth;
            
            // Draw buy volume
            ctx.fillStyle = this.colors.buy;
            ctx.globalAlpha = 0.7;
            ctx.fillRect(chartArea.right - barWidth, y - 1, buyWidth, 2);
            
            // Draw sell volume
            ctx.fillStyle = this.colors.sell;
            ctx.fillRect(chartArea.right - barWidth + buyWidth, y - 1, barWidth - buyWidth, 2);
        });
        
        ctx.restore();
    }

    updatePOCandValueAreas(profile) {
        const { ctx, chartArea } = this.chart;
        const yScale = this._cachedMeta.yScale;
        
        ctx.save();
        
        // Draw POC line
        if (profile.poc !== null) {
            const pocY = yScale.getPixelForValue(profile.poc);
            ctx.strokeStyle = this.colors.poc;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(chartArea.left, pocY);
            ctx.lineTo(chartArea.right, pocY);
            ctx.stroke();
        }
        
        // Draw value area
        const vahY = yScale.getPixelForValue(profile.valueAreaHigh);
        const valY = yScale.getPixelForValue(profile.valueAreaLow);
        ctx.fillStyle = this.colors.valueArea;
        ctx.fillRect(chartArea.left, vahY, chartArea.width, valY - vahY);
        
        ctx.restore();
    }

    draw() {
        const meta = this._cachedMeta;
        const { ctx } = this.chart;
        
        // Draw grid
        this.drawGrid();
        
        // Call parent draw
        super.draw();
        
        // Draw overlays
        this.drawOverlays();
    }

    drawGrid() {
        const { ctx, chartArea } = this.chart;
        const yScale = this._cachedMeta.yScale;
        
        ctx.save();
        ctx.strokeStyle = this.colors.grid;
        ctx.lineWidth = 0.5;
        
        // Draw horizontal grid lines
        const ticks = yScale.ticks;
        ticks.forEach(tick => {
            const y = yScale.getPixelForValue(tick.value);
            ctx.beginPath();
            ctx.moveTo(chartArea.left, y);
            ctx.lineTo(chartArea.right, y);
            ctx.stroke();
        });
        
        ctx.restore();
    }

    drawOverlays() {
        // Custom overlays like session boundaries, important levels, etc.
    }
}

/**
 * Heatmap Chart Controller
 * Multi-dimensional data visualization with color intensity
 */
class HeatmapController extends Chart.DatasetController {
    static id = 'heatmap';
    static defaults = {
        datasetElementType: false,
        dataElementType: 'rectangle',
        animations: {
            numbers: {
                type: 'number',
                properties: ['x', 'y', 'width', 'height', 'colorValue']
            }
        }
    };

    constructor(chart, datasetIndex) {
        super(chart, datasetIndex);
        this.cells = [];
        this.colorScale = this.createColorScale();
    }

    createColorScale() {
        // Create gradient from platform colors
        return {
            min: '#000033',
            low: '#ff00ff',
            mid: '#00ffff',
            high: '#00ff88',
            max: '#ffffff'
        };
    }

    update(mode) {
        const dataset = this.getDataset();
        const data = dataset.data || [];
        
        // Process heatmap data
        const matrix = this.processHeatmapData(data);
        
        // Update cells
        this.updateCells(matrix, mode);
        
        super.update(mode);
    }

    processHeatmapData(data) {
        // Convert data to 2D matrix
        const matrix = [];
        const xValues = [...new Set(data.map(d => d.x))].sort((a, b) => a - b);
        const yValues = [...new Set(data.map(d => d.y))].sort((a, b) => a - b);
        
        // Find min/max for normalization
        let min = Infinity, max = -Infinity;
        data.forEach(d => {
            if (d.value < min) min = d.value;
            if (d.value > max) max = d.value;
        });
        
        // Create data map
        const dataMap = new Map();
        data.forEach(d => {
            dataMap.set(`${d.x},${d.y}`, d.value);
        });
        
        // Build matrix
        xValues.forEach((x, xi) => {
            matrix[xi] = [];
            yValues.forEach((y, yi) => {
                const value = dataMap.get(`${x},${y}`) || 0;
                matrix[xi][yi] = {
                    x,
                    y,
                    value,
                    normalized: (value - min) / (max - min)
                };
            });
        });
        
        return { matrix, xValues, yValues, min, max };
    }

    updateCells(processedData, mode) {
        const { ctx, chartArea } = this.chart;
        const { matrix, xValues, yValues } = processedData;
        const xScale = this._cachedMeta.xScale;
        const yScale = this._cachedMeta.yScale;
        
        const cellWidth = chartArea.width / xValues.length;
        const cellHeight = chartArea.height / yValues.length;
        
        ctx.save();
        
        matrix.forEach((column, xi) => {
            column.forEach((cell, yi) => {
                const x = xScale.getPixelForValue(cell.x) - cellWidth / 2;
                const y = yScale.getPixelForValue(cell.y) - cellHeight / 2;
                
                // Get color based on value
                const color = this.getColorForValue(cell.normalized);
                
                // Draw cell
                ctx.fillStyle = color;
                ctx.fillRect(x, y, cellWidth, cellHeight);
                
                // Optional: draw cell border
                if (this.options.showBorder) {
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
                    ctx.lineWidth = 0.5;
                    ctx.strokeRect(x, y, cellWidth, cellHeight);
                }
            });
        });
        
        ctx.restore();
    }

    getColorForValue(normalized) {
        // Interpolate between color scale points
        if (normalized <= 0.25) {
            return this.interpolateColor(this.colorScale.min, this.colorScale.low, normalized * 4);
        } else if (normalized <= 0.5) {
            return this.interpolateColor(this.colorScale.low, this.colorScale.mid, (normalized - 0.25) * 4);
        } else if (normalized <= 0.75) {
            return this.interpolateColor(this.colorScale.mid, this.colorScale.high, (normalized - 0.5) * 4);
        } else {
            return this.interpolateColor(this.colorScale.high, this.colorScale.max, (normalized - 0.75) * 4);
        }
    }

    interpolateColor(color1, color2, factor) {
        // Simple color interpolation
        const c1 = this.hexToRgb(color1);
        const c2 = this.hexToRgb(color2);
        
        const r = Math.round(c1.r + (c2.r - c1.r) * factor);
        const g = Math.round(c1.g + (c2.g - c1.g) * factor);
        const b = Math.round(c1.b + (c2.b - c1.b) * factor);
        
        return `rgb(${r}, ${g}, ${b})`;
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    draw() {
        super.draw();
        
        // Draw color legend
        if (this.options.showLegend) {
            this.drawColorLegend();
        }
    }

    drawColorLegend() {
        const { ctx, chartArea } = this.chart;
        const legendWidth = 20;
        const legendHeight = chartArea.height;
        const x = chartArea.right + 10;
        const y = chartArea.top;
        
        ctx.save();
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, y, 0, y + legendHeight);
        gradient.addColorStop(0, this.colorScale.max);
        gradient.addColorStop(0.25, this.colorScale.high);
        gradient.addColorStop(0.5, this.colorScale.mid);
        gradient.addColorStop(0.75, this.colorScale.low);
        gradient.addColorStop(1, this.colorScale.min);
        
        // Draw gradient rectangle
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, legendWidth, legendHeight);
        
        // Draw border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, legendWidth, legendHeight);
        
        ctx.restore();
    }
}

/**
 * Order Flow Chart Controller
 * Visualizes order flow and market microstructure
 */
class OrderFlowController extends Chart.BubbleController {
    static id = 'orderFlow';
    static defaults = {
        datasetElementType: false,
        dataElementType: 'circle',
        animations: {
            numbers: {
                type: 'number',
                properties: ['x', 'y', 'r', 'opacity']
            }
        }
    };

    constructor(chart, datasetIndex) {
        super(chart, datasetIndex);
        this.bubbles = [];
        this.footprint = [];
        this.colors = {
            buy: '#00ff88',
            sell: '#ff00ff',
            aggressive: '#00ffff',
            passive: '#ffaa00',
            large: '#ffffff'
        };
        this.particles = [];
    }

    update(mode) {
        const dataset = this.getDataset();
        const data = dataset.data || [];
        
        // Process order flow data
        const processed = this.processOrderFlow(data);
        
        // Update bubbles
        this.updateBubbles(processed, mode);
        
        // Update footprint
        this.updateFootprint(processed);
        
        // Update particles for executed orders
        this.updateParticles(processed);
        
        super.update(mode);
    }

    processOrderFlow(data) {
        const orders = [];
        const footprint = new Map();
        const executions = [];
        
        data.forEach(order => {
            // Categorize order
            const category = this.categorizeOrder(order);
            
            orders.push({
                ...order,
                category,
                radius: this.calculateRadius(order.size),
                color: this.getOrderColor(order, category)
            });
            
            // Build footprint
            const priceLevel = Math.round(order.price * 100) / 100;
            const fp = footprint.get(priceLevel) || { bid: 0, ask: 0, delta: 0 };
            
            if (order.side === 'buy') {
                fp.bid += order.size;
                fp.delta += order.size;
            } else {
                fp.ask += order.size;
                fp.delta -= order.size;
            }
            
            footprint.set(priceLevel, fp);
            
            // Track executions for particle effects
            if (order.executed) {
                executions.push(order);
            }
        });
        
        return { orders, footprint, executions };
    }

    categorizeOrder(order) {
        if (order.size > 1000000) return 'whale';
        if (order.aggressive) return 'aggressive';
        if (order.passive) return 'passive';
        return 'normal';
    }

    calculateRadius(size) {
        // Logarithmic scale for bubble radius
        const minRadius = 2;
        const maxRadius = 30;
        const logSize = Math.log10(size + 1);
        const maxLogSize = Math.log10(10000000);
        
        return minRadius + (maxRadius - minRadius) * (logSize / maxLogSize);
    }

    getOrderColor(order, category) {
        if (category === 'whale') return this.colors.large;
        if (category === 'aggressive') return this.colors.aggressive;
        if (order.side === 'buy') return this.colors.buy;
        return this.colors.sell;
    }

    updateBubbles(processed, mode) {
        const { ctx, chartArea } = this.chart;
        const xScale = this._cachedMeta.xScale;
        const yScale = this._cachedMeta.yScale;
        
        ctx.save();
        
        processed.orders.forEach(order => {
            const x = xScale.getPixelForValue(order.time);
            const y = yScale.getPixelForValue(order.price);
            
            // Draw bubble
            ctx.globalAlpha = 0.6;
            ctx.fillStyle = order.color;
            ctx.beginPath();
            ctx.arc(x, y, order.radius, 0, Math.PI * 2);
            ctx.fill();
            
            // Draw bubble border for large orders
            if (order.category === 'whale') {
                ctx.strokeStyle = this.colors.large;
                ctx.lineWidth = 2;
                ctx.globalAlpha = 1;
                ctx.stroke();
            }
        });
        
        ctx.restore();
    }

    updateFootprint(processed) {
        const { ctx, chartArea } = this.chart;
        const yScale = this._cachedMeta.yScale;
        
        ctx.save();
        ctx.font = '10px monospace';
        
        processed.footprint.forEach((fp, price) => {
            const y = yScale.getPixelForValue(price);
            const x = chartArea.right - 100;
            
            // Draw bid/ask imbalance
            const imbalance = fp.bid / (fp.bid + fp.ask);
            const barWidth = 80;
            
            // Background bar
            ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.fillRect(x, y - 5, barWidth, 10);
            
            // Imbalance bar
            const bidWidth = barWidth * imbalance;
            ctx.fillStyle = this.colors.buy;
            ctx.globalAlpha = 0.7;
            ctx.fillRect(x, y - 5, bidWidth, 10);
            
            ctx.fillStyle = this.colors.sell;
            ctx.fillRect(x + bidWidth, y - 5, barWidth - bidWidth, 10);
            
            // Delta text
            ctx.globalAlpha = 1;
            ctx.fillStyle = fp.delta > 0 ? this.colors.buy : this.colors.sell;
            ctx.textAlign = 'right';
            ctx.fillText(fp.delta.toFixed(0), x - 5, y + 3);
        });
        
        ctx.restore();
    }

    updateParticles(processed) {
        // Create particle effects for executed orders
        processed.executions.forEach(execution => {
            this.createParticleEffect(execution);
        });
        
        // Update existing particles
        this.particles = this.particles.filter(particle => {
            particle.life -= 0.02;
            particle.y -= particle.velocity;
            particle.velocity *= 0.98;
            
            return particle.life > 0;
        });
    }

    createParticleEffect(execution) {
        const xScale = this._cachedMeta.xScale;
        const yScale = this._cachedMeta.yScale;
        
        const x = xScale.getPixelForValue(execution.time);
        const y = yScale.getPixelForValue(execution.price);
        
        // Create multiple particles
        for (let i = 0; i < 10; i++) {
            this.particles.push({
                x: x + (Math.random() - 0.5) * 20,
                y: y,
                velocity: Math.random() * 2 + 1,
                life: 1,
                color: execution.side === 'buy' ? this.colors.buy : this.colors.sell,
                size: Math.random() * 3 + 1
            });
        }
    }

    draw() {
        super.draw();
        
        // Draw particles
        this.drawParticles();
        
        // Draw order flow indicators
        this.drawOrderFlowIndicators();
    }

    drawParticles() {
        const { ctx } = this.chart;
        
        ctx.save();
        
        this.particles.forEach(particle => {
            ctx.globalAlpha = particle.life * 0.6;
            ctx.fillStyle = particle.color;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
        });
        
        ctx.restore();
    }

    drawOrderFlowIndicators() {
        const { ctx, chartArea } = this.chart;
        
        // Draw cumulative delta
        this.drawCumulativeDelta();
        
        // Draw volume profile
        this.drawMiniVolumeProfile();
        
        // Draw order book depth
        this.drawOrderBookDepth();
    }

    drawCumulativeDelta() {
        // Implementation for cumulative delta visualization
    }

    drawMiniVolumeProfile() {
        // Implementation for mini volume profile
    }

    drawOrderBookDepth() {
        // Implementation for order book depth visualization
    }
}

/**
 * Register custom controllers with Chart.js
 */
if (Chart && Chart.register) {
    Chart.register(VolumeProfileController, HeatmapController, OrderFlowController);
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        VolumeProfileController,
        HeatmapController,
        OrderFlowController
    };
}
