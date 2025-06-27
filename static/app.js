
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

function setActiveCarouselItem(index) {
    // Placeholder function to prevent console errors
    console.log('Carousel item', index, 'selected');
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

// Help system countdown and callback functionality
var agentCountdownInterval;
var callbackCountdownInterval;

function startAgentCountdown() {
    var countdownElement = document.querySelector('.countdown-timer');
    if (countdownElement) {
        var minutes = 4;
        var seconds = 20;
        
        agentCountdownInterval = setInterval(function() {
            if (seconds > 0) {
                seconds--;
            } else if (minutes > 0) {
                minutes--;
                seconds = 59;
            } else {
                clearInterval(agentCountdownInterval);
                countdownElement.textContent = 'Agent available now!';
                return;
            }
            
            var timeStr = minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
            countdownElement.textContent = timeStr;
        }, 1000);
    }
}

function stopAllCountdowns() {
    if (agentCountdownInterval) {
        clearInterval(agentCountdownInterval);
    }
    if (callbackCountdownInterval) {
        clearInterval(callbackCountdownInterval);
    }
}

function orderCallback() {
    var callbackBtn = document.getElementById('orderCallbackBtn');
    if (callbackBtn) {
        callbackBtn.disabled = true;
        callbackBtn.textContent = 'Callback Ordered';
        
        // Show countdown
        var countdownDiv = document.querySelector('.callback-countdown');
        if (!countdownDiv) {
            countdownDiv = document.createElement('div');
            countdownDiv.className = 'callback-countdown';
            callbackBtn.parentNode.appendChild(countdownDiv);
        }
        
        var countdownTime = 300; // 5 minutes
        callbackCountdownInterval = setInterval(function() {
            if (countdownTime > 0) {
                var minutes = Math.floor(countdownTime / 60);
                var seconds = countdownTime % 60;
                countdownDiv.innerHTML = 'Expect callback in: ' + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
                countdownTime--;
            } else {
                clearInterval(callbackCountdownInterval);
                countdownDiv.innerHTML = '<button id="answerCallBtn" class="answer-call-button">Answer Super Agent\'s Call</button>';
            }
        }, 1000);
    }
}

function answerCall() {
    alert('Connecting you with our super agent...');
}

function startAgentCountdown() {
    var agentCountdownEl = document.getElementById('agentCountdown');
    if (!agentCountdownEl) return;
    
    var minutes = 4;
    var seconds = 20;
    
    agentCountdownInterval = setInterval(function() {
        if (seconds === 0) {
            if (minutes === 0) {
                agentCountdownEl.textContent = '0:00';
                agentCountdownEl.style.color = '#28a745';
                clearInterval(agentCountdownInterval);
                return;
            }
            minutes--;
            seconds = 59;
        } else {
            seconds--;
        }
        
        var displaySeconds = seconds < 10 ? '0' + seconds : seconds;
        agentCountdownEl.textContent = minutes + ':' + displaySeconds;
    }, 1000);
}

function orderCallback() {
    var orderCallbackBtn = document.getElementById('orderCallbackBtn');
    var callbackCountdown = document.getElementById('callbackCountdown');
    
    if (orderCallbackBtn && callbackCountdown) {
        orderCallbackBtn.disabled = true;
        orderCallbackBtn.textContent = 'Callback ordered';
        callbackCountdown.style.display = 'block';
        
        startCallbackCountdown();
        
        // Track interaction if help desk client exists
        if (typeof helpDesk !== 'undefined') {
            helpDesk.trackInteraction('callback_ordered');
        }
    }
}

function startCallbackCountdown() {
    var callCountdownEl = document.getElementById('callCountdown');
    var answerCallBtn = document.getElementById('answerCallBtn');
    
    if (!callCountdownEl || !answerCallBtn) return;
    
    var totalSeconds = 30; // 30 seconds for demo
    
    callbackCountdownInterval = setInterval(function() {
        if (totalSeconds <= 0) {
            callCountdownEl.textContent = '00:00';
            answerCallBtn.style.display = 'inline-block';
            clearInterval(callbackCountdownInterval);
            return;
        }
        
        totalSeconds--;
        var minutes = Math.floor(totalSeconds / 60);
        var seconds = totalSeconds % 60;
        var displayMinutes = minutes < 10 ? '0' + minutes : minutes;
        var displaySeconds = seconds < 10 ? '0' + seconds : seconds;
        callCountdownEl.textContent = displayMinutes + ':' + displaySeconds;
    }, 1000);
}

function answerSuperAgentCall() {
    // Simulate connecting to super agent
    alert('Connecting you to our super agent...\n\nThis is a demo. In production, this would initiate a voice call.');
    
    // Reset the help section
    var callbackCountdown = document.getElementById('callbackCountdown');
    var orderCallbackBtn = document.getElementById('orderCallbackBtn');
    var answerCallBtn = document.getElementById('answerCallBtn');
    
    if (callbackCountdown) callbackCountdown.style.display = 'none';
    if (answerCallBtn) answerCallBtn.style.display = 'none';
    if (orderCallbackBtn) {
        orderCallbackBtn.disabled = false;
        orderCallbackBtn.textContent = 'Order callback';
    }
    
    // Track interaction if help desk client exists
    if (typeof helpDesk !== 'undefined') {
        helpDesk.trackInteraction('super_agent_call_answered');
    }
}

function stopAllCountdowns() {
    if (agentCountdownInterval) {
        clearInterval(agentCountdownInterval);
        agentCountdownInterval = null;
    }
    if (callbackCountdownInterval) {
        clearInterval(callbackCountdownInterval);
        callbackCountdownInterval = null;
    }
}

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
    
    // Initialize help toggle functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.id === 'helpToggle' || e.target.closest('#helpToggle')) {
            e.preventDefault();
            e.stopPropagation();
            
            var helpSection = document.querySelector('.help-section');
            if (helpSection) {
                // Toggle help section visibility
                if (helpSection.classList.contains('expanded')) {
                    helpSection.classList.remove('expanded');
                    helpSection.style.display = 'none';
                    stopAllCountdowns();
                } else {
                    helpSection.classList.add('expanded');
                    helpSection.style.display = 'block';
                    startAgentCountdown();
                }
                
                // Track interaction if help desk client exists
                if (typeof helpDesk !== 'undefined') {
                    helpDesk.trackInteraction('help_toggle');
                }
            }
        }
        
        // Handle callback button
        if (e.target.id === 'orderCallbackBtn') {
            orderCallback();
        }
        
        // Handle answer call button
        if (e.target.id === 'answerCallBtn') {
            answerCall();
        }
    });
});Btn');
    if (answerCallBtn) {
        answerCallBtn.addEventListener('click', function() {
            answerSuperAgentCall();
        });
    }
})
    
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
