/**
 * Paper Trading Configuration
 * Manages paper trading balance and reset functionality
 */

class PaperTradingManager {
    constructor() {
        this.STORAGE_KEY = 'auraquant_paper_balance';
        this.DEFAULT_BALANCE = 500.00; // $500 AUD default
        this.CURRENCY = 'AUD';
        this.MIN_BALANCE = 500.00; // Minimum required to trade
        
        // Initialize or load balance
        this.loadBalance();
    }
    
    /**
     * Load balance from localStorage or set default
     */
    loadBalance() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            try {
                const data = JSON.parse(stored);
                this.balance = data.balance || this.DEFAULT_BALANCE;
                this.lastReset = data.lastReset || new Date().toISOString();
            } catch (e) {
                this.resetBalance();
            }
        } else {
            this.resetBalance();
        }
    }
    
    /**
     * Save balance to localStorage
     */
    saveBalance() {
        const data = {
            balance: this.balance,
            lastReset: this.lastReset,
            currency: this.CURRENCY,
            timestamp: new Date().toISOString()
        };
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
        this.notifyBalanceChange();
    }
    
    /**
     * Reset balance to default $500 AUD
     */
    resetBalance(amount = null) {
        this.balance = amount || this.DEFAULT_BALANCE;
        this.lastReset = new Date().toISOString();
        this.saveBalance();
        
        // Show notification
        this.showNotification(`Paper trading balance reset to $${this.balance.toFixed(2)} ${this.CURRENCY}`, 'success');
        
        // Log the reset
        console.log(`✅ Paper balance reset to $${this.balance} ${this.CURRENCY}`);
        
        return this.balance;
    }
    
    /**
     * Get current balance
     */
    getBalance() {
        return {
            amount: this.balance,
            currency: this.CURRENCY,
            formatted: this.formatBalance(),
            canTrade: this.balance >= this.MIN_BALANCE,
            lastReset: this.lastReset
        };
    }
    
    /**
     * Update balance (after trade execution)
     */
    updateBalance(amount, type = 'trade') {
        const oldBalance = this.balance;
        this.balance += amount; // amount can be positive or negative
        
        // Ensure balance doesn't go below 0
        if (this.balance < 0) {
            this.balance = 0;
            this.showNotification('⚠️ Balance depleted! Reset to continue trading.', 'warning');
        }
        
        this.saveBalance();
        
        // Log the change
        const change = amount >= 0 ? `+$${Math.abs(amount).toFixed(2)}` : `-$${Math.abs(amount).toFixed(2)}`;
        console.log(`💰 Balance updated: $${oldBalance.toFixed(2)} → $${this.balance.toFixed(2)} (${change})`);
        
        // Check if trading should be blocked
        if (this.balance < this.MIN_BALANCE) {
            this.showNotification(`⚠️ Balance below minimum ($${this.MIN_BALANCE} ${this.CURRENCY}). Trading disabled.`, 'error');
            this.disableTrading();
        }
        
        return this.balance;
    }
    
    /**
     * Format balance for display
     */
    formatBalance() {
        return `$${this.balance.toFixed(2)} ${this.CURRENCY}`;
    }
    
    /**
     * Check if trading is allowed
     */
    canTrade() {
        return this.balance >= this.MIN_BALANCE;
    }
    
    /**
     * Disable trading UI
     */
    disableTrading() {
        // Disable buy/sell buttons
        const tradeButtons = document.querySelectorAll('.trade-btn, .buy-btn, .sell-btn');
        tradeButtons.forEach(btn => {
            btn.disabled = true;
            btn.title = `Minimum balance of $${this.MIN_BALANCE} ${this.CURRENCY} required`;
        });
        
        // Show warning banner
        const warningBanner = document.getElementById('low-balance-warning');
        if (warningBanner) {
            warningBanner.style.display = 'block';
            warningBanner.innerHTML = `
                <div class="alert alert-warning">
                    <strong>⚠️ Trading Disabled</strong> - 
                    Balance: ${this.formatBalance()} 
                    (Minimum: $${this.MIN_BALANCE} ${this.CURRENCY})
                    <button onclick="paperTrading.showResetDialog()" class="btn btn-sm btn-primary ml-3">
                        Reset Balance
                    </button>
                </div>
            `;
        }
    }
    
    /**
     * Enable trading UI
     */
    enableTrading() {
        const tradeButtons = document.querySelectorAll('.trade-btn, .buy-btn, .sell-btn');
        tradeButtons.forEach(btn => {
            btn.disabled = false;
            btn.title = '';
        });
        
        const warningBanner = document.getElementById('low-balance-warning');
        if (warningBanner) {
            warningBanner.style.display = 'none';
        }
    }
    
    /**
     * Show reset dialog
     */
    showResetDialog() {
        const dialog = `
            <div class="modal" id="reset-balance-modal">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5>Reset Paper Trading Balance</h5>
                        </div>
                        <div class="modal-body">
                            <p>Reset your paper trading balance to:</p>
                            <div class="form-group">
                                <label>Amount (${this.CURRENCY})</label>
                                <input type="number" id="reset-amount" class="form-control" 
                                       value="${this.DEFAULT_BALANCE}" min="500" step="100">
                                <small class="text-muted">Minimum: $500 ${this.CURRENCY}</small>
                            </div>
                            <p class="text-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                                This will reset your current balance and trading history.
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-secondary" onclick="paperTrading.closeResetDialog()">
                                Cancel
                            </button>
                            <button class="btn btn-primary" onclick="paperTrading.confirmReset()">
                                Reset Balance
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', dialog);
        document.getElementById('reset-balance-modal').style.display = 'block';
    }
    
    /**
     * Close reset dialog
     */
    closeResetDialog() {
        const modal = document.getElementById('reset-balance-modal');
        if (modal) {
            modal.remove();
        }
    }
    
    /**
     * Confirm balance reset
     */
    confirmReset() {
        const amountInput = document.getElementById('reset-amount');
        const amount = parseFloat(amountInput.value);
        
        if (amount < this.MIN_BALANCE) {
            alert(`Minimum balance is $${this.MIN_BALANCE} ${this.CURRENCY}`);
            return;
        }
        
        this.resetBalance(amount);
        this.closeResetDialog();
        
        // Re-enable trading if balance is sufficient
        if (amount >= this.MIN_BALANCE) {
            this.enableTrading();
        }
        
        // Refresh UI
        this.updateBalanceDisplay();
    }
    
    /**
     * Update balance display in UI
     */
    updateBalanceDisplay() {
        // Update all balance displays
        const balanceElements = document.querySelectorAll('.paper-balance, .balance-display, #paper-balance');
        balanceElements.forEach(el => {
            el.textContent = this.formatBalance();
            
            // Add color based on balance status
            if (this.balance < this.MIN_BALANCE) {
                el.classList.add('text-danger');
                el.classList.remove('text-success');
            } else {
                el.classList.add('text-success');
                el.classList.remove('text-danger');
            }
        });
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Check if notification container exists
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(container);
        }
        
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">&times;</button>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    /**
     * Notify balance change to other components
     */
    notifyBalanceChange() {
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('paperBalanceChanged', {
            detail: this.getBalance()
        }));
    }
    
    /**
     * Initialize paper trading UI components
     */
    initializeUI() {
        // Add reset button to UI if doesn't exist
        const resetBtn = document.getElementById('paper-reset-btn');
        if (!resetBtn) {
            const toolbar = document.querySelector('.trading-toolbar, .top-toolbar');
            if (toolbar) {
                const btn = document.createElement('button');
                btn.id = 'paper-reset-btn';
                btn.className = 'btn btn-outline-warning btn-sm';
                btn.innerHTML = '<i class="fas fa-redo"></i> Reset Balance';
                btn.onclick = () => this.showResetDialog();
                toolbar.appendChild(btn);
            }
        }
        
        // Update initial display
        this.updateBalanceDisplay();
        
        // Check if trading should be enabled
        if (this.canTrade()) {
            this.enableTrading();
        } else {
            this.disableTrading();
        }
    }
}

// Initialize paper trading manager
const paperTrading = new PaperTradingManager();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        paperTrading.initializeUI();
    });
} else {
    paperTrading.initializeUI();
}

// Export for use in other modules
window.PaperTradingManager = PaperTradingManager;
window.paperTrading = paperTrading;