
// Menu toggle functionality
function toggleMenu(element) {
    const dropdown = element.querySelector('.menu-dropdown');
    if (dropdown) {
        // Handle both class-based and display-based toggles
        if (dropdown.classList.contains('visible') || dropdown.style.display === 'block') {
            dropdown.classList.remove('visible');
            dropdown.style.display = 'none';
        } else {
            dropdown.classList.add('visible');
            dropdown.style.display = 'block';
        }
    }
}

// Profile dropdown functionality
function toggleProfileDropdown() {
    const dropdown = document.querySelector('.profile-dropdown');
    if (dropdown) {
        if (dropdown.classList.contains('visible') || dropdown.style.display === 'block') {
            dropdown.classList.remove('visible');
            dropdown.style.display = 'none';
        } else {
            dropdown.classList.add('visible');
            dropdown.style.display = 'block';
        }
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const menuIcon = document.querySelector('.menu-icon');
    const profileSection = document.querySelector('.profile-section');
    const menuDropdown = document.querySelector('.menu-dropdown');
    const profileDropdown = document.querySelector('.profile-dropdown');
    
    // Close menu dropdown if clicking outside
    if (menuDropdown && menuIcon && !menuIcon.contains(event.target)) {
        menuDropdown.classList.remove('visible');
        menuDropdown.style.display = 'none';
    }
    
    // Close profile dropdown if clicking outside
    if (profileDropdown && profileSection && !profileSection.contains(event.target)) {
        profileDropdown.classList.remove('visible');
        profileDropdown.style.display = 'none';
    }
});

// Notification tester functionality
function showNotificationTester() {
    // Simple notification tester - you can expand this as needed
    if (Notification.permission === 'granted') {
        new Notification('🚀 GORSE Network Alert', {
            body: 'Your global connectivity is active! Ready to stay connected worldwide.',
            icon: '/static/favicon.ico'
        });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                new Notification('🚀 GORSE Network Alert', {
                    body: 'Your global connectivity is active! Ready to stay connected worldwide.',
                    icon: '/static/favicon.ico'
                });
            }
        });
    } else {
        alert('Notifications are blocked. Please enable them in your browser settings.');
    }
}

// Help system functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Help desk script loaded successfully');
    
    // Initialize help toggle functionality
    var helpToggle = document.getElementById('helpToggle');
    var helpSection = document.querySelector('.help-section');
    
    if (helpToggle && helpSection) {
        helpToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle help section visibility
            if (helpSection.style.display === 'none' || helpSection.style.display === '') {
                helpSection.style.display = 'block';
                helpSection.classList.add('expanded');
            } else {
                helpSection.style.display = 'none';
                helpSection.classList.remove('expanded');
            }
            
            // Track interaction if help desk client exists
            if (typeof helpDesk !== 'undefined') {
                helpDesk.trackInteraction('help_toggle');
            }
        });
    }
    
    // Initialize settings toggle functionality
    var settingsToggle = document.getElementById('settingsToggle');
    var settingsSubmenu = document.querySelector('.settings-submenu');
    
    if (settingsToggle && settingsSubmenu) {
        settingsToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle settings submenu visibility
            if (settingsSubmenu.style.display === 'none' || settingsSubmenu.style.display === '') {
                settingsSubmenu.style.display = 'block';
            } else {
                settingsSubmenu.style.display = 'none';
            }
        });
    }
    
    // Initialize dark mode toggle functionality
    var darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Check if dark mode preference exists, if not set it to true (dark mode default)
        const darkModePreference = localStorage.getItem('darkMode');
        const isDarkMode = darkModePreference === null ? true : darkModePreference === 'true';
        const icon = darkModeToggle.querySelector('i');
        const textSpan = darkModeToggle.querySelector('span');
        const body = document.body;

        // Set initial state and localStorage for new users
        if (isDarkMode) {
            body.classList.add('dark-mode');
            if (darkModePreference === null) {
                localStorage.setItem('darkMode', 'true');
            }
            if (icon) icon.classList.replace('fa-moon', 'fa-sun');
            if (textSpan) textSpan.textContent = 'Light Mode';
        }

        darkModeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            body.classList.toggle('dark-mode');
            const isDark = body.classList.contains('dark-mode');

            if (icon) {
                icon.classList.replace(isDark ? 'fa-moon' : 'fa-sun', 
                                     isDark ? 'fa-sun' : 'fa-moon');
            }
            if (textSpan) {
                textSpan.textContent = isDark ? 'Light Mode' : 'Dark Mode';
            }
            localStorage.setItem('darkMode', isDark);
        });
    }
    
    // Carousel functionality if present
    initializeCarousel();
});

// Carousel initialization
function initializeCarousel() {
    console.log('Carousel initialized');
    
    var carouselItems = document.querySelectorAll('.carousel-item');
    var carouselControls = document.querySelectorAll('.carousel-controls button');
    var currentSlide = 0;
    
    if (carouselItems.length === 0) return;
    
    // Set initial active item
    carouselItems[0].classList.add('active');
    if (carouselControls[0]) carouselControls[0].classList.add('active');
    
    // Add control event listeners
    carouselControls.forEach(function(control, index) {
        control.addEventListener('click', function() {
            showSlide(index);
        });
    });
    
    function showSlide(index) {
        // Remove active class from all items and controls
        carouselItems.forEach(function(item) {
            item.classList.remove('active');
        });
        carouselControls.forEach(function(control) {
            control.classList.remove('active');
        });
        
        // Add active class to current item and control
        carouselItems[index].classList.add('active');
        if (carouselControls[index]) {
            carouselControls[index].classList.add('active');
        }
        
        currentSlide = index;
    }
    
    // Auto-advance carousel every 5 seconds
    setInterval(function() {
        var nextSlide = (currentSlide + 1) % carouselItems.length;
        showSlide(nextSlide);
    }, 5000);
}

// Global help functions for compatibility
function startHelpSession() {
    if (typeof helpDesk !== 'undefined') {
        return helpDesk.startHelpSession();
    }
}

function endHelpSession() {
    if (typeof helpDesk !== 'undefined') {
        return helpDesk.endHelpSession();
    }
}

function trackHelpInteraction(type, data) {
    if (typeof helpDesk !== 'undefined') {
        return helpDesk.trackInteraction(type, data);
    }
}
