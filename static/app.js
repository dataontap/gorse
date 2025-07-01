
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

function setActiveCarouselItem(index) {
    // Placeholder function to prevent console errors
    console.log('Carousel item', index, 'selected');
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
    console.log('Help desk script loaded successfully');

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

                    // Create redesigned help content
                    helpSection.innerHTML = `
                        <div class="help-content-redesigned">
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
                        </div>
                    `;

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
            refreshInvitesList();
        }, 1000);
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
            body.classList.remove('light-mode');
            if (darkModePreference === null) {
                localStorage.setItem('darkMode', 'true');
            }
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
            if (textSpan) textSpan.textContent = 'Light Mode';
        } else {
            body.classList.remove('dark-mode');
            body.classList.add('light-mode');
            if (icon) {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
            if (textSpan) textSpan.textContent = 'Dark Mode';
        }

        darkModeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const isDark = body.classList.contains('dark-mode');

            if (isDark) {
                // Switch to light mode
                body.classList.remove('dark-mode');
                body.classList.add('light-mode');
                if (icon) {
                    icon.classList.remove('fa-sun');
                    icon.classList.add('fa-moon');
                }
                if (textSpan) {
                    textSpan.textContent = 'Dark Mode';
                }
                localStorage.setItem('darkMode', 'false');
            } else {
                // Switch to dark mode
                body.classList.remove('light-mode');
                body.classList.add('dark-mode');
                if (icon) {
                    icon.classList.remove('fa-moon');
                    icon.classList.add('fa-sun');
                }
                if (textSpan) {
                    textSpan.textContent = 'Light Mode';
                }
                localStorage.setItem('darkMode', 'true');
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

// Dashboard functions for offer cards and user data
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

// Chart toggle functionality for dashboard
function toggleChart(link) {
    const dataUsage = link.closest('.data-usage');
    const chart = dataUsage.querySelector('.usage-chart');

    // Store current scroll position relative to the link element
    const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const linkRect = link.getBoundingClientRect();
    const linkOffsetFromTop = linkRect.top + currentScrollTop;

    if (chart.style.display === 'none' || chart.style.display === '') {
        chart.style.display = 'block';
        link.textContent = 'Hide details';

        // Initialize chart if needed
        if (!chart.querySelector('canvas').chart) {
            const ctx = chart.querySelector('canvas').getContext('2d');
            const newChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Usage Trend',
                        data: [12, 19, 15, 25, 22, 18, 30],
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        }
                    }
                }
            });
            chart.querySelector('canvas').chart = newChart;
        }

        // Maintain scroll position after chart expands
        setTimeout(() => {
            window.scrollTo(0, linkOffsetFromTop - linkRect.top);
        }, 10);
    } else {
        chart.style.display = 'none';
        link.textContent = 'See details';
    }
}

// Add User Popup Functions
function showAddUserPopup() {
    // Remove existing popup if any
    const existingPopup = document.getElementById('addUserPopup');
    if (existingPopup) {
        existingPopup.remove();
    }

    const popup = document.createElement('div');
    popup.id = 'addUserPopup';
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-header">
                <h3>Add New User</h3>
                <button class="popup-close">&times;</button>
            </div>
            <div class="popup-body">
                <div class="invitation-options">
                    <button id="inviteAnyoneBtn" class="invite-option-btn">
                        <i class="fas fa-envelope"></i>
                        <span>Invite Anyone</span>
                        <small>Send invitation email</small>
                    </button>
                    <button id="demoUserBtn" class="invite-option-btn">
                        <i class="fas fa-user-plus"></i>
                        <span>Demo User</span>
                        <small>Create random demo user</small>
                    </button>
                </div>
                <div id="inviteForm" class="invite-form" style="display: none;">
                    <h4>Send Invitation</h4>
                    <div class="form-group">
                        <label for="inviteEmail">Email Address:</label>
                        <input type="email" id="inviteEmail" placeholder="Enter email address" required>
                    </div>
                    <div class="form-group">
                        <label for="inviteMessage">Personal Message (optional):</label>
                        <textarea id="inviteMessage" placeholder="Add a personal message to the invitation" rows="3"></textarea>
                    </div>
                    <div class="form-actions">
                        <button id="sendInvitationBtn" class="btn-primary">Send Invitation</button>
                        <button id="cancelInviteBtn" class="btn-secondary">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(popup);

    // Add animation
    setTimeout(() => {
        popup.classList.add('show');
    }, 10);
}

function hideAddUserPopup() {
    const popup = document.getElementById('addUserPopup');
    if (popup) {
        popup.classList.remove('show');
        setTimeout(() => {
            popup.remove();
        }, 300);
    }
}

function showInviteForm() {
    const options = document.querySelector('.invitation-options');
    const form = document.getElementById('inviteForm');

    if (options && form) {
        options.style.display = 'none';
        form.style.display = 'block';

        // Focus on email input
        const emailInput = document.getElementById('inviteEmail');
        if (emailInput) {
            emailInput.focus();
        }
    }
}

function createDemoUser() {
    // Generate random demo user data
    const demoEmails = [
        'demo.user1@example.com',
        'test.user2@example.com',
        'sample.user3@example.com',
        'beta.tester4@example.com',
        'trial.user5@example.com'
    ];

    const randomEmail = demoEmails[Math.floor(Math.random() * demoEmails.length)] + '.' + Date.now();

    // Send invitation for demo user
    sendInvitationToAPI(randomEmail, 'Auto-generated demo user invitation', true);
}

function sendInvitation() {
    const emailInput = document.getElementById('inviteEmail');
    const messageInput = document.getElementById('inviteMessage');

    if (!emailInput || !emailInput.value.trim()) {
        alert('Please enter a valid email address.');
        return;
    }

    const email = emailInput.value.trim();
    const message = messageInput ? messageInput.value.trim() : '';

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address.');
        return;
    }

    sendInvitationToAPI(email, message, false);
}

function sendInvitationToAPI(email, message, isDemoUser) {
    const firebaseUid = localStorage.getItem('userId') || null;

    fetch('/api/send-invitation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            message: message,
            isDemoUser: isDemoUser,
            firebaseUid: firebaseUid
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(isDemoUser ? 'Demo user created successfully!' : 'Invitation sent successfully!');
            hideAddUserPopup();

            // Refresh invites list if on dashboard
            if (typeof refreshInvitesList === 'function') {
                refreshInvitesList();
            }
        } else {
            alert('Error: ' + (data.message || 'Failed to send invitation'));
        }
    })
    .catch(error => {
        console.error('Error sending invitation:', error);
        alert('Error sending invitation. Please try again.');
    });
}

function refreshInvitesList() {
    const firebaseUid = localStorage.getItem('userId') || null;

    fetch(`/api/invites?firebaseUid=${firebaseUid}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayInvitesList(data.invites);
        }
    })
    .catch(error => {
        console.error('Error fetching invites:', error);
    });
}

function displayInvitesList(invites) {
    console.log('Invites to display:', invites);

    const recentInvitationsSection = document.getElementById('recentInvitationsSection');
    const invitationsList = document.getElementById('invitationsList');
    const acceptedUsersContainer = document.getElementById('acceptedUsersContainer');

    if (!invites || invites.length === 0) {
        if (recentInvitationsSection) {
            recentInvitationsSection.style.display = 'none';
        }
        return;
    }

    // Show the section
    if (recentInvitationsSection) {
        recentInvitationsSection.style.display = 'block';
    }

    // Filter invites by status
    const pendingInvites = invites.filter(invite => 
        invite.invitation_status === 'invite_sent' || invite.invitation_status === 're_invited'
    );
    const acceptedInvites = invites.filter(invite => 
        invite.invitation_status === 'invite_accepted'
    );

    // Display pending invitations
    if (invitationsList && pendingInvites.length > 0) {
        invitationsList.innerHTML = pendingInvites.map(invite => `
            <div class="invitation-item">
                <div class="invitation-info">
                    <div class="invitation-email">${invite.email}</div>
                    <div class="invitation-date">Sent ${new Date(invite.created_at).toLocaleDateString()}</div>
                </div>
                <div style="display: flex; align-items: center;">
                    <span class="invitation-status status-${invite.invitation_status.replace('_', '-')}">
                        ${invite.invitation_status.replace('_', ' ')}
                    </span>
                    <button class="cancel-invite-btn" onclick="cancelInvitation(${invite.id})" title="Cancel invitation">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } else if (invitationsList) {
        invitationsList.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">No pending invitations</div>';
    }

    // Display accepted invitations as user cards
    if (acceptedUsersContainer && acceptedInvites.length > 0) {
        acceptedUsersContainer.innerHTML = acceptedInvites.map(invite => {
            const userData = generateRandomUserData(invite.email);
            return `
                <div class="accepted-user-card">
                    <div class="accepted-user-header">
                        <div class="accepted-user-info">
                            <div class="accepted-user-name">${userData.name}</div>
                            <div class="accepted-user-email">${invite.email}</div>
                        </div>
                        <div class="invitation-status status-invite-accepted">
                            Joined ${new Date(invite.accepted_at).toLocaleDateString()}
                        </div>
                    </div>
                    <div class="accepted-user-stats">
                        <div class="stat-item">
                            <div class="stat-value">${userData.dataUsage}%</div>
                            <div class="stat-label">Data Used</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${userData.screenTime}h</div>
                            <div class="stat-label">Screen Time</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">$${userData.cost}</div>
                            <div class="stat-label">Monthly Cost</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${userData.location}</div>
                            <div class="stat-label">Location</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else if (acceptedUsersContainer) {
        acceptedUsersContainer.innerHTML = '';
    }
}

function generateRandomUserData(email) {
    // Generate consistent random data based on email
    const hash = email.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
    }, 0);

    const abs = Math.abs(hash);

    // Generate random name
    const firstNames = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn', 'Sage', 'River'];
    const lastNames = ['Smith', 'Johnson', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas'];

    const firstName = firstNames[abs % firstNames.length];
    const lastName = lastNames[(abs * 7) % lastNames.length];

    // Generate random but realistic data
    const dataUsage = 15 + (abs % 70); // 15-85%
    const screenTime = 2 + (abs % 10); // 2-12 hours
    const cost = 25 + (abs % 50); // $25-75

    const locations = ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Ottawa', 'Edmonton', 'Winnipeg', 'Quebec', 'Hamilton', 'London'];
    const location = locations[abs % locations.length];

    return {
        name: `${firstName} ${lastName}`,
        dataUsage,
        screenTime,
        cost,
        location
    };
}

function cancelInvitation(inviteId) {
    if (!confirm('Are you sure you want to cancel this invitation?')) {
        return;
    }

    const firebaseUid = localStorage.getItem('userId') || null;

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
            alert('Invitation cancelled successfully!');

            // Refresh invites list
            if (typeof refreshInvitesList === 'function') {
                refreshInvitesList();
            }
        } else {
            alert('Error: ' + (data.message || 'Failed to cancel invitation'));
        }
    })
    .catch(error => {
        console.error('Error cancelling invitation:', error);
        alert('Error cancelling invitation. Please try again.');
    });
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
