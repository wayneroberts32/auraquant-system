/**
 * AuraQuant QA/QC Check Script
 * Verifies all required pages and integration
 */

const fs = require('fs').promises;
const path = require('path');

const FRONTEND_ROOT = 'D:\\New AuraQuant\\New_Synthetic_System_AuraQuant\\frontend';
const PAGES_DIR = path.join(FRONTEND_ROOT, 'pages');
const JS_DIR = path.join(FRONTEND_ROOT, 'assets', 'js');
const IMG_DIR = path.join(FRONTEND_ROOT, 'assets', 'img');

// Required pages from QA/QC list
const REQUIRED_PAGES = [
    'main-trading-dashboard.html',
    'login.html',
    'help-centre.html',
    'ai-workers-panel.html',
    'asx-paper-trading-launcher.html',
    'balance-control.html',
    'bot-status.html',
    'deployment-verification.html',
    'market-depth-demo.html',
    'performance-monitor.html',
    'pnl-dashboard.html',
    'unified-dashboard.html',
    'auraquant.html',
    // Additional required pages
    'brokers-banks.html',
    'manual-trade.html',
    'growth-selector.html',
    'tax-calculator.html',
    'fees-display.html',
    'heatmaps.html',
    'libraries.html'
];

// Required JS files
const REQUIRED_JS = [
    'workspace-manager.js',
    'menu-registry.js'
];

// QA/QC Check Results
const results = {
    timestamp: new Date().toISOString(),
    checks: [],
    passed: 0,
    failed: 0,
    warnings: 0
};

async function checkFile(filePath, description) {
    try {
        await fs.access(filePath);
        results.checks.push({
            check: description,
            path: filePath,
            status: 'PASS',
            message: 'File exists'
        });
        results.passed++;
        return true;
    } catch (error) {
        results.checks.push({
            check: description,
            path: filePath,
            status: 'FAIL',
            message: 'File not found'
        });
        results.failed++;
        return false;
    }
}

async function checkPages() {
    console.log('\n📄 Checking Required Pages...\n');
    
    for (const page of REQUIRED_PAGES) {
        const pagePath = path.join(PAGES_DIR, page);
        const exists = await checkFile(pagePath, `Page: ${page}`);
        
        if (exists) {
            console.log(`✅ ${page}`);
        } else {
            console.log(`❌ ${page} - MISSING`);
        }
    }
}

async function checkJSFiles() {
    console.log('\n📜 Checking JavaScript Files...\n');
    
    for (const jsFile of REQUIRED_JS) {
        const jsPath = path.join(JS_DIR, jsFile);
        const exists = await checkFile(jsPath, `JS: ${jsFile}`);
        
        if (exists) {
            console.log(`✅ ${jsFile}`);
        } else {
            console.log(`❌ ${jsFile} - MISSING`);
        }
    }
}

async function checkLogo() {
    console.log('\n🎨 Checking Logo...\n');
    
    const logoPath = path.join(IMG_DIR, 'logo-button.png');
    const exists = await checkFile(logoPath, 'Logo: logo-button.png');
    
    if (exists) {
        console.log('✅ Logo file present');
    } else {
        console.log('❌ Logo file missing');
        // Try alternate logo names
        const altLogos = ['logo.png', 'logo.jpg', 'logo.svg'];
        for (const alt of altLogos) {
            const altPath = path.join(IMG_DIR, alt);
            try {
                await fs.access(altPath);
                console.log(`⚠️ Found alternate logo: ${alt}`);
                results.warnings++;
                break;
            } catch {}
        }
    }
}

async function checkMainDashboard() {
    console.log('\n🏠 Checking Main Dashboard Integration...\n');
    
    const dashPath = path.join(PAGES_DIR, 'main-trading-dashboard.html');
    
    try {
        const content = await fs.readFile(dashPath, 'utf8');
        
        // Check for menu-registry.js inclusion
        if (content.includes('menu-registry.js')) {
            console.log('✅ Menu registry integrated');
            results.checks.push({
                check: 'Menu Registry Integration',
                status: 'PASS',
                message: 'menu-registry.js is included'
            });
            results.passed++;
        } else {
            console.log('⚠️ Menu registry not found in main dashboard');
            results.checks.push({
                check: 'Menu Registry Integration',
                status: 'WARNING',
                message: 'menu-registry.js not included in main dashboard'
            });
            results.warnings++;
        }
        
        // Check for single-tab workspace
        if (content.includes('workspace-manager.js') || content.includes('single-tab')) {
            console.log('✅ Single-tab workspace configured');
            results.checks.push({
                check: 'Single-tab Workspace',
                status: 'PASS'
            });
            results.passed++;
        }
        
    } catch (error) {
        console.log('❌ Could not check main dashboard integration');
        results.failed++;
    }
}

async function checkAdminGating() {
    console.log('\n🔒 Checking Admin Gating...\n');
    
    const adminPages = ['bot-status.html', 'deployment-verification.html', 'performance-monitor.html'];
    
    for (const page of adminPages) {
        const pagePath = path.join(PAGES_DIR, page);
        
        try {
            const content = await fs.readFile(pagePath, 'utf8');
            
            // Simple check for admin references
            if (content.includes('admin') || content.includes('Admin')) {
                console.log(`✅ ${page} - Has admin references`);
                results.checks.push({
                    check: `Admin Gating: ${page}`,
                    status: 'PASS'
                });
                results.passed++;
            } else {
                console.log(`⚠️ ${page} - No explicit admin checks found`);
                results.checks.push({
                    check: `Admin Gating: ${page}`,
                    status: 'WARNING'
                });
                results.warnings++;
            }
        } catch {
            // Page doesn't exist, already counted as failed
        }
    }
}

async function generateReport() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 QA/QC SUMMARY REPORT');
    console.log('='.repeat(60));
    
    const total = results.passed + results.failed + results.warnings;
    const passRate = total > 0 ? ((results.passed / total) * 100).toFixed(1) : 0;
    
    console.log(`\n✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`⚠️ Warnings: ${results.warnings}`);
    console.log(`📈 Pass Rate: ${passRate}%`);
    
    // Overall status
    let overallStatus = 'FAIL';
    if (results.failed === 0 && results.warnings <= 2) {
        overallStatus = 'PASS';
    } else if (results.failed === 0) {
        overallStatus = 'PASS WITH WARNINGS';
    }
    
    console.log(`\n🎯 Overall Status: ${overallStatus}`);
    
    // Write JSON report
    const reportPath = path.join(FRONTEND_ROOT, 'qa-qc-report.json');
    results.overallStatus = overallStatus;
    results.passRate = passRate;
    
    try {
        await fs.writeFile(reportPath, JSON.stringify(results, null, 2));
        console.log(`\n📝 Detailed report saved to: qa-qc-report.json`);
    } catch (error) {
        console.log('⚠️ Could not save JSON report');
    }
    
    console.log('\n' + '='.repeat(60));
}

// Main execution
async function runQAChecks() {
    console.log('🚀 Starting AuraQuant QA/QC Checks...');
    console.log('Frontend Root:', FRONTEND_ROOT);
    
    await checkPages();
    await checkJSFiles();
    await checkLogo();
    await checkMainDashboard();
    await checkAdminGating();
    await generateReport();
    
    // Exit with appropriate code
    if (results.failed > 0) {
        process.exit(1);
    } else {
        process.exit(0);
    }
}

// Run the checks
runQAChecks().catch(error => {
    console.error('❌ QA/QC script failed:', error);
    process.exit(1);
});