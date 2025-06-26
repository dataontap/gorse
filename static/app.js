
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
