/**
 * Language Dropdown Component
 * Handles positioning, mobile optimization, and click outside
 */

function toggleLanguageDropdown() {
    const dropdown = document.getElementById('languageDropdown');
    const menu = dropdown.querySelector('.language-dropdown-menu');
    
    dropdown.classList.toggle('active');
    
    // If dropdown opened, check positioning
    if (dropdown.classList.contains('active')) {
        // Small delay for CSS transition to complete
        setTimeout(() => {
            adjustDropdownPosition(dropdown, menu);
        }, 10);
    }
}

function adjustDropdownPosition(dropdown, menu) {
    // Get viewport and dropdown dimensions
    const rect = menu.getBoundingClientRect();
    const windowWidth = window.innerWidth;
    const rightOverflow = rect.right > windowWidth - 10; // 10px buffer
    
    // If dropdown overflows right side
    if (rightOverflow) {
        menu.classList.add('adjust-position');
    } else {
        menu.classList.remove('adjust-position');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('languageDropdown');
    if (dropdown && !dropdown.contains(event.target)) {
        dropdown.classList.remove('active');
        // Clear position adjustment when closing
        const menu = dropdown.querySelector('.language-dropdown-menu');
        if (menu) {
            menu.classList.remove('adjust-position');
        }
    }
});

// Adjust on window resize
window.addEventListener('resize', function() {
    const dropdown = document.getElementById('languageDropdown');
    if (dropdown && dropdown.classList.contains('active')) {
        const menu = dropdown.querySelector('.language-dropdown-menu');
        if (menu) {
            adjustDropdownPosition(dropdown, menu);
        }
    }
});

// Close dropdown on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const dropdown = document.getElementById('languageDropdown');
        if (dropdown && dropdown.classList.contains('active')) {
            dropdown.classList.remove('active');
            const menu = dropdown.querySelector('.language-dropdown-menu');
            if (menu) {
                menu.classList.remove('adjust-position');
            }
        }
    }
});