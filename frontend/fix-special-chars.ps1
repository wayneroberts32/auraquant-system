# PowerShell script to fix special characters in HTML files
# Run this to fix encoding issues

$files = @(
    "pages\bot-status.html",
    "pages\deployment-verification.html",
    "pages\help-centre.html"
)

$replacements = @{
    # Emoji replacements
    'ðŸ¤–' = '🤖'  # Robot
    'ðŸ"Š' = '📊'  # Chart
    'ðŸ"ˆ' = '📈'  # Chart increasing
    'ðŸ"‰' = '📉'  # Chart decreasing
    'ðŸ'°' = '💰'  # Money bag
    'ðŸŽ¯' = '🎯'  # Target
    'ðŸš€' = '🚀'  # Rocket
    'âœ…' = '✅'  # Check mark
    'ðŸ'Ž' = '💎'  # Diamond
    'ðŸ§ ' = '🧠'  # Brain
    'âš¡' = '⚡'  # Lightning
    'ðŸ"' = '🔍'  # Search
    'ðŸ"' = '🔑'  # Key
    'ðŸ'¤' = '👤'  # User
    'âš™ï¸' = '⚙️'  # Gear
    'ðŸ•¯ï¸' = '🕯️'  # Candle
    'ðŸ"·' = '📷'  # Camera
    'ðŸ©¹' = '🩹'  # Band-aid
    'ðŸŒ' = '🌍'  # Earth
    'ðŸŒŸ' = '🌟'  # Star
    'ðŸ§¬' = '🧬'  # DNA
    'âš›ï¸' = '⚛️'  # Atom
    
    # Special characters
    'â—' = '●'     # Bullet
    'Ã—' = '×'     # Multiplication sign
    'â†'' = '↑'     # Up arrow
    'â†"' = '↓'     # Down arrow
    'â†»' = '↻'     # Refresh
    'âœ"' = '✓'     # Check
    'âœ"' = '✔'     # Check (alternate)
    'â­•' = '⭕'   # Circle
    'â"' = '❓'     # Question mark
    'âœï¸' = '✏️'   # Pencil
    
    # Text fixes
    'MÃ—' = 'M×'   # Million times
}

foreach ($file in $files) {
    $fullPath = Join-Path $PSScriptRoot $file
    if (Test-Path $fullPath) {
        Write-Host "Processing: $file" -ForegroundColor Green
        
        # Read file with UTF-8 encoding
        $content = Get-Content -Path $fullPath -Raw -Encoding UTF8
        
        # Apply replacements
        foreach ($key in $replacements.Keys) {
            $content = $content -replace [regex]::Escape($key), $replacements[$key]
        }
        
        # Write file back with UTF-8 encoding
        Set-Content -Path $fullPath -Value $content -Encoding UTF8
        
        Write-Host "  Fixed special characters in $file" -ForegroundColor Cyan
    } else {
        Write-Host "  File not found: $fullPath" -ForegroundColor Yellow
    }
}

Write-Host "`nAll files processed!" -ForegroundColor Green