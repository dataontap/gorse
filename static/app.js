
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

// Help system functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Help desk script loaded successfully');
    
    // Initialize help toggle functionality
    var helpToggle = document.getElementById('helpToggle');
    var helpSection = document.querySelector('.help-section');
    
    if (helpToggle && helpSection) {
        var clickCount = 0;
        var isExpanded = false;
        
        helpToggle.addEventListener('click', function(e) {
            e.preventDefault();
            clickCount++;
            
            // Toggle expanded state
            isExpanded = !isExpanded;
            
            if (isExpanded) {
                helpSection.classList.add('expanded');
                helpToggle.innerHTML = '<i class="fas fa-times"></i>';
                helpToggle.classList.add('active');
            } else {
                helpSection.classList.remove('expanded');
                helpToggle.innerHTML = '<i class="fas fa-question"></i>';
                helpToggle.classList.remove('active');
            }
            
            // Track interaction if help desk client exists
            if (typeof helpDesk !== 'undefined') {
                helpDesk.trackInteraction('help_toggle');
            }
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
