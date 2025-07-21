// Prevent re-initialization and duplicate loading
if (window.appInitialized) {
    console.log("App already initialized, skipping...");
    // Exit early by wrapping the rest in a conditional
} else {
window.appInitialized = true;

// Standalone logout function
function handleLogout(event) {
    if (event) {
        event.preventDefault();
    }

    console.log('Handling logout...');

    // Clear all localStorage
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('databaseUserId');
    localStorage.clear();

    // Try Firebase logout if available
    if (typeof firebase !== 'undefined' && firebase.auth) {
        firebase.auth().signOut().then(() => {
            console.log('Firebase logout successful');
            window.location.href = '/';
        }).catch((error) => {
            console.error('Firebase logout error:', error);
            window.location.href = '/';
        });
    } else {
        // Direct redirect if Firebase not available
        console.log('Firebase not available, redirecting directly');
        window.location.href = '/';
    }
}

// Make function globally available
window.handleLogout = handleLogout;

// Global variables
let currentUser = null;

// Initialize user data
function initializeUser() {
    const user = getCurrentUser(); // From firebase-auth.js
    if (user) {
        currentUser = user;
        console.log('App initialized with user:', currentUser);
    } else {
        console.log('App initialized without user (guest mode)');
    }
}

// Call initialization when the page loads
document.addEventListener('DOMContentLoaded', initializeUser);

// Global variables
let currentTheme = 'dark'; // Default to dark mode

// Ensure functions are available immediately
window.toggleMenu = toggleMenu;
window.toggleProfileDropdown = toggleProfileDropdown;
window.showConfirmationDrawer = showConfirmationDrawer;
window.hideConfirmationDrawer = hideConfirmationDrawer;
window.confirmPurchase = confirmPurchase;
window.sendComingSoonNotification = sendComingSoonNotification;
window.toggleTheme = toggleTheme;

// Global menu toggle functionality
function toggleMenu(element) {
    console.log('toggleMenu called with element:', element);
    
    // Find the dropdown within the clicked element
    let dropdown = element.querySelector('.menu-dropdown');
    
    // If not found within the element, try finding it as a sibling
    if (!dropdown) {
        dropdown = element.parentElement.querySelector('.menu-dropdown');
    }
    
    // If still not found, try finding it globally
    if (!dropdown) {
        dropdown = document.querySelector('.menu-dropdown');
    }
    
    console.log('Found dropdown:', dropdown);
    
    if (dropdown) {
        const isVisible = dropdown.classList.contains('visible') || 
                        dropdown.style.display === 'block' || 
                        getComputedStyle(dropdown).display === 'block';
        
        console.log('Dropdown is currently visible:', isVisible);
        
        if (isVisible) {
            dropdown.classList.remove('visible');
            dropdown.style.display = 'none';
            console.log('Hiding dropdown');
        } else {
            dropdown.classList.add('visible');
            dropdown.style.display = 'block';
            console.log('Showing dropdown');
        }
    } else {
        console.error('Menu dropdown not found');
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

        // Get Firebase UID from multiple possible sources
        var firebaseUid = null;

        // First try to get current user data
        var currentUserData = JSON.parse(localStorage.getItem('currentUser') || 'null');
        if (currentUserData && currentUserData.uid) {
            firebaseUid = currentUserData.uid;
            console.log('Using Firebase UID from currentUser:', firebaseUid);
        } else {
            // Fallback to other localStorage keys
            firebaseUid = localStorage.getItem('firebaseUid') || 
                         localStorage.getItem('userId') || null;
            console.log('Using Firebase UID from fallback:', firebaseUid);
        }

        if (!firebaseUid) {
            alert('Please log in to make a purchase.');
            return;
        }

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

// Carousel functions removed - using grid layout now

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

    // Initialize theme based on localStorage or default to dark
    const savedTheme = localStorage.getItem('darkMode');
    const isDarkMode = savedTheme === null ? true : savedTheme === 'true';
    toggleTheme(isDarkMode);

    // Load DOTM balance if wallet is connected
    loadDOTMBalance();

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

    // Initialize chart toggle functionality
    document.querySelectorAll('.insight-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            toggleChart(this);
        });
    });

    // Use event delegation for all interactive elements
    document.addEventListener('click', function(e) {
        // Handle logout functionality
        if (e.target.id === 'logoutBtn' || e.target.closest('#logoutBtn')) {
            e.preventDefault();
            console.log('Logout button clicked');

            // Try multiple logout methods
            if (window.firebaseAuth && window.firebaseAuth.signOut) {
                window.firebaseAuth.signOut();
            } else if (typeof firebase !== 'undefined' && firebase.auth) {
                firebase.auth().signOut().then(() => {
                    localStorage.clear();
                    window.location.href = '/';
                }).catch((error) => {
                    console.error('Logout error:', error);
                    localStorage.clear();
                    window.location.href = '/';
                });
            } else {
                // Fallback: clear storage and redirect
                localStorage.clear();
                window.location.href = '/';
            }
            return;
        }

        // Close popup
        if (e.target.classList.contains('popup-overlay') || e.target.classList.contains('popup-close')) {
            hideAddUserPopup();
            return;
        }

        // Handle invite anyone button
        if (e.target.id === 'inviteAnyoneBtn') {
            e.preventDefault();
            showInviteForm();
            return;
        }

        // Handle demo user button
        if (e.target.id === 'demoUserBtn') {
            e.preventDefault();
            createDemoUser();
            return;
        }

        // Handle send invitation button
        if (e.target.id === 'sendInvitationBtn') {
            e.preventDefault();
            sendInvitation();
            return;
        }

        // Handle cancel invitation button
        if (e.target.id === 'cancelInviteBtn') {
            e.preventDefault();
            hideAddUserPopup();
            return;
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

    // Initialize settings toggle functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.id === 'settingsToggle' || e.target.closest('#settingsToggle')) {
            e.preventDefault();
            e.stopPropagation();

            const settingsSubmenu = document.querySelector('.settings-submenu');
            if (settingsSubmenu) {
                // Toggle settings submenu visibility
                if (settingsSubmenu.style.display === 'none' || settingsSubmenu.style.display === '') {
                    settingsSubmenu.style.display = 'block';
                } else {
                    settingsSubmenu.style.display = 'none';
                }
            }
        }

        // Handle language selector changes
        if (e.target.id === 'languageSelect') {
            const selectedLanguage = e.target.value;
            if (typeof setLanguage === 'function') {
                setLanguage(selectedLanguage);
            }
        }

        // Close settings submenu when clicking outside
        if (!e.target.closest('#settingsToggle') && !e.target.closest('.settings-submenu')) {
            const settingsSubmenu = document.querySelector('.settings-submenu');
            if (settingsSubmenu && settingsSubmenu.style.display === 'block') {
                settingsSubmenu.style.display = 'none';
            }
        }
    });

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
    console.log('showAddUserPopup called');

    // Remove existing popup if any
    hideAddUserPopup();

    const popup = document.createElement('div');
    popup.id = 'addUserPopup';
    popup.className = 'popup-overlay';
    popup.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background: rgba(0, 0, 0, 0.7) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        z-index: 999999 !important;
        opacity: 1 !important;
    `;

    popup.innerHTML = `
        <div class="popup-content" style="z-index: 999999; position: relative;">
            <div class="popup-header">
                <h3>Add New Datashare User</h3>
                <button class="popup-close" onclick="hideAddUserPopup()">&times;</button>
            </div>
            <div class="popup-body">
                <div class="invitation-options">
                    <button class="invite-option-btn" id="inviteAnyoneBtn">
                        <i class="fas fa-envelope"></i>
                        <span>Invite Anyone</span>
                        <small>Send invitation via email for a start</small>
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
    console.log('Popup added to body:', popup);

    // Force show with timeout
    setTimeout(() => {
        popup.classList.add('show');
        popup.style.opacity = '1';
    }, 10);

    // Add event listeners
    document.getElementById('inviteAnyoneBtn').addEventListener('click', showInviteForm);
    document.getElementById('demoUserBtn').addEventListener('click', createDemoUser);
}

function hideAddUserPopup() {
    console.log('hideAddUserPopup called');
    const popup = document.getElementById('addUserPopup');
    if (popup) {
        popup.style.opacity = '0';
        setTimeout(() => {
            popup.remove();
        }, 300);
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

// Edit user card function (placeholder for future functionality)
function editUserCard(element) {
    alert('Edit user functionality coming soon!');
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

    // Truncate email after 16 characters
    const truncatedEmail = invite.email.length > 16 ? invite.email.substring(0, 16) + '...' : invite.email;

    const userCard = document.createElement('div');
    userCard.className = 'dashboard-content user-card accepted-user';
    userCard.setAttribute('data-data-percentage', dataPercentage);
    userCard.setAttribute('data-time-percentage', timePercentage);
    userCard.setAttribute('data-dollar-amount', dollarAmount);
    userCard.setAttribute('data-score', scoreNumber);

    userCard.innerHTML = `
        <div class="user-info-header">
            <div class="user-name">Datashare User ${invite.id}</div>
            <div class="header-icons">
                <div class="edit-icon" onclick="editUserCard(this)" title="Edit user">
                    <i class="fas fa-edit"></i>
                </div>
                <div class="remove-icon" onclick="removeUserCard(this)" title="Remove user">
                    <i class="fas fa-times"></i>
                </div>
            </div>
        </div>
        <div class="email-container">
            <div class="user-email">${truncatedEmail}</div>
            <div class="timestamp">Active Member since ${formatDate(invite.created_at)}</div>
        </div>

        <div class="data-usage">
            <div class="usage-metrics">
                <div class="metric" data-metric="data">
                    <div class="usage_label"><i class="fas fa-database"></i> Data</div>
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
    pausedCards.forEach(card => {        updatePauseDuration(card);
    });
}

// Call this when the page loads to handle any existing paused users
document.addEventListener('DOMContentLoaded', function() {
    console.log('App.js loaded successfully');

    // Initialize theme based on localStorage or default to dark
    const savedTheme = localStorage.getItem('darkMode');
    const isDarkMode = savedTheme === null ? true : savedTheme === 'true';
    toggleTheme(isDarkMode);

    // Load DOTM balance if wallet is connected
    loadDOTMBalance();

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

    // Initialize chart toggle functionality
    document.querySelectorAll('.insight-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            toggleChart(this);
        });
    });

    // Use event delegation for all interactive elements
    document.addEventListener('click', function(e) {
        // Handle logout functionality
        if (e.target.id === 'logoutBtn' || e.target.closest('#logoutBtn')) {
            e.preventDefault();
            console.log('Logout button clicked');

            // Try multiple logout methods
            if (window.firebaseAuth && window.firebaseAuth.signOut) {
                window.firebaseAuth.signOut();
            } else if (typeof firebase !== 'undefined' && firebase.auth) {
                firebase.auth().signOut().then(() => {
                    localStorage.clear();
                    window.location.href = '/';
                }).catch((error) => {
                    console.error('Logout error:', error);
                    localStorage.clear();
                    window.location.href = '/';
                });
            } else {
                // Fallback: clear storage and redirect
                localStorage.clear();
                window.location.href = '/';
            }
            return;
        }

        // Close popup
        if (e.target.classList.contains('popup-overlay') || e.target.classList.contains('popup-close')) {
            hideAddUserPopup();
            return;
        }

        // Handle invite anyone button
        if (e.target.id === 'inviteAnyoneBtn') {
            e.preventDefault();
            showInviteForm();
            return;
        }

        // Handle demo user button
        if (e.target.id === 'demoUserBtn') {
            e.preventDefault();
            createDemoUser();
            return;
        }

        // Handle send invitation button
        if (e.target.id === 'sendInvitationBtn') {
            e.preventDefault();
            sendInvitation();
            return;
        }

        // Handle cancel invitation button
        if (e.target.id === 'cancelInviteBtn') {
            e.preventDefault();
            hideAddUserPopup();
            return;
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

    // Initialize settings toggle functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.id === 'settingsToggle' || e.target.closest('#settingsToggle')) {
            e.preventDefault();
            e.stopPropagation();

            const settingsSubmenu = document.querySelector('.settings-submenu');
            if (settingsSubmenu) {
                // Toggle settings submenu visibility
                if (settingsSubmenu.style.display === 'none' || settingsSubmenu.style.display === '') {
                    settingsSubmenu.style.display = 'block';
                } else {
                    settingsSubmenu.style.display = 'none';
                }
            }
        }

        // Handle language selector changes
        if (e.target.id === 'languageSelect') {
            const selectedLanguage = e.target.value;
            if (typeof setLanguage === 'function') {
                setLanguage(selectedLanguage);
            }
        }

        // Close settings submenu when clicking outside
        if (!e.target.closest('#settingsToggle') && !e.target.closest('.settings-submenu')) {
            const settingsSubmenu = document.querySelector('.settings-submenu');
            if (settingsSubmenu && settingsSubmenu.style.display === 'block') {
                settingsSubmenu.style.display = 'none';
            }
        }
    });

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
    console.log('showAddUserPopup called');

    // Remove existing popup if any
    hideAddUserPopup();

    const popup = document.createElement('div');
    popup.id = 'addUserPopup';
    popup.className = 'popup-overlay';
    popup.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background: rgba(0, 0, 0, 0.7) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        z-index: 999999 !important;
        opacity: 1 !important;
    `;

    popup.innerHTML = `
        <div class="popup-content" style="z-index: 999999; position: relative;">
            <div class="popup-header">
                <h3>Add New Datashare User</h3>
                <button class="popup-close" onclick="hideAddUserPopup()">&times;</button>
            </div>
            <div class="popup-body">
                <div class="invitation-options">
                    <button class="invite-option-btn" id="inviteAnyoneBtn">
                        <i class="fas fa-envelope"></i>
                        <span>Invite Anyone</span>
                        <small>Send invitation via email for a start</small>
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
    console.log('Popup added to body:', popup);

    // Force show with timeout
    setTimeout(() => {
        popup.classList.add('show');
        popup.style.opacity = '1';
    }, 10);

    // Add event listeners
    document.getElementById('inviteAnyoneBtn').addEventListener('click', showInviteForm);
    document.getElementById('demoUserBtn').addEventListener('click', createDemoUser);
}

function hideAddUserPopup() {
    console.log('hideAddUserPopup called');
    const popup = document.getElementById('addUserPopup');
    if (popup) {
        popup.style.opacity = '0';
        setTimeout(() => {
            popup.remove();
        }, 300);
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

// Edit user card function (placeholder for future functionality)
function editUserCard(element) {
    alert('Edit user functionality coming soon!');
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

    // Truncate email after 16 characters
    const truncatedEmail = invite.email.length > 16 ? invite.email.substring(0, 16) + '...' : invite.email;

    const userCard = document.createElement('div');
    userCard.className = 'dashboard-content user-card accepted-user';
    userCard.setAttribute('data-data-percentage', dataPercentage);
    userCard.setAttribute('data-time-percentage', timePercentage);
    userCard.setAttribute('data-dollar-amount', dollarAmount);
    userCard.setAttribute('data-score', scoreNumber);

    userCard.innerHTML = `
        <div class="user-info-header">
            <div class="user-name">Datashare User ${invite.id}</div>
            <div class="header-icons">
                <div class="edit-icon" onclick="editUserCard(this)" title="Edit user">
                    <i class="fas fa-edit"></i>
                </div>
                <div class="remove-icon" onclick="removeUserCard(this)" title="Remove user">
                    <i class="fas fa-times"></i>
                </div>
            </div>
        </div>
        <div class="email-container">
            <div class="user-email">${truncatedEmail}</div>
            <div class="timestamp">Active Member since ${formatDate(invite.created_at)}</div>
        </div>

        <div class="data-usage">
            <div class="usage-metrics">
                <div class="metric" data-metric="data">
                    <div class="usage_label"><i class="fas fa-database"></i> Data</div>
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
    pausedCards.forEach(card => {        updatePauseDuration(card);
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

// Add missing toggleChart function
function toggleChart(element) {
    const insightsCard = element.closest('.insights-card') || element.closest('.dashboard-content');
    const chart = insightsCard ? insightsCard.querySelector('.usage-chart') : null;

    if (chart) {
        const isCurrentlyHidden = chart.style.display === 'none' || chart.style.display === '';

        if (isCurrentlyHidden) {
            chart.style.display = 'block';
            element.textContent = element.textContent.replace('See details', 'Hide details');

            // Initialize chart if it doesn't exist
            if (!chart.querySelector('canvas')) {
                initializeUsageChart(chart);
            }
        } else {
            chart.style.display = 'none';
            element.textContent = element.textContent.replace('Hide details', 'See details');
        }
    }
}

// Function to initialize the usage chart
function initializeUsageChart(chartContainer) {
    const canvas = chartContainer.querySelector('canvas');
    if (!canvas || typeof Chart === 'undefined') {
        console.log('Chart.js not available or canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');

    // Sample data for the usage trend
    const chartData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Data Usage (MB)',
            data: [120, 150, 180, 220, 280, 320, 350],
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Usage (MB)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Day of Week'
                }
            }
        }
    };

    new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: chartOptions
    });
}

// DOTM Balance Functions
async function loadDOTMBalance() {
    const tokenBalancePill = document.getElementById('tokenBalancePill');
    if (!tokenBalancePill) return;

    try {
        // Check if MetaMask is available and connected
        if (typeof window.ethereum !== 'undefined') {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });```javascript
            if (accounts.length > 0) {
                const address = accounts[0];

                // Fetch balance from our API
                const response = await fetch(`/api/token/balance/${address}`);
                const data = await response.json();

                if (data.error) {
                    console.error('Error fetching DOTM balance:', data.error);
                    tokenBalancePill.textContent = '0.00 DOTM';
                } else {
                    // Display balance in the format "100.33 DOTM"
                    tokenBalancePill.textContent = `${data.balance.toFixed(2)} DOTM`;
                }
            } else {                tokenBalancePill.textContent = 'Connect Wallet';
            }
        } else {
            tokenBalancePill.textContent = 'MetaMask Required';
        }
    } catch (error) {
        console.error('Error loading DOTM balance:', error);
        tokenBalancePill.textContent = '0.00 DOTM';
    }
}

// Make functions globally available
window.showAddUserPopup = showAddUserPopup;
window.hideAddUserPopup = hideAddUserPopup;
window.loadInvitesList = loadInvitesList;
window.refreshInvitesList = loadInvitesList;
window.cancelInvitation = cancelInvitation;
window.editUserCard = editUserCard;
window.removeUserCard = removeUserCard;
window.toggleUserPause = toggleUserPause;
window.performSort = performSort;
window.toggleChart = toggleChart;
window.loadDOTMBalance = loadDOTMBalance;

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

// Initialize card stack functionality
function initializeCarousel() {
    console.log('Card stack initialized');

    // Initialize offers on all pages that have an offers section
    console.log('Initializing offers carousel');

    // Check if offers section exists, if not wait a bit
    const offersSection = document.querySelector('.offers-section');
    if (!offersSection) {
        console.log('Offers section not found, waiting...');
        // Try again with longer intervals to avoid spam
        let attempts = 0;
        const maxAttempts = 10;
        const checkInterval = setInterval(() => {
            attempts++;
            const section = document.querySelector('.offers-section');
            if (section || attempts >= maxAttempts) {
                clearInterval(checkInterval);
                if (section) {
                    console.log('Offers section found after', attempts, 'attempts');
                    populateOfferCards();
                    setTimeout(() => {
                        initializeCardStack();
                    }, 200);
                } else {
                    console.log('Offers section not found after maximum attempts');
                }
            }
        }, 1000);
        return;
    }

    // Wait for subscription status to be loaded
    setTimeout(() => {
        populateOfferCards();
        setTimeout(() => {
            initializeCardStack();
        }, 200);
    }, 100);
}

// Global variables for card stack
let currentCardIndex = 2; // Start at the last card (index 2)
let cardStack = [];
let isDragging = false;
let startX = 0;
let currentX = 0;
let cardContainer = null;

function populateOfferCards() {
    const offersSection = document.querySelector('.offers-section');
    if (!offersSection) {
        console.log('Offers section not found');
        return;
    }

    // Define all possible offers
    const allOffers = [
        {
            id: 'global_data',
            title: 'TRULY GLOBAL DATA',
            description: ['10000MB no expiry data for $10', 'Priority fast 5G+ when available', 'Share infinitely with any member', 'Works on most of planet Earth +10km above it'],
            price: '$10',
            buttonText: 'Buy',
            buttonClass: 'btn-primary',
            action: "showConfirmationDrawer(10, 10, 'global_data_10gb')",
            alwaysShow: true
        },
        {
            id: 'basic_membership',
            title: 'Basic Service',
            description: [
                'Access GLOBAL DATA @ $1 a GIG',
                'Works in roaming in 160+ countries',
                'Pay for data 10X less than 4 big telcos'
            ],
            price: '$24/year',
            buttonText: 'Subscribe',
            buttonClass: 'btn-primary',
            action: "showConfirmationDrawer(10, 24, 'basic_membership')",
            showCondition: shouldShowBasicMembership
        },
        {
            id: 'full_membership',
            title: 'Full Service',
            description: ['North America Talk + Text (RCS)', 'Wi-Fi Calling Access Globally', 'Satellite TXT (& E9-1-1)', 'Access GLOBAL DATA @ $1 a GIG'],
            price: '$66/year',
            buttonText: 'Coming Soon',
            buttonClass: 'btn-secondary',
            action: "sendComingSoonNotification()",
            disabled: true,
            alwaysShow: true
        }
    ];

    // Get dismissed offers from localStorage
    const dismissedOffers = JSON.parse(localStorage.getItem('dismissedOffers') || '[]');

    // Always show all offers for all users (ignore dismissal and conditions)
    const availableOffers = allOffers;

    console.log('Available offers:', availableOffers.length);

    // Always ensure we have offers to display
    if (availableOffers.length === 0) {
        console.log('No offers available, this should not happen');
        return;
    }

    // Set the initial card index to the last card
    currentCardIndex = availableOffers.length - 1;

    // Create card stack container with proper styling
    offersSection.innerHTML = `
        <div class="offers-stack-container" id="cardStackContainer" style="position: relative; height: 450px; width: 100%; max-width: 400px; margin: 0 auto;">
            <!-- Cards will be inserted here -->
        </div>
        <div class="card-indicators" id="cardIndicators">
            <!-- Indicators will be inserted here -->
        </div>
    `;

    const stackContainer = document.getElementById('cardStackContainer');
    const indicatorsContainer = document.getElementById('cardIndicators');

    if (!stackContainer || !indicatorsContainer) {
        console.error('Stack container or indicators container not found');
        return;
    }

    // Create cards and indicators
    availableOffers.forEach((offer, index) => {
        // Create card
        const offerCard = document.createElement('div');
        offerCard.className = 'offer-card';
        offerCard.dataset.index = index;

        const descriptions = offer.description.map(desc => `<p>${desc}</p>`).join('');
        const buttonDisabled = offer.disabled ? ' disabled' : '';

        offerCard.innerHTML = `
            <h3>${offer.title}</h3>
            <div class="offer-description">
                ${descriptions}
            </div>
            <div class="price">${offer.price}</div>
            <div style="display: flex; align-items: center; gap: 15px; margin-top: auto; justify-content: space-between; width: 100%;">
                <button class="dismiss-card-btn" onclick="dismissOfferCard('${offer.id}')" title="Dismiss this offer">
                    <i class="fas fa-times"></i><br>
                </button>
                <button class="offer-button ${offer.buttonClass}"${buttonDisabled} onclick="${offer.action}">
                    ${offer.buttonText}
                </button>
            </div>
        `;

        stackContainer.appendChild(offerCard);

        // Create indicator
        const indicator = document.createElement('div');
        indicator.className = 'indicator-dot';
        indicator.dataset.index = index;
        indicator.addEventListener('click', () => goToCard(index));
        indicatorsContainer.appendChild(indicator);
    });

    cardStack = Array.from(stackContainer.querySelectorAll('.offer-card'));
    console.log('Created card stack with', cardStack.length, 'cards');
    updateCardPositions();
}

function initializeCardStack() {
    cardContainer = document.getElementById('cardStackContainer');
    if (!cardContainer) {
        console.log('Card container not found');
        return;
    }

    console.log('Initializing card stack with', cardStack.length, 'cards');

    // Remove existing listeners first
    cardContainer.removeEventListener('touchstart', handleTouchStart);
    cardContainer.removeEventListener('touchmove', handleTouchMove);
    cardContainer.removeEventListener('touchend', handleTouchEnd);
    cardContainer.removeEventListener('mousedown', handleMouseStart);

    // Add touch event listeners with proper options
    cardContainer.addEventListener('touchstart', handleTouchStart, { passive: false });
    cardContainer.addEventListener('touchmove', handleTouchMove, { passive: false });
    cardContainer.addEventListener('touchend', handleTouchEnd, { passive: false });

    // Add mouse event listeners for desktop
    cardContainer.addEventListener('mousedown', handleMouseStart);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseEnd);

    // Prevent default drag behavior
    cardContainer.addEventListener('dragstart', e => e.preventDefault());
    cardContainer.addEventListener('selectstart', e => e.preventDefault());

    updateCardPositions();
}

function handleTouchStart(e) {
    if (e.touches.length > 1) return;

    // Don't prevent default on buttons
    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
        return;
    }

    e.preventDefault();
    e.stopPropagation();
    console.log('Touch start detected at:', e.touches[0].clientX);
    startSwipe(e.touches[0].clientX);
}

function handleTouchMove(e) {
    if (e.touches.length > 1 || !isDragging) return;
    e.preventDefault();
    e.stopPropagation();
    moveSwipe(e.touches[0].clientX);
}

function handleTouchEnd(e) {
    if (!isDragging) return;
    e.preventDefault();
    e.stopPropagation();
    console.log('Touch end detected');
    endSwipe();
}

function handleMouseStart(e) {
    // Only handle left mouse button
    if (e.button !== 0) return;

    // Don't prevent default on buttons
    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
        return;
    }

    e.preventDefault();
    e.stopPropagation();
    console.log('Mouse start detected at:', e.clientX);
    startSwipe(e.clientX);
}

function handleMouseMove(e) {
    if (!isDragging) return;
    e.preventDefault();
    moveSwipe(e.clientX);
}

function handleMouseEnd(e) {
    if (!isDragging) return;
    e.preventDefault();
    console.log('Mouse end detected');
    endSwipe();
}

function startSwipe(x) {
    console.log('Starting swipe at', x);
    isDragging = true;
    startX = x;
    currentX = x;

    const topCard = cardStack[currentCardIndex];
    if (topCard) {
        topCard.classList.add('swiping');
        console.log('Added swiping class to card', currentCardIndex);
    }
}

function moveSwipe(x) {
    if (!isDragging) return;

    currentX = x;
    const deltaX = currentX - startX;
    const topCard = cardStack[currentCardIndex];

    if (topCard && Math.abs(deltaX) > 5) { // Add small threshold to prevent micro-movements
        const rotation = deltaX * 0.08; // Reduced rotation for smoother feel
        const opacity = Math.max(0.8, 1 - Math.abs(deltaX) / 400);

        topCard.style.transform = `translateX(${deltaX}px) rotate(${rotation}deg) scale(1)`;
        topCard.style.opacity = opacity;
        topCard.style.zIndex = '15';

        console.log('Moving card with deltaX:', deltaX);
    }
}

function endSwipe() {
    if (!isDragging) return;

    console.log('Ending swipe');
    isDragging = false;
    const deltaX = currentX - startX;
    const threshold = 60; // Reduced threshold for easier swiping

    const topCard = cardStack[currentCardIndex];
    if (topCard) {
        topCard.classList.remove('swiping');
    }

    if (Math.abs(deltaX) > threshold) {
        console.log('Threshold exceeded, deltaX:', deltaX);
        // Swipe in either direction dismisses the card
        dismissCurrentCard();
    } else {
        console.log('Snapping back to center');
        // Snap back to center
        if (topCard) {
            topCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            topCard.style.transform = '';
            topCard.style.opacity = '';
            topCard.style.zIndex = '';

            // Remove transition after animation
            setTimeout(() => {
                if (topCard) {
                    topCard.style.transition = '';
                }
            }, 300);
        }
    }
}

function goToNextCard() {
    if (currentCardIndex < cardStack.length - 1) {
        // Animate current card out
        const currentCard = cardStack[currentCardIndex];
        if (currentCard) {
            currentCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            currentCard.style.transform = 'translateX(-100%) rotate(-10deg)';
            currentCard.style.opacity = '0';
        }

        currentCardIndex++;

        // Update positions after a short delay
        setTimeout(() => {
            updateCardPositions();
        }, 150);
    }
}

function goToPreviousCard() {
    if (currentCardIndex > 0) {
        // Animate current card out
        const currentCard = cardStack[currentCardIndex];
        if (currentCard) {
            currentCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            currentCard.style.transform = 'translateX(100%) rotate(10deg)';
            currentCard.style.opacity = '0';
        }

        currentCardIndex--;

        // Update positions after a short delay
        setTimeout(() => {
            updateCardPositions();
        }, 150);
    }
}

function goToCard(index) {
    if (index >= 0 && index < cardStack.length && index !== currentCardIndex) {
        const direction = index > currentCardIndex ? -1 : 1;
        const currentCard = cardStack[currentCardIndex];

        if (currentCard) {
            currentCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            currentCard.style.transform = `translateX(${direction * 100}%) rotate(${direction * -10}deg)`;
            currentCard.style.opacity = '0';
        }

        currentCardIndex = index;

        setTimeout(() => {
            updateCardPositions();
        }, 150);
    }
}

function updateCardPositions() {
    console.log('Updating card positions, current index:', currentCardIndex);

    cardStack.forEach((card, index) => {
        // Clear any transition and inline styles
        card.style.transition = '';
        card.style.transform = '';
        card.style.opacity = '';
        card.style.zIndex = '';

        // Remove all position classes
        card.classList.remove('top-card', 'behind-card', 'hidden-card');

        if (index === currentCardIndex) {
            card.classList.add('top-card');
            card.style.zIndex = '10';
            card.style.opacity = '1';
            console.log('Setting card', index, 'as top card');
        } else if (index === currentCardIndex + 1) {
            card.classList.add('behind-card');
            card.style.zIndex = '9';
            card.style.opacity = '0.8';
            console.log('Setting card', index, 'as behind card');
        } else {
            card.classList.add('hidden-card');
            card.style.zIndex = '8';
            card.style.opacity = '0';
            console.log('Setting card', index, 'as hidden card');
        }
    });

    // Update indicators
    const indicators = document.querySelectorAll('.indicator-dot');
    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentCardIndex);
    });
}

// Dismiss current card function (for swipe dismissal)
function dismissCurrentCard() {
    const currentCard = cardStack[currentCardIndex];
    if (!currentCard) return;

    // Find the offer ID from the card's button onclick attribute
    const offerButton = currentCard.querySelector('.offer-button[onclick]');
    let offerId = null;

    if (offerButton) {
        const onclickAttr = offerButton.getAttribute('onclick');
        // Extract offer ID from onclick attribute
        if (onclickAttr.includes('global_data_10gb')) {
            offerId = 'global_data';
        } else if (onclickAttr.includes('basic_membership')) {
            offerId = 'basic_membership';
        } else if (onclickAttr.includes('full_membership')) {
            offerId = 'full_membership';
        }
    }

    if (offerId) {
        // Get current dismissed offers
        const dismissedOffers = JSON.parse(localStorage.getItem('dismissedOffers') || '[]');

        // Add this offer to dismissed list if not already there
        if (!dismissedOffers.includes(offerId)) {
            dismissedOffers.push(offerId);
            localStorage.setItem('dismissedOffers', JSON.stringify(dismissedOffers));
        }

        console.log('Dismissing offer:', offerId);
    }

    // Animate the card out based on swipe direction
    const deltaX = currentX - startX;
    const direction = deltaX > 0 ? 1 : -1;

    currentCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
    currentCard.style.transform = `translateX(${direction * 100}%) rotate(${direction * -10}deg) scale(0.8)`;
    currentCard.style.opacity = '0';

    // After animation, repopulate the cards
    setTimeout(() => {
        populateOfferCards();
        setTimeout(() => {
            initializeCardStack();
        }, 100);
    }, 300);
}

// Dismiss offer card function (for button dismissal)
function dismissOfferCard(offerId) {
    // Get current dismissed offers
    const dismissedOffers = JSON.parse(localStorage.getItem('dismissedOffers') || '[]');

    // Add this offer to dismissed list if not already there
    if (!dismissedOffers.includes(offerId)) {
        dismissedOffers.push(offerId);
        localStorage.setItem('dismissedOffers', JSON.stringify(dismissedOffers));
    }

    // Find the card to dismiss
    const currentCard = cardStack[currentCardIndex];
    if (currentCard && currentCard.querySelector(`[onclick*="${offerId}"]`)) {
        // Animate the card out
        currentCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
        currentCard.style.transform = 'translateX(-100%) rotate(-10deg) scale(0.8)';
        currentCard.style.opacity = '0';

        // After animation, repopulate the cards
        setTimeout(() => {
            populateOfferCards();
            setTimeout(() => {
                initializeCardStack();
            }, 100);
        }, 300);
    }
}

// Make card stack functions globally available
window.goToNextCard = goToNextCard;
window.goToPreviousCard = goToPreviousCard;
window.goToCard = goToCard;
window.dismissOfferCard = dismissOfferCard;
window.dismissCurrentCard = dismissCurrentCard;

// Function to clear all dismissed offers
function clearDismissedOffers() {
    localStorage.removeItem('dismissedOffers');
    populateOfferCards();
    setTimeout(() => {
        initializeCardStack();
    }, 100);
}

window.clearDismissedOffers = clearDismissedOffers;

function shouldShowBasicMembership() {
    // Always show basic membership offer for all users
    return true;
}

// Update subscription status when it's received
function updateSubscriptionStatus(subscriptionData) {
    currentSubscriptionStatus = subscriptionData;
    console.log('Subscription status updated:', subscriptionData);

    // Re-populate offer cards if carousel is already initialized
    if (document.getElementById('offersGrid')) {
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
            if (data.email_sent && data.iccid) {
                // Show success message with ICCID details
                alert(`Beta eSIM Ready!\n\nICCID: ${data.iccid}\n\nActivation details have been sent to your email. Check your inbox for complete instructions.`);
                updateBetaStatus(data.status, data.message);
            } else {
                updateBetaStatus(data.status, data.message);
            }
        } else {
            alert('Error enrolling in beta: ' + (data.message || 'Unknown error'));
            betaEnrollBtn.disabled = false;
            betaEnrollBtn.textContent = 'Request BETA eSIM';
        }
    })
    .catch(error => {
        console.error('Error enrolling in beta:', error);
        alert('Error enrolling in beta. Please try again.');
        betaEnrollBtn.disabled = false;
        betaEnrollBtn.textContent = 'Request BETA eSIM';
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
            betaStatusText.style.color = '#28a745';

            // Show resend link
            let resendContainer = document.getElementById('resendContainer');
            if (!resendContainer) {
                resendContainer = document.createElement('div');
                resendContainer.id = 'resendContainer';
                resendContainer.style.marginTop = '5px';

                const resendLink = document.createElement('a');
                resendLink.href = '#';
                resendLink.textContent = 'Resend';
                resendLink.style.color = '#007bff';
                resendLink.style.textDecoration = 'underline';
                resendLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    send_esim_ready_email();
                });

                resendContainer.appendChild(resendLink);
                betaStatus.appendChild(resendContainer);
            } else {
                resendContainer.style.display = 'block'; // Ensure it's visible
            }

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
                <span data-translate="humanHelp">Human help:</span>
            </div>
            <div class="help-option-content">
                <div class="agent-status">
                    <span class="agent-availability">Super agent available in <span class="countdown-timer" style="color: #28a745; font-weight: bold;">4:20</span></span>
                </div>
                <button id="orderCallbackBtn" class="callback-btn" data-translate="orderCallback">Order callback</button>
            </div>
            <button id="chatWithAgentBtn" class="chat-btn" data-translate="chatWithAgent">Chat with Agent</button>
        </div>

        <div class="ai-help-section">
            <div class="help-option-header">
                <i class="fas fa-robot"></i>
                <span data-translate="useAiHelp">Use AI help:</span>
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

    // Apply translations to the newly created content
    setTimeout(() => {
        updatePageTranslations();
    }, 0);

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

// Function to resend the eSIM ready email
function send_esim_ready_email() {
    const firebaseUid = localStorage.getItem('userId');
    if (!firebaseUid) {
        alert('Please sign in to resend the email.');
        return;
    }

    fetch('/api/resend-esim-email', {
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
            alert('eSIM Ready email resent successfully!');
        } else {
            alert('Error resending eSIM Ready email: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error resending eSIM Ready email:', error);
        alert('Error resending eSIM Ready email. Please try again.');
    });
}

// Modify updateBetaStatus function to handle resend link
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
            betaStatusText.style.color = '#28a745';

            // Show resend link
            let resendContainer = document.getElementById('resendContainer');
            if (!resendContainer) {
                resendContainer = document.createElement('div');
                resendContainer.id = 'resendContainer';
                resendContainer.style.marginTop = '5px';

                const resendLink = document.createElement('a');
                resendLink.href = '#';
                resendLink.textContent = 'Resend';
                resendLink.style.color = '#007bff';
                resendLink.style.textDecoration = 'underline';
                resendLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    send_esim_ready_email();
                });

                resendContainer.appendChild(resendLink);
                betaStatus.appendChild(resendContainer);
            } else {
                resendContainer.style.display = 'block'; // Ensure it's visible
            }

            break;
        case 'enrolled':
            betaEnrollBtn.style.display = 'none';
            betaStatus.style.display = 'block';
            betaStatusText.textContent = message || 'Beta enrollment complete';
            break;
    }
}

// Function to show notifications
function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#007bff'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000000;
        max-width: 350px;
        word-wrap: break-word;
        font-size: 14px;
        line-height: 1.4;
        animation: slideInRight 0.3s ease-out;
    `;

    notification.textContent = message;

    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        float: right;
        font-size: 18px;
        cursor: pointer;
        margin-left: 10px;
        padding: 0;
        line-height: 1;
    `;

    closeBtn.onclick = () => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    };

    notification.appendChild(closeBtn);
    document.body.appendChild(notification);

    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);
    }
}

// Make functions globally available
window.showNotification = showNotification;
} // Close the conditional block