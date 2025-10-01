/**
 * AuraQuant Multi-Screen Workspace Manager
 * Handles multiple draggable/resizable panels in single tab
 * NO STYLING CHANGES - preserves existing look and feel
 */

// Multi-Screen Workspace Manager
document.addEventListener("DOMContentLoaded", () => {
    const workspace = document.getElementById("workspace-container");
    let panelZIndex = 2000;

    function openPanel(page, title) {
        const panel = document.createElement("div");
        panel.className = "workspace-panel";
        panel.style.position = "absolute";
        panel.style.top = Math.random() * 100 + 80 + "px"; 
        panel.style.left = Math.random() * 100 + 80 + "px";
        panel.style.width = "800px";
        panel.style.height = "600px";
        panel.style.background = "#1e222d";
        panel.style.border = "1px solid #2a2e39";
        panel.style.borderRadius = "6px";
        panel.style.resize = "both";
        panel.style.overflow = "hidden";
        panel.style.zIndex = ++panelZIndex;

        panel.innerHTML = `
            <div class="workspace-header" style="cursor:move; background:#2a2e39; padding:6px 10px; display:flex; justify-content:space-between; align-items:center; color:#d1d4dc; font-size:13px; font-weight:500;">
                <span>${title}</span>
                <button class="close-btn" style="background:none; border:none; color:#ff4444; font-size:20px; cursor:pointer; padding:0; line-height:1;">×</button>
            </div>
            <iframe src="../pages/${page}.html" class="workspace-iframe" style="width:100%; height:calc(100% - 32px); border:none; background:#131722;"></iframe>
        `;

        panel.querySelector(".close-btn").onclick = () => panel.remove();

        makeDraggable(panel);
        workspace.appendChild(panel);
        
        // Bring to front on click
        panel.addEventListener('mousedown', () => {
            panel.style.zIndex = ++panelZIndex;
        });
    }

    // Hook all menu items with data-workspace-page
    document.querySelectorAll("[data-workspace-page]").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault(); 
            e.stopPropagation(); 
            
            const page = item.getAttribute("data-workspace-page");
            const title = item.textContent.trim();
            
            openPanel(page, title);
        });
    });

    // Override sidebar button navigation to open in workspace
    const sidebarMappings = {
        '📈': 'manual-trade',
        '🔍': 'screeners', 
        '🤖': 'ai-workers-panel',
        '🔑': 'libraries',
        '⚙️': 'balance-control',
        '❓': 'help-centre'
    };

    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        const icon = btn.querySelector('span')?.textContent;
        if (sidebarMappings[icon]) {
            // Remove existing click handlers
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); 
                
                // Don't open panel for menu toggle button
                if (this.id === 'menuToggle') return;
                
                document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const pageName = sidebarMappings[icon];
                const titles = {
                    'manual-trade': 'Trading Panel',
                    'screeners': 'Screener',
                    'ai-workers-panel': 'AI Workers',
                    'libraries': 'Strategy Builder',
                    'balance-control': 'Settings',
                    'help-centre': 'Help Centre'
                };
                
                openPanel(pageName, titles[pageName] || pageName);
            });
        }
    });

    function makeDraggable(el) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        const header = el.querySelector(".workspace-header");
        if (!header) return;
        header.onmousedown = dragMouseDown;

        function dragMouseDown(e) {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            el.style.top = (el.offsetTop - pos2) + "px";
            el.style.left = (el.offsetLeft - pos1) + "px";
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    // Add workspace styles dynamically
    const workspaceStyles = document.createElement('style');
    workspaceStyles.innerHTML = `
        .workspace {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1999;
        }
        
        .workspace-panel {
            pointer-events: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            min-width: 300px;
            min-height: 200px;
            max-width: calc(100vw - 100px);
            max-height: calc(100vh - 100px);
        }
        
        .workspace-panel:hover {
            box-shadow: 0 6px 30px rgba(0, 255, 136, 0.2);
        }
        
        .workspace-header:active {
            background: #363a45 !important;
        }
        
        .workspace-iframe {
            background: #131722;
        }
    `;
    document.head.appendChild(workspaceStyles);
});
