// Global variables
let currentTheme = 'dark'; // Default to dark mode

// Ensure functions are available immediately
window.toggleMenu = toggleMenu;
window.toggleProfileDropdown = toggleProfileDropdown;
window.showConfirmationDrawer = showConfirmationDrawer;
window.hideConfirmationDrawer = hideConfirmationDrawer;
window.confirmPurchase = confirmPurchase;
window.sendComingSoonNotification = sendComingSoonNotification;
window.setActiveCarouselItem = setActiveCarouselItem;
window.toggleTheme = toggleTheme;

// Global menu toggle functionality
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

// Global profile dropdown functionality
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

// Theme toggle function
function toggleTheme(isDarkMode) {
    const body = document.body;
    const darkToggle = document.getElementById('darkModeToggle');
    const lightToggle = document.getElementById('lightModeToggle');

    if (isDarkMode) {
        // Switch to dark mode
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        currentTheme = 'dark';
        localStorage.setItem('darkMode', 'true');

        // Update toggle states
        if (darkToggle) darkToggle.classList.add('active');
        if (lightToggle) lightToggle.classList.remove('active');
    } else {
        // Switch to light mode
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        currentTheme = 'light';
        localStorage.setItem('darkMode', 'false');

        // Update toggle states
        if (darkToggle) darkToggle.classList.remove('active');
        if (lightToggle) lightToggle.classList.add('active');
    }
}

// Global dashboard functions for offer cards and user data
function showConfirmationDrawer(dataAmount, price, productId) {
    console.log('Showing confirmation drawer for:', productId, dataAmount, price);
    var drawer = document.getElementById('confirmationDrawer');
    if (drawer) {
        var dataAmountElement = document.getElementById('confirmDataAmount');
        var priceElement = document.getElementById('confirmPrice');

        if (dataAmountElement) {
            dataAmountElement.textContent = dataAmount + 'GB';
        }
        if (priceElement) {
            priceElement.textContent = '$' + price;
        }

        drawer.classList.add('show');
        drawer.style.display = 'block';
        drawer.dataset.productId = productId;
    }
}

function hideConfirmationDrawer() {
    var drawer = document.getElementById('confirmationDrawer');
    if (drawer) {
        drawer.classList.remove('show');
        drawer.style.display = 'none';
    }
}

function confirmPurchase() {
    var drawer = document.getElementById('confirmationDrawer');
    if (drawer && drawer.dataset.productId) {
        var productId = drawer.dataset.productId;
        console.log('Confirming purchase for:', productId);

        // Get Firebase UID if available
        var firebaseUid = localStorage.getItem('userId') || null;

        // Make API call to record purchase
        fetch('/api/record-global-purchase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                productId: productId,
                firebaseUid: firebaseUid
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Purchase recorded:', data);
            hideConfirmationDrawer();

            // Show success message
            alert('Purchase successful! Your data will be available shortly.');

            // Refresh the page to update data balance
            window.location.reload();
        })
        .catch(error => {
            console.error('Error recording purchase:', error);
            alert('Error processing purchase. Please try again.');
        });
    }
}

function sendComingSoonNotification() {
    alert('This feature is coming soon! Thank you for your interest.');
}

function setActiveCarouselItem(index) {
    var carouselItems = document.querySelectorAll('.carousel-item');
    var carouselControls = document.querySelectorAll('.carousel-controls button');

    if (carouselItems.length === 0) return;

    // Remove active class from all items and controls
    carouselItems.forEach(function(item) {
        item.classList.remove('active');
    });
    carouselControls.forEach(function(control) {
        control.classList.remove('active');
    });

    // Add active class to current item and control
    if (carouselItems[index]) {
        carouselItems[index].classList.add('active');
    }
    if (carouselControls[index]) {
        carouselControls[index].classList.add('active');
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
	alert('Callback ordered! We will call you back shortly.');
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

document.addEventListener('DOMContentLoaded', function() {
    console.log('App.js loaded successfully');

    // Add logout functionality
    document.addEventListener('click', function(e) {
        if (e.target.id === 'logoutBtn' || e.target.closest('#logoutBtn')) {
            e.preventDefault();
            if (window.firebaseAuth && window.firebaseAuth.signOut) {
                window.firebaseAuth.signOut();
            }
        }
    });

    // Initialize theme based on localStorage or default to dark
    const savedTheme = localStorage.getItem('darkMode');
    const isDarkMode = savedTheme === null ? true : savedTheme === 'true';
    toggleTheme(isDarkMode);

    // Add event listeners for theme toggles
    const darkToggle = document.getElementById('darkModeToggle');
    const lightToggle = document.getElementById('lightModeToggle');

    if (darkToggle) {
        darkToggle.addEventListener('click', function() {
            toggleTheme(true);
        });
    }

    if (lightToggle) {
        lightToggle.addEventListener('click', function() {
            toggleTheme(false);
        });
    }

    // Initialize add user functionality with popup
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showAddUserPopup();
        });
    }

    // Handle invitation popup events using event delegation
    document.addEventListener('click', function(e) {
        // Close popup
        if (e.target.classList.contains('popup-overlay') || e.target.classList.contains('popup-close')) {
            hideAddUserPopup();
        }

        // Handle invite anyone button
        if (e.target.id === 'inviteAnyoneBtn') {
            e.preventDefault();
            showInviteForm();
        }

        // Handle demo user button
        if (e.target.id === 'demoUserBtn') {
            e.preventDefault();
            createDemoUser();
        }

        // Handle send invitation button
        if (e.target.id === 'sendInvitationBtn') {
            e.preventDefault();
            sendInvitation();
        }

        // Handle cancel invitation button
        if (e.target.id === 'cancelInviteBtn') {
            e.preventDefault();
            hideAddUserPopup();
        }
    });

    // Add event delegation for confirmation drawer buttons
    document.addEventListener('click', function(e) {
        // Handle buy buttons
        if (e.target.classList.contains('btn-primary') && e.target.textContent === 'Buy') {
            e.preventDefault();
            showConfirmationDrawer(10, 10, 'global_data_10gb');
        }

        // Handle subscribe buttons
        if (e.target.classList.contains('btn-primary') && e.target.textContent === 'Subscribe') {
            e.preventDefault();
            showConfirmationDrawer(10, 24, 'basic_membership');
        }

        // Handle drawer cancel/confirm buttons
        if (e.target.textContent === 'Cancel' && e.target.closest('.confirmation-drawer')) {
            e.preventDefault();
            hideConfirmationDrawer();
        }

        if (e.target.textContent === 'Confirm' && e.target.closest('.confirmation-drawer')) {
            e.preventDefault();
            confirmPurchase();
        }
    });

    // Initialize beta enrollment functionality
    const betaEnrollBtn = document.getElementById('betaEnrollBtn');
    if (betaEnrollBtn) {
        betaEnrollBtn.addEventListener('click', handleBetaEnrollment);
        checkBetaStatus(); // Check current status on page load
    }

    // Handle help toggle functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.id === 'helpToggle' || e.target.closest('#helpToggle')) {
            e.preventDefault();
            e.stopPropagation();
            showHelpModal();
        }
    });

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

    // Load invites if on dashboard page
    if (window.location.pathname === '/dashboard') {
        setTimeout(() => {
            if (typeof loadInvitesList === 'function') {
                loadInvitesList();
            }
        }, 1000);
    }

    // Initialize carousel functionality
    initializeCarousel();
});

// Add User Popup Functions
function showAddUserPopup() {
    // Remove existing popup if any
    hideAddUserPopup();
    
    const popup = document.createElement('div');
    popup.id = 'addUserPopup';
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-header">
                <h3>Add New User</h3>
                <button class="popup-close" onclick="hideAddUserPopup()">&times;</button>
            </div>
            <div class="popup-body">
                <div class="invitation-options">
                    <button class="invite-option-btn" id="inviteAnyoneBtn">
                        <i class="fas fa-envelope"></i>
                        <span>Invite Anyone</span>
                        <small>Send invitation via email</small>
                    </button>
                    <button class="invite-option-btn" id="demoUserBtn">
                        <i class="fas fa-user-plus"></i>
                        <span>Demo User</span>
                        <small>Create sample user instantly</small>
                    </button>
                </div>
                <div id="inviteFormContainer"></div>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    // Add event listeners
    document.getElementById('inviteAnyoneBtn').addEventListener('click', showInviteForm);
    document.getElementById('demoUserBtn').addEventListener('click', createDemoUser);
}

function hideAddUserPopup() {
    const popup = document.getElementById('addUserPopup');
    if (popup) {
        popup.remove();
    }
}

function showInviteForm() {
    const container = document.getElementById('inviteFormContainer');
    if (!container) return;
    
    container.innerHTML = `
        <div class="invite-form">
            <h4>Send Invitation</h4>
            <div class="form-group">
                <label for="inviteEmail">Email Address</label>
                <input type="email" id="inviteEmail" placeholder="Enter email address" required>
            </div>
            <div class="form-group">
                <label for="inviteMessage">Personal Message (Optional)</label>
                <textarea id="inviteMessage" placeholder="Add a personal message..." rows="3"></textarea>
            </div>
            <div class="form-actions">
                <button class="btn-secondary" id="cancelInviteBtn">Cancel</button>
                <button class="btn-primary" id="sendInvitationBtn">Send Invitation</button>
            </div>
        </div>
    `;
    
    // Add event listeners for form buttons
    document.getElementById('cancelInviteBtn').addEventListener('click', hideAddUserPopup);
    document.getElementById('sendInvitationBtn').addEventListener('click', sendInvitation);
}

function sendInvitation() {
    const email = document.getElementById('inviteEmail')?.value;
    const message = document.getElementById('inviteMessage')?.value || '';
    
    if (!email) {
        alert('Please enter an email address');
        return;
    }
    
    const firebaseUid = localStorage.getItem('userId');
    
    // Disable button during processing
    const sendBtn = document.getElementById('sendInvitationBtn');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';
    }
    
    fetch('/api/send-invitation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            message: message,
            firebaseUid: firebaseUid,
            isDemoUser: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Invitation sent successfully!');
            hideAddUserPopup();
            if (typeof loadInvitesList === 'function') {
                loadInvitesList(); // Refresh the invites list
            }
        } else {
            alert('Error sending invitation: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error sending invitation:', error);
        alert('Error sending invitation. Please try again.');
    })
    .finally(() => {
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send Invitation';
        }
    });
}

function createDemoUser() {
    const timestamp = Date.now();
    const demoEmail = `demo${timestamp}@example.com`;
    const firebaseUid = localStorage.getItem('userId');
    
    fetch('/api/send-invitation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: demoEmail,
            message: 'Demo user created automatically',
            firebaseUid: firebaseUid,
            isDemoUser: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Demo user created successfully!');
            hideAddUserPopup();
            if (typeof loadInvitesList === 'function') {
                loadInvitesList(); // Refresh the invites list
            }
        } else {
            alert('Error creating demo user: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error creating demo user:', error);
        alert('Error creating demo user. Please try again.');
    });
}

// Invites List Functions
function loadInvitesList() {
    const firebaseUid = localStorage.getItem('userId');
    if (!firebaseUid) return;
    
    fetch(`/api/invites?firebaseUid=${firebaseUid}&limit=10`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayInvites(data.invites);
        } else {
            console.error('Error loading invites:', data.message);
        }
    })
    .catch(error => {
        console.error('Error loading invites:', error);
    });
}

function displayInvites(invites) {
    const invitationsSection = document.getElementById('recentInvitationsSection');
    const invitationsList = document.getElementById('invitationsList');
    const acceptedUsersContainer = document.getElementById('acceptedUsersContainer');
    
    if (!invitationsList) return;
    
    // Clear existing content
    invitationsList.innerHTML = '';
    if (acceptedUsersContainer) {
        acceptedUsersContainer.innerHTML = '';
    }
    
    if (!invites || invites.length === 0) {
        invitationsList.innerHTML = '<p class="no-invites">No invitations sent yet</p>';
        if (invitationsSection) {
            invitationsSection.style.display = 'none';
        }
        toggleSortControls();
        return;
    }
    
    // Show the invitations section
    if (invitationsSection) {
        invitationsSection.style.display = 'block';
    }
    
    // Separate accepted and pending invitations
    const acceptedInvites = invites.filter(invite => invite.invitation_status === 'invite_accepted');
    const pendingInvites = invites.filter(invite => invite.invitation_status !== 'invite_accepted');
    
    // Display accepted invitations as user cards
    if (acceptedInvites.length > 0 && acceptedUsersContainer) {
        acceptedInvites.forEach(invite => {
            const userCard = createUserCard(invite);
            acceptedUsersContainer.appendChild(userCard);
        });
        
        // Update user count
        const userCountElement = document.querySelector('.user-count');
        if (userCountElement) {
            userCountElement.textContent = acceptedInvites.length;
        }
        
        // Show/hide sort controls based on number of cards
        toggleSortControls();
        initializeSorting();
    }
    
    // Display pending invitations in the invitations list
    pendingInvites.forEach(invite => {
        const inviteItem = createInviteItem(invite);
        invitationsList.appendChild(inviteItem);
    });
    
    if (pendingInvites.length === 0) {
        invitationsList.innerHTML = '<p class="no-pending-invites">No pending invitations</p>';
    }
}

// Toggle sort controls visibility
function toggleSortControls() {
    const userCards = document.querySelectorAll('.accepted-user');
    const sortContainer = document.querySelector('.sort-container .sort-controls');
    
    if (userCards.length >= 2) {
        if (sortContainer) {
            sortContainer.style.display = 'flex';
        }
    } else {
        if (sortContainer) {
            sortContainer.style.display = 'none';
        }
    }
}

// Initialize sorting functionality
function initializeSorting() {
    const sortSelect = document.querySelector('.sort-select');
    const sortIcons = document.querySelectorAll('.sort-icon');
    
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const activeIcon = document.querySelector('.sort-icon.active');
            if (activeIcon) {
                performSort();
            }
        });
    }
    
    sortIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            // Remove active class from all icons
            sortIcons.forEach(i => i.classList.remove('active'));
            // Add active class to clicked icon
            this.classList.add('active');
            performSort();
        });
    });
}

// Perform sorting with animation
function performSort() {
    const sortSelect = document.querySelector('.sort-select');
    const activeIcon = document.querySelector('.sort-icon.active');
    const userCards = Array.from(document.querySelectorAll('.accepted-user'));
    
    if (!sortSelect || !activeIcon || userCards.length < 2) return;
    
    const sortBy = sortSelect.value;
    const sortDirection = activeIcon.dataset.sort;
    
    // Add sorting class to cards for animation
    userCards.forEach(card => {
        card.classList.add('sorting');
    });
    
    // Sort the cards array
    userCards.sort((a, b) => {
        let valueA, valueB;
        
        switch(sortBy) {
            case 'percentage':
                valueA = parseInt(a.getAttribute('data-data-percentage'));
                valueB = parseInt(b.getAttribute('data-data-percentage'));
                break;
            case 'screentime':
                valueA = parseInt(a.getAttribute('data-time-percentage'));
                valueB = parseInt(b.getAttribute('data-time-percentage'));
                break;
            case 'dollars':
                valueA = parseInt(a.getAttribute('data-dollar-amount'));
                valueB = parseInt(b.getAttribute('data-dollar-amount'));
                break;
            default:
                valueA = parseInt(a.getAttribute('data-score'));
                valueB = parseInt(b.getAttribute('data-score'));
        }
        
        if (sortDirection === 'asc' || sortDirection === 'oldest') {
            return valueA - valueB;
        } else {
            return valueB - valueA;
        }
    });
    
    // Apply animation classes
    userCards.forEach((card, index) => {
        if (index % 2 === 0) {
            card.classList.add('sorting-up');
        } else {
            card.classList.add('sorting-down');
        }
    });
    
    // Re-append cards in sorted order after animation
    setTimeout(() => {
        const container = document.getElementById('acceptedUsersContainer');
        userCards.forEach(card => {
            container.appendChild(card);
            card.classList.remove('sorting', 'sorting-up', 'sorting-down');
        });
    }, 600);
}

// Remove user card function
function removeUserCard(element) {
    const userCard = element.closest('.user-card');
    if (userCard && confirm('Are you sure you want to remove this user?')) {
        userCard.style.transition = 'all 0.3s ease';
        userCard.style.transform = 'translateX(100%)';
        userCard.style.opacity = '0';
        
        setTimeout(() => {
            userCard.remove();
            toggleSortControls();
            
            // Update user count
            const userCards = document.querySelectorAll('.accepted-user');
            const userCountElement = document.querySelector('.user-count');
            if (userCountElement) {
                userCountElement.textContent = userCards.length;
            }
        }, 300);
    }
}

// Toggle user pause function
function toggleUserPause(element) {
    const card = element.closest('.user-card');
    const icon = element;
    const pauseDuration = card.querySelector('.pause-duration');
    
    if (icon.classList.contains('fa-pause')) {
        // Currently active, pause it
        icon.classList.remove('fa-pause');
        icon.classList.add('fa-play');
        icon.title = 'Resume data sharing';
        card.classList.add('paused');
        pauseDuration.style.display = 'inline';
        
        // Store the pause timestamp
        const pauseTime = Date.now();
        card.setAttribute('data-pause-time', pauseTime);
        pauseDuration.textContent = 'Paused just now';
        
        // Start updating the pause duration
        updatePauseDuration(card);
    } else {
        // Currently paused, resume it
        icon.classList.remove('fa-play');
        icon.classList.add('fa-pause');
        icon.title = 'Temporarily pause data share for this user';
        card.classList.remove('paused');
        pauseDuration.style.display = 'none';
        card.removeAttribute('data-pause-time');
    }
}

// Function to update pause duration display
function updatePauseDuration(card) {
    const pauseDuration = card.querySelector('.pause-duration');
    const pauseTime = parseInt(card.getAttribute('data-pause-time'));
    
    if (!pauseTime || !card.classList.contains('paused')) {
        return; // Stop if card is no longer paused
    }
    
    const now = Date.now();
    const secondsElapsed = Math.floor((now - pauseTime) / 1000);
    
    let durationText;
    if (secondsElapsed < 60) {
        if (secondsElapsed < 5) {
            durationText = 'Paused just now';
        } else {
            durationText = `Paused ${secondsElapsed} seconds ago`;
        }
    } else {
        const minutesElapsed = Math.floor(secondsElapsed / 60);
        const remainingSeconds = secondsElapsed % 60;
        
        if (minutesElapsed === 1 && remainingSeconds === 0) {
            durationText = 'Paused 1 minute ago';
        } else if (remainingSeconds === 0) {
            durationText = `Paused ${minutesElapsed} minutes ago`;
        } else if (minutesElapsed === 1) {
            durationText = `Paused 1 minute ${remainingSeconds} seconds ago`;
        } else {
            durationText = `Paused ${minutesElapsed} minutes ${remainingSeconds} seconds ago`;
        }
    }
    
    pauseDuration.textContent = durationText;
    
    // Schedule next update in 10 seconds
    setTimeout(() => updatePauseDuration(card), 10000);
}

function createUserCard(invite) {
    // Generate random data for demo users
    const isDemo = invite.email.includes('example.com');
    const dataPercentage = Math.floor(Math.random() * 100) + 1;
    const timePercentage = Math.floor(Math.random() * 100) + 1;
    const dollarAmount = Math.floor(Math.random() * 25) + 1;
    const scoreNumber = Math.floor(Math.random() * 10) + 1;

    const userCard = document.createElement('div');
    userCard.className = 'dashboard-content user-card accepted-user';
    userCard.setAttribute('data-data-percentage', dataPercentage);
    userCard.setAttribute('data-time-percentage', timePercentage);
    userCard.setAttribute('data-dollar-amount', dollarAmount);
    userCard.setAttribute('data-score', scoreNumber);
    
    userCard.innerHTML = `
        <div class="user-info-header">
            <div class="user-name">${invite.email}</div>
            <div class="remove-icon" onclick="removeUserCard(this)" title="Remove user">
                <i class="fas fa-times"></i>
            </div>
        </div>
        <div class="email-container">
            <div class="user-email">${invite.email}</div>
            <div class="timestamp">Active Member since ${formatDate(invite.created_at)}</div>
        </div>
        
        <div class="data-usage">
            <div class="usage-metrics">
                <div class="metric" data-metric="data">
                    <div class="usage-label"><i class="fas fa-database"></i> Data</div>
                    <div class="usage-amount">${dataPercentage}%</div>
                </div>
                <div class="metric" data-metric="time">
                    <div class="usage-label"><i class="fas fa-clock"></i> Time</div>
                    <div class="usage-amount">${timePercentage}%</div>
                </div>
                <div class="metric" data-metric="cost">
                    <div class="usage-label"><i class="fas fa-dollar-sign"></i> Cost</div>
                    <div class="usage-amount">$${dollarAmount}</div>
                </div>
                <div class="metric" data-metric="score">
                    <div class="usage-label"><i class="fas fa-star"></i> Score</div>
                    <div class="usage-amount">${scoreNumber}</div>
                </div>
            </div>
        </div>

        <div class="card-actions">
            <i class="fas fa-pause pause-play-icon" title="Temporarily pause data share for this user" onclick="toggleUserPause(this)"></i>
            <span class="pause-duration" style="display: none;"></span>
        </div>
    `;
    
    return userCard;
}

// Initialize pause duration updates for any existing paused users on page load
function initializePauseDurationUpdates() {
    const pausedCards = document.querySelectorAll('.user-card.paused[data-pause-time]');
    pausedCards.forEach(card => {
        updatePauseDuration(card);
    });
}

// Call this when the page loads to handle any existing paused users
document.addEventListener('DOMContentLoaded', function() {
    // Existing DOMContentLoaded code...
    
    // Initialize pause duration updates after a short delay to ensure cards are loaded
    setTimeout(initializePauseDurationUpdates, 1500);
});

function createInviteItem(invite) {
    const inviteItem = document.createElement('div');
    inviteItem.className = 'invitation-item';
    
    const statusClass = `status-${invite.invitation_status.replace('_', '-')}`;
    const canCancel = invite.invitation_status === 'invite_sent' || invite.invitation_status === 're_invited';
    
    inviteItem.innerHTML = `
        <div class="invitation-info">
            <div class="invitation-email">${invite.email}</div>
            <div class="invitation-date">${formatDate(invite.created_at)}</div>
        </div>
        <div class="invitation-status ${statusClass}">${formatStatus(invite.invitation_status)}</div>
        ${canCancel ? `<button class="cancel-invite-btn" onclick="cancelInvitation(${invite.id})" title="Cancel invitation">
            <i class="fas fa-times"></i>
        </button>` : ''}
    `;
    
    return inviteItem;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function formatStatus(status) {
    const statusMap = {
        'invite_sent': 'Sent',
        're_invited': 'Re-sent',
        'invite_accepted': 'Accepted',
        'invite_rejected': 'Rejected',
        'invite_cancelled': 'Cancelled'
    };
    return statusMap[status] || status;
}

function cancelInvitation(inviteId) {
    if (!confirm('Are you sure you want to cancel this invitation?')) {
        return;
    }
    
    const firebaseUid = localStorage.getItem('userId');
    
    fetch(`/api/invites/${inviteId}/cancel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            firebaseUid: firebaseUid
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Invitation cancelled successfully');
            loadInvitesList(); // Refresh the list
        } else {
            alert('Error cancelling invitation: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error cancelling invitation:', error);
        alert('Error cancelling invitation. Please try again.');
    });
}

// Make functions globally available
window.showAddUserPopup = showAddUserPopup;
window.hideAddUserPopup = hideAddUserPopup;
window.loadInvitesList = loadInvitesList;
window.refreshInvitesList = loadInvitesList;
window.cancelInvitation = cancelInvitation;
window.removeUserCard = removeUserCard;
window.toggleUserPause = toggleUserPause;
window.performSort = performSort;

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

// Store current subscription status globally
let currentSubscriptionStatus = null;

// Initialize carousel functionality with intelligent offer filtering
function initializeCarousel() {
    console.log('Carousel initialized');

    // Wait for subscription status to be loaded
    setTimeout(() => {
        populateOfferCards();
    }, 1000);
}

function populateOfferCards() {
    const carouselInner = document.getElementById('carouselInner');
    const carouselControls = document.getElementById('carouselControls');

    if (!carouselInner || !carouselControls) return;

    // Define all possible offers
    const allOffers = [
        {
            id: 'global_data',
            title: 'Global Priority Data',
            description: ['10GB no-expiry data for $10.', 'Share with any member.', 'Works in 160+ countries.'],
            price: '$10',
            buttonText: 'Buy',
            buttonClass: 'btn-primary',
            action: "showConfirmationDrawer(10, 10, 'global_data_10gb')",
            alwaysShow: true
        },
        {
            id: 'full_membership',
            title: 'Full Membership',
            description: ['Global Data Access. National Talk + Text.', 'Global Wi-Fi Calling & Satellite eTXT.'],
            price: '$66/year',
            buttonText: 'Subscribe',
            buttonClass: 'btn-secondary',
            action: "sendComingSoonNotification()",
            disabled: true,
            alwaysShow: true
        },
        {
            id: 'basic_membership',
            title: 'Basic Membership',
            description: ['New number. 2FA. Global data access.', 'To include SAT T9-1-1 when available.'],
            price: '$24/year',
            buttonText: 'Subscribe',
            buttonClass: 'btn-primary',
            action: "showConfirmationDrawer(10, 24, 'basic_membership')",
            showCondition: shouldShowBasicMembership
        }
    ];

    // Filter offers based on conditions
    const availableOffers = allOffers.filter(offer => {
        if (offer.alwaysShow) return true;
        if (offer.showCondition) return offer.showCondition();
        return true;
    });

    // Clear existing content
    carouselInner.innerHTML = '';
    carouselControls.innerHTML = '';

    // Populate carousel with available offers
    availableOffers.forEach((offer, index) => {
        // Create carousel item
        const carouselItem = document.createElement('div');
        carouselItem.className = `carousel-item${index === 0 ? ' active' : ''}`;

        const descriptions = offer.description.map(desc => `<p>${desc}</p>`).join('');
        const buttonDisabled = offer.disabled ? ' disabled' : '';

        carouselItem.innerHTML = `
            <div class="offer-card">
                <div class="offer-content">
                    <h3>${offer.title}</h3>
                    ${descriptions}
                    <div class="price">${offer.price}</div>
                    <button class="btn ${offer.buttonClass}"${buttonDisabled} onclick="${offer.action}">${offer.buttonText}</button>
                </div>
            </div>
        `;

        carouselInner.appendChild(carouselItem);

        // Create control button
        const controlButton = document.createElement('button');
        controlButton.className = index === 0 ? 'active' : '';
        controlButton.onclick = () => setActiveCarouselItem(index);
        carouselControls.appendChild(controlButton);
    });

    // Initialize carousel controls
    initializeCarouselControls();
}

function shouldShowBasicMembership() {
    if (!currentSubscriptionStatus) return true;

    // Don't show if user has active basic membership with more than 7 days remaining
    if (currentSubscriptionStatus.status === 'active' && 
        currentSubscriptionStatus.subscription_type === 'basic_membership') {

        const endDate = new Date(currentSubscriptionStatus.end_date);
        const now = new Date();
        const daysRemaining = (endDate - now) / (1000 * 60 * 60 * 24);

        if (daysRemaining > 7) {
            console.log(`Basic membership has ${Math.round(daysRemaining)} days remaining - hiding basic membership offer`);
            return false;
        }
    }

    return true;
}

function initializeCarouselControls() {
    const carouselItems = document.querySelectorAll('.carousel-item');
    const carouselControls = document.querySelectorAll('.carousel-controls button');
    let currentSlide = 0;
    let autoAdvanceInterval;

    if (carouselItems.length === 0) return;

    function showSlide(index) {
        // Remove active class from all items and controls
        carouselItems.forEach(function(item, i) {
            if (i === index) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        carouselControls.forEach(function(control, i) {
            if (i === index) {
                control.classList.add('active');
            } else {
                control.classList.remove('active');
            }
        });

        currentSlide = index;
    }

    // Start auto-advance if there are multiple items
    if (carouselItems.length > 1) {
        autoAdvanceInterval = setInterval(function() {
            const nextSlide = (currentSlide + 1) % carouselItems.length;
            showSlide(nextSlide);
        }, 6000);
    }

    // Store the showSlide function globally for manual control
    window.setActiveCarouselItem = showSlide;
}

// Update subscription status when it's received
function updateSubscriptionStatus(subscriptionData) {
    currentSubscriptionStatus = subscriptionData;
    console.log('Subscription status updated:', subscriptionData);

    // Re-populate offer cards if carousel is already initialized
    if (document.getElementById('carouselInner')) {
        populateOfferCards();
    }
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

// Beta enrollment functions
function handleBetaEnrollment() {
    const firebaseUid = localStorage.getItem('userId');
    if (!firebaseUid) {
        alert('Please sign in to enroll in the beta program.');
        return;
    }

    const betaEnrollBtn = document.getElementById('betaEnrollBtn');
    betaEnrollBtn.disabled = true;
    betaEnrollBtn.textContent = 'Processing...';

    fetch('/api/beta-enrollment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            firebaseUid: firebaseUid
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.checkout_url) {
                // Redirect to Stripe checkout
                window.location.href = data.checkout_url;
            } else {
                updateBetaStatus(data.status, data.message);
            }
        } else {
            alert('Error enrolling in beta: ' + (data.message || 'Unknown error'));
            betaEnrollBtn.disabled = false;
            betaEnrollBtn.textContent = 'Request BETA access ($1 eSIM)';
        }
    })
    .catch(error => {
        console.error('Error enrolling in beta:', error);
        alert('Error enrolling in beta. Please try again.');
        betaEnrollBtn.disabled = false;
        betaEnrollBtn.textContent = 'Request BETA access ($1 eSIM)';
    });
}

function checkBetaStatus() {
    const firebaseUid = localStorage.getItem('userId');
    if (!firebaseUid) return;

    fetch(`/api/beta-status?firebaseUid=${firebaseUid}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBetaStatus(data.status, data.message);
        }
    })
    .catch(error => {
        console.error('Error checking beta status:', error);
    });
}

function updateBetaStatus(status, message) {
    const betaEnrollBtn = document.getElementById('betaEnrollBtn');
    const betaStatus = document.getElementById('betaStatus');
    const betaStatusText = document.getElementById('betaStatusText');

    switch(status) {
        case 'not_enrolled':
            betaEnrollBtn.style.display = 'block';
            betaEnrollBtn.disabled = false;
            betaEnrollBtn.textContent = 'Request BETA access ($1 eSIM)';
            betaStatus.style.display = 'none';
            break;
        case 'payment_pending':
            betaEnrollBtn.style.display = 'none';
            betaStatus.style.display = 'block';
            betaStatusText.textContent = 'Check for eSIM invite in your email.';
            break;
        case 'esim_ready':
            betaEnrollBtn.style.display = 'none';
            betaStatus.style.display = 'block';
            betaStatusText.textContent = 'Your eSIM is ready to download';
            break;
        case 'enrolled':
            betaEnrollBtn.style.display = 'none';
            betaStatus.style.display = 'block';
            betaStatusText.textContent = message || 'Beta enrollment complete';
            break;
    }
}

// Function to show the help modal
function showHelpModal() {
    // Create the modal overlay
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'helpModalOverlay';
    modalOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
    `;

    // Create the modal content
    const modalContent = document.createElement('div');
    modalContent.id = 'helpModalContent';
    modalContent.style.cssText = `
        background-color: #fff;
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
        width: 80%;
        max-width: 600px;
    `;

    // Create the close button
    const closeButton = document.createElement('button');
    closeButton.id = 'closeHelpModal';
    closeButton.textContent = 'Close';
    closeButton.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        padding: 5px 10px;
        background-color: #f00;
        color: white;
        border: none;
        border-radius: 3px;
        cursor: pointer;
    `;
    closeButton.addEventListener('click', hideHelpModal);

    // Create the help content
    const helpContent = document.createElement('div');
    helpContent.className = 'help-content-redesigned';
    helpContent.innerHTML = `
        <div class="human-help-section">
            <div class="help-option-header">
                <i class="fas fa-user"></i>
                <span>Human help:</span>
            </div>
            <div class="help-option-content">
                <div class="agent-status">
                    <span class="agent-availability">Super agent available in <span class="countdown-timer" style="color: #28a745; font-weight: bold;">4:20</span></span>
                </div>
                <button id="orderCallbackBtn" class="callback-btn">Order callback</button>
            </div>
            <button id="chatWithAgentBtn" class="chat-btn">Chat with Agent</button>
        </div>

        <div class="ai-help-section">
            <div class="help-option-header">
                <i class="fas fa-robot"></i>
                <span>Use AI help:</span>
            </div>
            <div class="help-option-content">
                <div class="ai-links">
                    <a href="https://chat.openai.com" target="_blank" class="ai-link chatgpt-link">
                        <i class="fas fa-comments"></i>
                        ChatGPT
                    </a>
                    <a href="https://gemini.google.com" target="_blank" class="ai-link gemini-link">
                        <i class="fas fa-star"></i>
                        Gemini
                    </a>
                </div>
            </div>
        </div>
    `;

    // Append elements to the modal
    modalContent.appendChild(closeButton);
    modalContent.appendChild(helpContent);
    modalOverlay.appendChild(modalContent);

    // Append the modal to the body
    document.body.appendChild(modalOverlay);

    // Add event listener for the order callback button (event delegation)
    modalOverlay.addEventListener('click', function(e) {
        if (e.target.id === 'orderCallbackBtn') {
            orderCallback();
        }
        if (e.target.id === 'chatWithAgentBtn') {
            startChat();
        }
    });
}

// Function to hide the help modal
function hideHelpModal() {
    const modalOverlay = document.getElementById('helpModalOverlay');
    if (modalOverlay) {
        modalOverlay.remove();
		stopAllCountdowns();
    }
}

function startChat() {
    alert('Starting chat with agent...');
}