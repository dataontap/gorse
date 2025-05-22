// Update token value pill on all pages
// Initialize session user (always user #1)
if (!localStorage.getItem('userId')) {
    localStorage.setItem('userId', '1');
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize wallet data if not present
    if (!localStorage.getItem('walletBalance')) {
        localStorage.setItem('walletBalance', '0.0');
    }

    const tokenValuePill = document.querySelector('.token-value-pill');

    if (tokenValuePill) {
        // Function to create sparkle animation
        function createSparkle(element) {
            const rect = element.getBoundingClientRect();

            for (let i = 0; i < 5; i++) {
                const sparkle = document.createElement('div');
                sparkle.classList.add('sparkle');

                // Random position around the element
                const x = rect.left + Math.random() * rect.width;
                const y = rect.top + Math.random() * rect.height;

                sparkle.style.left = `${x}px`;
                sparkle.style.top = `${y}px`;
                sparkle.style.width = `${10 + Math.random() * 10}px`;
                sparkle.style.height = sparkle.style.width;

                document.body.appendChild(sparkle);

                // Remove the sparkle after animation completes
                setTimeout(() => {
                    document.body.removeChild(sparkle);
                }, 800);
            }
        }

        // Add CSS for animations
        const style = document.createElement('style');
        style.textContent = `
            .token-value-pill {
                background-color: #f0f0f0;
                border-radius: 20px;
                padding: 4px 12px;
                display: inline-flex;
                align-items: center;
                font-weight: 500;
                transition: background-color 0.3s, transform 0.2s;
            }
            .token-value-pill.updating {
                animation: pulse 1s ease-in-out;
            }
            @keyframes pulse {
                0% { background-color: #f0f0f0; transform: scale(1); }
                50% { background-color: #e0f7fa; transform: scale(1.05); }
                100% { background-color: #f0f0f0; transform: scale(1); }
            }
            .sparkle {
                position: absolute;
                pointer-events: none;
                background-image: radial-gradient(circle, #fff 10%, transparent 60%);
                border-radius: 50%;
                opacity: 0;
                animation: sparkle 0.8s ease-in-out forwards;
            }
            @keyframes sparkle {
                0% { transform: scale(0); opacity: 0; }
                50% { opacity: 0.8; }
                100% { transform: scale(1.5); opacity: 0; }
            }
        `;
        document.head.appendChild(style);

        // Function to update the token value display
        async function updateTokenValue() {
            try {
                const response = await fetch('/api/token/price');
                const data = await response.json();

                if (data.price) {
                    // Add updating animation
                    tokenValuePill.classList.add('updating');

                    // Create sparkle effect
                    createSparkle(tokenValuePill);

                    // Update content
                    tokenValuePill.textContent = `1 DOTM = $${data.price.toFixed(2)}`;

                    // Remove animation class after animation completes
                    setTimeout(() => {
                        tokenValuePill.classList.remove('updating');
                    }, 1000);
                }
            } catch (error) {
                console.error('Error fetching token price:', error);
            }
        }

        // Update immediately
        updateTokenValue();

        // Then update every minute
        setInterval(updateTokenValue, 60000);
    }
});

// Add refresh functionality to dot indicator
function initializeDotRefresh() {
    const dotIndicator = document.querySelector('.dot-indicator');
    if (!dotIndicator) return;

    let pressTimer;
    let isLongPress = false;

    // Long press detection
    dotIndicator.addEventListener('mousedown', (e) => {
        pressTimer = setTimeout(() => {
            isLongPress = true;
            refreshDataAmount();
        }, 1000); // 1 second long press
    });

    dotIndicator.addEventListener('touchstart', (e) => {
        pressTimer = setTimeout(() => {
            isLongPress = true;
            refreshDataAmount();
        }, 1000); // 1 second long press
    });

    // Clear timer if press is canceled
    dotIndicator.addEventListener('mouseup', () => {
        clearTimeout(pressTimer);
        isLongPress = false;
    });

    dotIndicator.addEventListener('touchend', () => {
        clearTimeout(pressTimer);
        isLongPress = false;
    });

    dotIndicator.addEventListener('mouseleave', () => {
        clearTimeout(pressTimer);
        isLongPress = false;
    });
}

function refreshDataAmount() {
    const dataDisplay = document.getElementById('dataDisplay');
    const dotIndicator = document.querySelector('.dot-indicator');

    if (!dataDisplay || !dotIndicator) return;

    // Add pulse animation
    dotIndicator.classList.add('pulse');

    // Simulate loading
    setTimeout(() => {
        // Get current amount from localStorage or API
        let currentAmount = parseFloat(localStorage.getItem('walletBalance') || '0.0');

        // Update the display
        dataDisplay.innerHTML = `${currentAmount.toFixed(1)}<span>GB</span>`;
        dataDisplay.style.display = 'block';

        // Create sparkle effect
        createSparkle(dotIndicator);

        // Remove pulse after animation completes
        setTimeout(() => {
            dotIndicator.classList.remove('pulse');
        }, 1000);
    }, 500);
}

// Add scroll animation for offer cards
function checkOfferCardsInView() {
    const offerCards = document.querySelectorAll('.offer-card');
    const windowHeight = window.innerHeight;

    offerCards.forEach(card => {
        const rect = card.getBoundingClientRect();
        // Check if card is in the center of the viewport
        if (rect.top <= windowHeight/2 && rect.bottom >= windowHeight/2) {
            card.classList.add('in-view');
        } else {
            card.classList.remove('in-view');
        }
    });
}

// Add scroll event listener
document.addEventListener('DOMContentLoaded', function() {
    window.addEventListener('scroll', checkOfferCardsInView, { passive: true });

    // Check on initial load as well
    setTimeout(checkOfferCardsInView, 500);
});

// Initialize arrays at the top level
const firstNames = ['Jenny', 'Mike', 'Sarah', 'Alex', 'Emma', 'James', 'Lisa', 'David'];
const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'];
const userTypes = ['Admin', 'Parent', 'Child', 'Family', 'Friend', 'Device', 'Car', 'Pet'];

document.addEventListener('DOMContentLoaded', () => {
    initializeAddUser();
    initializeSortControls();
    initializeBackToTop();
    initializeButtons();
    initializeDarkMode();
    initializeMenu();
    initializeProfileDropdown();
    updateSortControlsVisibility();
    initializeCarousel();
    checkPurchasedMemberships();
    updateCarouselControlsVisibility();
    initializeDotRefresh();
    loadDataFromSession();
});

// Load data from session storage
function loadDataFromSession() {
    const dataDisplay = document.getElementById('dataDisplay');
    const globalStatus = document.getElementById('globalStatus');

    if (dataDisplay) {
        // First show cached data immediately for better UX
        const walletBalance = localStorage.getItem('walletBalance');
        if (walletBalance) {
            const amount = parseFloat(walletBalance);
            dataDisplay.innerHTML = `${amount.toFixed(1)}<span>GB</span>`;
            dataDisplay.style.display = 'block';

            if (globalStatus) {
                globalStatus.style.display = 'block';
            }
        }

        // Then fetch fresh data from API
        fetchUserDataBalance();
    }
}

// Fetch current user data balance from API
function fetchUserDataBalance() {
    const userId = localStorage.getItem('userId') || '1';

    fetch(`/api/user/data-balance?userId=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data) {
                    // Update localStorage
                    if (data.dataBalance !== null && data.dataBalance !== undefined) {
                        localStorage.setItem('walletBalance', data.dataBalance.toString());
                    } else {
                        localStorage.removeItem('walletBalance');
                    }

                    // Update display if on dashboard
                    const dataDisplay = document.getElementById('dataDisplay');
                    if (dataDisplay) {
                        if (data.dataBalance === null || data.dataBalance === undefined) {
                            dataDisplay.innerHTML = `--<span>GB</span>`;
                        } else {
                            dataDisplay.innerHTML = `${data.dataBalance.toFixed(1)}<span>GB</span>`;
                        }
                        dataDisplay.style.display = 'block';

                        const globalStatus = document.getElementById('globalStatus');
                        if (globalStatus) {
                            globalStatus.style.display = 'block';
                        }
                    }
                }
        })
        .catch(error => {
            console.error('Error fetching data balance:', error);
            // No need to show error to user, just use cached data
        });
}

function initializeCarousel() {
    const carousel = document.getElementById('promotionsCarousel');
    if (!carousel) return;

    let touchStartX = 0;
    let touchEndX = 0;

    carousel.addEventListener('touchstart', e => {
        touchStartX = e.touches[0].clientX;
    }, false);

    carousel.addEventListener('touchmove', e => {
        touchEndX = e.touches[0].clientX;
    }, false);

    carousel.addEventListener('touchend', () => {
        handleSwipe();
    }, false);

    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
            const items = carousel.querySelectorAll('.carousel-item');
            const activeItem = carousel.querySelector('.carousel-item.active');

            if (!activeItem || items.length === 0) return;

            const currentIndex = Array.from(items).indexOf(activeItem);

            items.forEach(item => {
                if (item && item.classList) {
                    item.classList.remove('active');
                }
            });

            if (diff > 0) { // Swipe left
                const nextIndex = (currentIndex + 1) % items.length;
                if (items[nextIndex] && items[nextIndex].classList) {
                    items[nextIndex].classList.add('active');
                }
            } else { // Swipe right
                const prevIndex = (currentIndex - 1 + items.length) % items.length;
                if (items[prevIndex] && items[prevIndex].classList) {
                    items[prevIndex].classList.add('active');
                }
            }
        }
    }
}

function initializeProfileDropdown() {
    const profileDropdown = document.querySelector('.profile-dropdown');
    let helpTimerInterval;
    let helpStartTime;
    let helpTimeRemaining = 260; // 4 minutes and 20 seconds

    // Help section toggle
    const helpToggle = document.getElementById('helpToggle');
    const helpSection = document.querySelector('.help-section');
    const helpTimer = document.getElementById('helpTimer');
    const phoneIcon = document.getElementById('helpPhoneIcon');

    if (helpToggle && helpSection && helpTimer) {
        helpToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const isExpanded = helpSection.classList.contains('expanded');

            // Toggle help section
            helpSection.style.display = isExpanded ? 'none' : 'block';
            helpSection.classList.toggle('expanded');

            // Toggle active class for red color
            helpToggle.classList.toggle('active', !isExpanded);

            // Handle timer
            if (!isExpanded) {
                // Start timer
                helpTimer.style.display = 'inline';
                helpTimeRemaining = 260; // Reset to 4 minutes and 20 seconds
                updateHelpTimer();
                helpTimerInterval = setInterval(updateHelpTimer, 1000);

                // Hide phone icon initially
                if (phoneIcon) {
                    phoneIcon.style.display = 'none';
                }
            } else {
                // Stop timer
                clearInterval(helpTimerInterval);
                helpTimer.style.display = 'none';

                // Hide phone icon when help is closed
                if (phoneIcon) {
                    phoneIcon.style.display = 'none';
                }
            }

// Handle notification permission
document.addEventListener('DOMContentLoaded', function() {
    const notificationToggle = document.getElementById('notificationToggle');
    if (notificationToggle) {
        // Check initial permission status
        if (Notification.permission === 'granted') {
            notificationToggle.checked = true;
        } else if (Notification.permission === 'denied') {
            notificationToggle.checked = false;
            notificationToggle.disabled = true;
        }

        // Handle toggle changes
        notificationToggle.addEventListener('change', function() {
            if (this.checked) {
                Notification.requestPermission().then(function(permission) {
                    if (permission !== 'granted') {
                        notificationToggle.checked = false;
                    }
                });
            }
        });
    }
});

// Test notification function (for testing purposes)
window.sendTestNotification = function() {
    const statusElement = document.getElementById('notification-status');
    statusElement.textContent = 'Sending notification...';

    // Check if we have notification permission first
    if (Notification.permission !== 'granted') {
        statusElement.textContent = 'Error: Notification permission not granted. Please enable notifications first.';
        return;
    }

    const target = document.getElementById('notification-target').value;
    const timestamp = new Date().toLocaleTimeString();

    fetch('/api/send-notification', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            title: 'Test Notification (' + timestamp + ')',
            body: 'This is a test notification from your application! Sent at ' + timestamp,
            target: target
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Notification sent:', data);
        statusElement.textContent = 'Success: ' + data.message;

        // Create a local notification as a fallback
        if (target === 'web' || target === 'all') {
            statusElement.textContent += ' If FCM notifications are working, you should see a notification shortly.';

            // Create a direct browser notification as a fallback
            setTimeout(() => {
                const localNotification = new Notification('Local Test Notification (' + timestamp + ')', {
                    body: 'This is a local browser notification (not via FCM). Sent at ' + timestamp,
                    icon: '/static/tropical-border.png'
                });

                localNotification.onclick = function() {
                    window.focus();
                    this.close();
                };
            }, 2000);
        }

        // Clear status after 10 seconds
        setTimeout(() => {
            if (statusElement && statusElement.textContent && statusElement.textContent.includes('Success:')) {
                statusElement.textContent = '';
            }
        }, 10000);
    })
    .catch(error => {
        console.error('Error sending notification:', error);
        if (statusElement) {
            statusElement.textContent = 'Error: ' + error.message;
        }
    });
};


            // For menu expansion
            if (profileDropdown) {
                // Calculate dynamic height based on current dropdown height
                const originalHeight = profileDropdown.scrollHeight;
                if (!isExpanded) {
                    profileDropdown.style.height = (originalHeight * 1.25) + 'px';
                } else {
                    profileDropdown.style.height = '';
                }
            }
        });
    }

    function updateHelpTimer() {
        if (helpTimeRemaining <= 0) {
            // Timer reached zero
            clearInterval(helpTimerInterval);
            helpTimer.textContent = '00:00:00';

            // Show the help section if it's not already shown
            if (!helpSection.classList.contains('expanded')) {
                helpSection.style.display = 'none';
            }

            // Show phone icon in green when timer is done
            if (phoneIcon) {
                phoneIcon.style.display = 'inline';
                phoneIcon.style.color = '#4CAF50'; // Green color
            }

            // Update indicators to show online status
            document.querySelectorAll('.online-indicator').forEach(indicator => {
                indicator.style.animation = 'pulse 1s ease-in-out infinite';
                indicator.style.opacity = '1';
            });

            return;
        }

        // Decrement the remaining time
        helpTimeRemaining--;

        // Convert to hours, minutes, seconds
        const hours = Math.floor(helpTimeRemaining / 3600);
        const minutes = Math.floor((helpTimeRemaining % 3600) / 60);
        const seconds = helpTimeRemaining % 60;

        // Format time as HH:MM:SS
        const formattedTime = 
            (hours < 10 ? '0' : '') + hours + ':' +
            (minutes < 10 ? '0' : '') + minutes + ':' +
            (seconds < 10 ? '0' : '') + seconds;

        helpTimer.textContent = formattedTime;
    }

    window.hideProfileDropdown = function(event) {
        if (event) {
            event.preventDefault();
            const profileDropdown = document.querySelector('.profile-dropdown');
            if (profileDropdown) {
                profileDropdown.style.display = 'none';
                const link = event.target.closest('a');
                if (link) {
                    setTimeout(() => {
                        window.location.href = link.getAttribute('href');
                    }, 300);
                }
            }
        }
    };
}

function initializeMenu() {
    const menuIcon = document.querySelector('.menu-icon');
    const menuDropdown = document.querySelector('.menu-dropdown');

    menuIcon.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        menuDropdown.classList.toggle('visible');
        menuDropdown.style.display = menuDropdown.classList.contains('visible') ? 'block' : 'none';
        if (menuDropdown.classList.contains('visible')) {
            highlightCurrentPage();
        }
    });

    document.addEventListener('click', function(e) {
        if (!menuDropdown.contains(e.target) && !menuIcon.contains(e.target)) {
            menuDropdown.classList.remove('visible');
            menuDropdown.style.display = 'none';
        }
    });

    menuDropdown.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const href = this.getAttribute('href');
            menuDropdown.classList.remove('visible');
            menuDropdown.style.display = 'none';

            if (href && href !== window.location.pathname) {
                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });

    function highlightCurrentPage() {
        const currentPath = window.location.pathname;
        menuDropdown.querySelectorAll('a').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    const menuLinks = menuDropdown.querySelectorAll('a');
    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            menuLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            menuDropdown.classList.remove('visible');
            menuDropdown.style.display = 'none';

            const href = link.getAttribute('href');
            if (href && href !== window.location.pathname) {
                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });

    // Handle profile section click
    const profileSection = document.querySelector('.profile-section');
    const profileDropdown = document.querySelector('.profile-dropdown');

    if (profileSection && profileDropdown) {
        profileSection.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            profileDropdown.style.display = profileDropdown.style.display === 'block' ? 'none' : 'block';
        });

        // Handle profile dropdown links
        const profileLinks = document.querySelectorAll('.profile-dropdown a');
        profileLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                const id = link.getAttribute('id');
                if (href && href !== '#' && id !== 'settingsToggle') {
                    e.preventDefault();
                    profileDropdown.style.display = 'none';
                    // Ensure profile page navigation works correctly
                    window.location.href = href;
                }
            });
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileSection.contains(e.target)) {
                profileDropdown.style.display = 'none';
            }
        });
    }

    // Initial highlight
    highlightCurrentPage();
}

window.editAddress = function(icon) {
    const addressDiv = icon.closest('.address-card').querySelector('div > div');
    const addressLines = Array.from(addressDiv.querySelectorAll('p')).map(p => p.textContent);

    const form = document.createElement('form');
    form.className = 'edit-address-form';

    addressLines.forEach((line, index) => {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control mb-2';
        input.value = line;
        form.appendChild(input);
    });

    const saveBtn = document.createElement('button');
    saveBtn.type = 'button';
    saveBtn.className = 'btn btn-primary btn-sm me-2';
    saveBtn.textContent = 'Save';
    saveBtn.onclick = () => {
        const newLines = Array.from(form.querySelectorAll('input')).map(input => input.value);
        addressDiv.innerHTML = '';
        newLines.forEach(line => {
            const p = document.createElement('p');
            p.className = 'mb-1';
            p.textContent = line;
            addressDiv.appendChild(p);
        });

        // Restore the edit icon
        const parentCard = addressDiv.closest('.address-card');
        const editDiv = parentCard.querySelector('.d-flex');
        const editIcon = document.createElement('i');
        editIcon.className = 'fas fa-edit edit-icon';
        editIcon.style.cssText = 'cursor: pointer; color: #666; padding: 8px;';
        editIcon.onclick = function() { editAddress(this); };
        editDiv.appendChild(editIcon);
    };

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'btn btn-secondary btn-sm';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = () => {
        addressDiv.innerHTML = addressLines.map(line => `<p class="mb-1">${line}</p>`).join('');
    };

    const btnGroup = document.createElement('div');
    btnGroup.className = 'mt-2';
    btnGroup.appendChild(saveBtn);
    btnGroup.appendChild(cancelBtn);
    form.appendChild(btnGroup);

    addressDiv.innerHTML = '';
    addressDiv.appendChild(form);
};

function initializeDarkMode() {
    const settingsToggle = document.getElementById('settingsToggle');
    const settingsSubmenu = document.querySelector('.settings-submenu');
    const darkModeToggle = document.getElementById('darkModeToggle');
    const logoutBtn = document.getElementById('logoutBtn');
    const profileLink = document.querySelector('.profile-dropdown a[href="/profile"]');
    const helpToggle = document.getElementById('helpToggle');
    const helpSection = document.querySelector('.help-section');
    const body = document.body;
    const isDarkMode = localStorage.getItem('darkMode') === 'true';

    // Initialize settings toggle
    if (settingsToggle) {
        settingsToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            settingsSubmenu.style.display = settingsSubmenu.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Initialize profile link
    if (profileLink) {
        profileLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/profile';
        });
    }

    // Initialize logout button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/';
        });
    }

    // Initialize help toggle
    if (helpToggle && helpSection) {
        helpToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            helpSection.style.display = helpSection.style.display === 'none' ? 'block' : 'none';

            // Toggle help timer display
            const helpTimer = document.getElementById('helpTimer');
            const helpPhoneIcon = document.getElementById('helpPhoneIcon');

            if (helpTimer && helpPhoneIcon) {
                if (helpSection.style.display === 'block') {
                    helpTimer.style.display = 'inline';
                    helpPhoneIcon.style.display = 'inline';

                    // Start a countdown timer (just for demonstration)
                    let minutes = 4;
                    let seconds = 20;
                    const timerInterval = setInterval(() => {
                        seconds--;
                        if (seconds < 0) {
                            minutes--;
                            seconds = 59;
                        }
                        if (minutes < 0) {
                            clearInterval(timerInterval);
                            helpTimer.textContent = "Available";
                        } else {
                            helpTimer.textContent = `00:0${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                        }
                    }, 1000);
                } else {
                    helpTimer.style.display = 'none';
                    helpPhoneIcon.style.display = 'none';
                }
            }
        });
    }

    // Apply dark mode if needed
    if (isDarkMode) {
        body.classList.add('dark-mode');
        if (darkModeToggle) {
            const moonIcon = darkModeToggle.querySelector('i');
            const modeText = darkModeToggle.querySelector('span');
            if (moonIcon) moonIcon.classList.replace('fa-moon', 'fa-sun');
            if (modeText) modeText.textContent = 'Light Mode';
        }
    }

    darkModeToggle.addEventListener('click', (e) => {
        e.preventDefault();
        body.classList.toggle('dark-mode');
        const icon = darkModeToggle.querySelector('i');
        const textSpan = darkModeToggle.querySelector('span');
        const isDark = body.classList.contains('dark-mode');

        icon.classList.replace(isDark ? 'fa-moon' : 'fa-sun', 
                             isDark ? 'fa-sun' : 'fa-moon');
        textSpan.textContent = isDark ? 'Light Mode' : 'Dark Mode';
        localStorage.setItem('darkMode', isDark);
    });
}

function initializeButtons() {
    document.querySelectorAll('.btn-primary').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (btn.textContent.trim() === 'Buy') {
                addGlobalData();
            }
        });
    });
}

function initializeAddUser() {
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
            const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
            const usage = Math.floor(Math.random() * 100);
            const screentime = (Math.random() * 12).toFixed(1); // Random hours up to 12
            const dollars = (Math.random() * 50).toFixed(2); // Random amount up to $50
            const timestamp = new Date().toLocaleString();
            const userType = userTypes[Math.floor(Math.random() * userTypes.length)];

            createNewUserCard(firstName, lastName, usage, screentime, dollars, timestamp, userType);
            return false;
        });
    }
}

function createNewUserCard(firstName, lastName, usage, screentime, dollars, timestamp, userType) {
    const newCard = document.createElement('div');
    newCard.className = 'dashboard-content slide-in user-card';
    newCard.innerHTML = `
        <div class="user-info">
            <div class="email-container">
                <div class="user-info-header">
                    <div class="name-with-esim">
                        <span class="user-name">${firstName} ${lastName}</span>
                        <span class="user-type user-type-${userType.toLowerCase()}">${userType}</span>
                        <i class="fas fa-sim-card esim-icon" onclick="showEsimInfo(this, event)"></i>
                        <div class="esim-info">
                            <div class="imei">IMEI: ${generateIMEI()}</div>
                            <div class="sim">SIM #: ${generateSIMNumber()}</div>
                            <div class="device">${generateDevice()}</div>
                        </div>
                    </div>
                    <span class="user-email">${firstName.toLowerCase()}@example.com</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="card-actions">
                    <i class="fas fa-pause pause-play-icon" onclick="togglePausePlay(this)"></i>
                    ${firstName !== 'John' ? '<i class="fas fa-times remove-icon"></i>' : ''}
                </div>
            </div>
            <div class="data-usage">
                <div class="usage-metrics">
                    <div class="metric percentage">
                        <div class="usage-label">Data</div>
                        <div class="usage-amount">${usage}%</div>
                    </div>
                    <div class="metric screentime">
                        <div class="usage-label">Time</div>
                        <div class="usage-amount">${screentime}h</div>
                    </div>
                    <div class="metric dollars">
                        <div class="usage-label">Cost</div>
                        <div class="usage-amount">$${dollars}</div>
                    </div>
                </div>
            </div>
            <div class="manage-section">
                <span class="settings-text">Manage ${userType.toLowerCase()} settings</span>
                <button class="cog-button" title="Manage user">
                    <i class="fas fa-cog"></i>
                </button>
            </div>
            <div class="policy-pills">
                ${getPolicies(userType).map(policy => `<span class="policy-pill">${policy}</span>`).join('')}
            </div>
        </div>
    `;

    const container = document.querySelector('.container');
    const addUserContainer = document.querySelector('.add-user-container');

    if (container && addUserContainer) {
        container.insertBefore(newCard, addUserContainer);

        if (firstName !== 'John') {
            const removeIcon = newCard.querySelector('.remove-icon');
            if (removeIcon) {
                removeIcon.addEventListener('click', () => removeUserCard(newCard));
            }
        }

        setTimeout(() => {
            newCard.classList.add('visible');
            updateUserCount(1);
            updateSortControlsVisibility();
        }, 50);
    }
}

function initializeSortControls() {
    const sortIcons = document.querySelectorAll('.sort-icon');
    const sortSelect = document.querySelector('.sort-select');

    // Set newest as default active
    document.querySelector('[data-sort="newest"]').classList.add('active');

    sortIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            sortIcons.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            updateMetricHighlight(sortSelect.value);
            sortUsers(this.dataset.sort);
        });
    });

    sortSelect.addEventListener('change', function() {
        updateMetricHighlight(this.value);
        const activeSort = document.querySelector('.sort-icon.active');
        if (activeSort) {
            sortUsers(activeSort.dataset.sort);
        }
    });

    // Initial highlight
    updateMetricHighlight(sortSelect.value);
}

function updateMetricHighlight(selectedMetric) {
    document.querySelectorAll('.metric').forEach(metric => {
        metric.classList.remove('highlighted');
    });

    document.querySelectorAll('.user-card').forEach(card => {
        const metrics = card.querySelectorAll('.metric');
        metrics.forEach(metric => {
            if (metric.classList.contains(selectedMetric)) {
                metric.classList.add('highlighted');
            }
        });
    });
}

// Utility functions
function generateIMEI() {
    return Array.from({length: 20}, () => Math.floor(Math.random() * 10)).join('');
}

function generateSIMNumber() {
    return Array.from({length: 20}, () => Math.floor(Math.random() * 10)).join('');
}

function generateDevice() {
    const makes = ['Apple', 'Samsung', 'Google', 'OnePlus'];
    const models = ['iPhone 14', 'Galaxy S23', 'Pixel 7', 'OnePlus 11'];
    return `${makes[Math.floor(Math.random() * makes.length)]} ${models[Math.floor(Math.random() * models.length)]}`;
}

function getPolicies(type) {
    const policies = {
        'Admin': ['Unlimited Data', 'Full Control', 'Priority Network'],
        'Parent': ['10GB Data', 'Content Filter Off', 'Usage Reports'],
        'Child': ['5GB Data', 'Content Filter On', 'Time Limits'],
        'Family': ['8GB Data', 'Shared Pool', 'Family Sync'],
        'Friend': ['3GB Data', 'Time Limited', 'Guest Access'],
        'Device': ['2GB Data', 'IoT Priority', 'Auto Connect'],
        'Car': ['4GB Data', 'Navigation Only', 'Emergency Data'],
        'Pet': ['1GB Data', 'Location Track', 'Health Monitor']
    };
    return policies[type] || [];
}

function updateUserCount(change = 0) {
    const countElement = document.querySelector('.user-count');
    if (countElement) {
        const currentCount = parseInt(countElement.textContent) || 0;
        countElement.textContent = currentCount + change;
    }
}

function updateSortControlsVisibility() {
    const userCards = Array.from(document.getElementsByClassName('user-card'));
    const sortControls = document.querySelector('.sort-controls');
    if (sortControls) {
        sortControls.style.display = userCards.length > 1 ? 'flex' : 'none';
    }
}

function removeUserCard(card) {
    if (confirm('Remove this user from data share?')) {
        card.classList.remove('visible');
        setTimeout(() => {
            card.remove();
            updateUserCount(-1);
            updateSortControlsVisibility();
        }, 300);
    }
}

function sortUsers(sortType) {
    const container = document.querySelector('.container');
    const cards = Array.from(document.getElementsByClassName('user-card'));
    const addUserContainer = document.querySelector('.add-user-container');

    cards.sort((a, b) => {
        const getMetricValue = (card) => {
            const selectedMetric = document.querySelector('.sort-select').value;
            switch(selectedMetric) {
                case 'percentage':
                    return parseInt(card.querySelector('.metric.percentage .usage-amount').textContent);
                case 'screentime':
                    return parseFloat(card.querySelector('.metric.screentime .usage-amount').textContent);
                case 'dollars':
                    return parseFloat(card.querySelector('.metric.dollars .usage-amount').textContent.substring(1));
                default:
                    return 0;
            }
        };

        if (sortType === 'asc' || sortType === 'desc') {
            return sortType === 'asc' 
                ? getMetricValue(a) - getMetricValue(b)
                : getMetricValue(b) - getMetricValue(a);
        }

        if (sortType === 'newest' || sortType === 'oldest') {
            const timeA = a.querySelector('.timestamp').textContent;
            const timeB = b.querySelector('.timestamp').textContent;
            const dateA = new Date(timeA.replace(/(\d{4}-\d{2}-\d{2}),\s*(\d{1,2}):(\d{2}):(\d{2})\s*(a\.m\.|p\.m\.)/, function(match, date, hour, min, sec, period) {
                hour = parseInt(hour);
                if (period === 'p.m.' && hour !== 12) hour += 12;
                if (period === 'a.m.' && hour === 12) hour = 0;
                return `${date} ${hour}:${min}:${sec}`;
            }));
            const dateB = new Date(timeB.replace(/(\d{4}-\d{2}-\d{2}),\s*(\d{1,2}):(\d{2}):(\d{2})\s*(a\.m\.|p\.m\.)/, function(match, date, hour, min, sec, period) {
                hour = parseInt(hour);
                if (period === 'p.m.' && hour !== 12) hour += 12;
                if (period === 'a.m.' && hour === 12) hour = 0;
                return `${date} ${hour}:${min}:${sec}`;
            }));
            return sortType === 'newest' ? dateB - dateA : dateA - dateB;
        } else {
            const usageA = parseInt(a.querySelector('.usage-amount').textContent);
            const usageB = parseInt(b.querySelector('.usage-amount').textContent);
            return sortType === 'asc' ? usageA - usageB : usageB - usageA;
        }
    });

    // Get original positions
    const originalPositions = cards.map(card => {
        const rect = card.getBoundingClientRect();
        return { card, top: rect.top };
    });

    // Remove and reinsert cards
    // Store current positions
    const currentPositions = cards.map(card => ({
        card,
        rect: card.getBoundingClientRect()
    }));

    // Remove all cards
    cards.forEach(card => card.remove());

    // Reinsert cards in new order
    cards.forEach((card, index) => {
        container.insertBefore(card, addUserContainer);
        const oldPos = currentPositions.find(pos => pos.card === card);
        const newPos = card.getBoundingClientRect();
        const isMovingDown = oldPos.rect.top < newPos.top;

        // Set initial position
        card.style.transform = `translateY(${oldPos.rect.top - newPos.top}px)`;
        card.style.transition = 'none';

        // Force reflow
        card.offsetHeight;

        // Apply animation class and reset transform
        card.classList.add(isMovingDown ? 'sorting-down' : 'sorting-up');
        card.style.transition = '';
        card.style.transform = '';
    });

    // Reset classes after animation
    setTimeout(() => {
        cards.forEach(card => {
            card.classList.remove('sorting-up', 'sorting-down');
        });
    }, 2000);
}

function initializeBackToTop() {
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({top: 0, behavior: 'smooth'});
        });
    }
}

// Global functions needed for HTML onclick attributes
window.showEsimInfo = function(icon, event) {
    event.preventDefault();
    event.stopPropagation();
    const infoElement = icon.nextElementSibling;
    if (infoElement) {
        const allInfoElements = document.querySelectorAll('.esim-info');
        allInfoElements.forEach(el => {
            if (el !== infoElement) el.style.display = 'none';
        });
        infoElement.style.display = infoElement.style.display === 'block' ? 'none' : 'block';
    }
};

window.togglePausePlay = function(icon) {
    const card = icon.closest('.dashboard-content');
    if (icon.classList.contains('fa-pause')) {
        icon.classList.remove('fa-pause');
        icon.classList.add('fa-play');
        card.classList.add('paused');

        const pauseTime = new Date();
        const durationSpan = document.createElement('span');
        durationSpan.className = 'pause-duration';
        durationSpan.textContent = 'Paused just now';
        icon.parentElement.appendChild(durationSpan);

        setInterval(() => {
            durationSpan.textContent = 'Paused ' + formatTimeDifference(pauseTime);
        }, 60000);
    } else {
        icon.classList.remove('fa-play');
        icon.classList.add('fa-pause');
        card.classList.remove('paused');
        const durationSpan = icon.parentElement.querySelector('.pause-duration');
        if (durationSpan) durationSpan.remove();
    }
};

function formatTimeDifference(timestamp) {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
}

function showConfirmationDrawer(dataAmount, price, productId) {
    const drawer = document.getElementById('confirmationDrawer');
    const dataAmountElement = document.getElementById('confirmDataAmount');
    const priceElement = document.getElementById('confirmPrice');

    if (drawer && dataAmountElement && priceElement) {
        dataAmountElement.textContent = `${dataAmount}GB`;
        priceElement.textContent = `$${price}`;
        drawer.classList.add('show');
        drawer.setAttribute('data-product-id', productId);
    } else {
        console.error('Confirmation drawer elements not found');
        // Fall back to direct purchase if drawer elements aren't available
        confirmPurchase(productId);
    }
}

function confirmPurchase(productId) {
    // If called from drawer, get product ID from there
    if (!productId) {
        const drawer = document.getElementById('confirmationDrawer');
        if (drawer) {
            productId = drawer.getAttribute('data-product-id');
            hideConfirmationDrawer();
        }
    }

    if (productId === 'global_data_10gb') {
        addGlobalData();
    }
}

window.addGlobalData = function() {
    showConfirmationDrawer(10, 10, 'global_data_10gb');
};

window.showConfirmationDrawer = function(dataAmount, price, productId) {
    const drawer = document.getElementById('confirmationDrawer');
    const dataAmountElement = document.getElementById('confirmDataAmount');
    const priceElement = document.getElementById('confirmPrice');

    if (drawer && dataAmountElement && priceElement) {
        dataAmountElement.textContent = `${dataAmount}GB`;
        priceElement.textContent = `$${price}`;
        drawer.setAttribute('data-product-id', productId);
        drawer.style.display = 'block';
        drawer.classList.add('show');
        drawer.style.bottom = '0';
    } else {
        console.error('Confirmation drawer elements not found');
        // Fall back to direct purchase if drawer elements aren't available
        confirmPurchase(productId);
    }
};

window.hideConfirmationDrawer = function() {
    const drawer = document.getElementById('confirmationDrawer');
    if (drawer) {
        drawer.classList.remove('show');
        drawer.style.bottom = '-100%';
        setTimeout(() => {
            drawer.style.display = 'none';
        }, 300);
    }
};

window.confirmPurchase = function(productId) {
    // If called from drawer, get product ID from there
    if (!productId) {
        const drawer = document.getElementById('confirmationDrawer');
        if (drawer) {
            productId = drawer.getAttribute('data-product-id');
            hideConfirmationDrawer();
        }
    }

    // Send API request to record purchase
    fetch('/api/record-global-purchase', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ productId: productId || 'global_data_10gb' })
    })
    .then(response => {
        if (!response.ok && response.status >= 500) {
            // Handle server errors more gracefully - still process the UI updates
            console.warn('Server error when recording purchase, proceeding with UI update anyway');
            return { 
                status: 'success', 
                purchaseId: 'local_' + Date.now(),
                simulated: true
            };
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Show purchase in history
            addPurchaseToHistory(productId, data.purchaseId);
            // Show data added
            showDataAdded(productId);

            if (data.simulated) {
                console.info('Note: Using simulated purchase ID due to database issue');
            }

            // Check if this was a membership purchase and update offers
            if (productId === 'basic_membership' || productId === 'full_membership') {
                updateOffersCarousel(productId);
            }
        } else {
            console.error('Purchase failed:', data.message);
            // Show a user-friendly error message
            alert('Purchase could not be completed. Please try again later.');
        }
    })
    .catch(error => {
        console.error('Error recording purchase:', error);
        // Still show the purchase in the UI to improve user experience
        addPurchaseToHistory(productId, 'local_' + Date.now());
        showDataAdded(productId);
    });
};

function addPurchaseToHistory(productId, purchaseId) {
    const purchaseList = document.getElementById('purchaseList');
    if (!purchaseList) return;

    // Remove empty state if present
    const emptyState = purchaseList.querySelector('.purchase-empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    const now = new Date();
    const formattedDate = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
    const productName = getProductName(productId);
    const amount = getProductPrice(productId);

    const purchaseItem = document.createElement('div');
    purchaseItem.className = 'purchase-item';
    purchaseItem.innerHTML = `
        <div>
            <div>${productName}</div>
            <div class="purchase-date">${formattedDate}</div>
        </div>
        <div class="purchase-amount">$${amount}</div>
    `;

    purchaseList.prepend(purchaseItem);
}

function getProductName(productId) {
    const products = {
        'global_data_10gb': '10GB Global Data',
        'basic_membership': 'Basic Membership',
        'full_membership': 'Full Membership'
    };
    return products[productId] || 'Unknown Product';
}

function getProductPrice(productId) {
    const prices = {
        'global_data_10gb': '10.00',
        'basic_membership': '24.00',
        'full_membership': '66.00'
    };
    return prices[productId] || '0.00';
}

function showDataAdded(productId) {
    // Show data has been added to the account
    const dataDisplay = document.getElementById('dataDisplay');
    const globalStatus = document.getElementById('globalStatus');
    const dotIndicator = document.querySelector('.dot-indicator');

    if (dataDisplay && globalStatus) {
        // Get current data amount from localStorage
        let currentAmount = parseFloat(localStorage.getItem('walletBalance') || '0.0');

        // Add new data to current amount
        let addedAmount = 0;
        if (productId === 'global_data_10gb') {
            addedAmount = 10.0;
        } else {
            addedAmount = 1.0;
        }

        // Calculate new total and update display
        const newTotal = currentAmount + addedAmount;

        // Save to localStorage
        localStorage.setItem('walletBalance', newTotal.toString());

        // Update the display
        dataDisplay.innerHTML = `${newTotal.toFixed(1)}<span>GB</span>`;
        dataDisplay.style.display = 'block';
        globalStatus.style.display = 'block';

        // Add animation to both data display and dot
        dataDisplay.classList.add('pulse');
        if (dotIndicator) {
            dotIndicator.classList.add('pulse');
        }

        // Create sparkle effect
        createSparkle(dataDisplay);

        setTimeout(() => {
            dataDisplay.classList.remove('pulse');
            if (dotIndicator) {
                dotIndicator.classList.remove('pulse');
            }
        }, 1000);
    }
}

function checkPurchasedMemberships() {
    // Check local storage first for quick response
    if (localStorage.getItem('has_membership') === 'true') {
        updateOffersCarousel();
        return;
    }

    // Make an API call to check if user has a membership
    fetch('/api/check-memberships')
        .then(response => response.json())
        .then(data => {
            if (data.has_membership) {
                localStorage.setItem('has_membership', 'true');
                updateOffersCarousel(data.membership_type);
            }
        })
        .catch(error => {
            console.error('Error checking memberships:', error);
        });
}

function updateOffersCarousel(membershipType = null) {
    const carousel = document.getElementById('promotionsCarousel');
    if (!carousel) return;

    // If a membership was just purchased, update localStorage
    if (membershipType && (membershipType === 'basic_membership' || membershipType === 'full_membership')) {
        localStorage.setItem('has_membership', 'true');
    }

    // Only proceed with removing offers if user has a membership
    const hasMembership = localStorage.getItem('has_membership') === 'true' || membershipType;
    if (!hasMembership) return;

    // Remove membership offers from carousel
    const items = carousel.querySelectorAll('.carousel-item');
    const controls = document.querySelectorAll('.carousel-controls button');
    let removedCount = 0;

    items.forEach((item, index) => {
        const offerContent = item.querySelector('.offer-content h3');
        if (offerContent && (offerContent.textContent.includes('Basic Membership') || 
                             offerContent.textContent.includes('Full Membership'))) {
            item.remove();
            if (controls && controls[index]) {
                controls[index].remove();
            }
            removedCount++;
        }
    });

    // If we removed items, make sure the first remaining item is active
    if (removedCount > 0) {
        const remainingItems = carousel.querySelectorAll('.carousel-item');
        if (remainingItems.length > 0) {
            remainingItems.forEach(item => item.classList.remove('active'));
            remainingItems[0].classList.add('active');

            // Update the controls
            const remainingControls = document.querySelectorAll('.carousel-controls button');
            if (remainingControls.length > 0) {
                remainingControls.forEach(btn => btn.classList.remove('active'));
                remainingControls[0].classList.add('active');
            }
        } else {
            // No offers remain, hide the carousel
            const carouselContainer = carousel.closest('.carousel');
            if (carouselContainer) {
                carouselContainer.style.display = 'none';
            }
        }
    }

    // Check if only one offer remains and hide controls if needed
    updateCarouselControlsVisibility();
}

function updateCarouselControlsVisibility() {
    const carousel = document.getElementById('promotionsCarousel');
    if (!carousel) return;

    const items = carousel.querySelectorAll('.carousel-item');
    const controlsContainer = document.querySelector('.carousel-controls');

    if (controlsContainer && items.length <= 1) {
        controlsContainer.style.display = 'none';
    } else if (controlsContainer) {
        controlsContainer.style.display = 'flex';
    }
}

function initializeChart(canvas) {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Data Usage (GB)',
                data: [12, 19, 15, 25, 22, 30, 45],
                borderColor: '#FFC40C',
                backgroundColor: 'rgba(255, 196, 12, 0.2)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 750
            },
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                        drawTicks: false
                    },
                    backgroundColor: 'transparent',
                    border: {
                        display: false
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawTicks: false
                    },
                    backgroundColor: 'transparent',
                    border: {
                        display: false
                    }
                }
            },
            backgroundColor: 'transparent',
            elements: {
                point: {
                    radius: 4,
                    backgroundColor: '#FFC40C'
                }
            }
        }
    });
}

window.toggleChart = function(element) {
    const card = element.closest('.insights-card');
    const chartDiv = card.querySelector('.usage-chart');
    const canvas = chartDiv.querySelector('canvas');

    if (chartDiv.style.display === 'none') {
        chartDiv.style.display = 'block';
        element.textContent = 'Hide details';

        if (!canvas.chart) {
            canvas.chart = initializeChart(canvas);
        }
    } else {
        if (canvas.chart) {
            canvas.chart.destroy();
            canvas.chart = null;
        }
        chartDiv.style.display = 'none';
        element.textContent = 'See details';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.insight-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            toggleChart(this);
        });
    });
});

// Your JavaScript code here

// Function to send a test notification
function sendTestNotification() {
  fetch('/api/send-notification', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: 'Test Notification',
      body: 'This is a test notification from your application!',
      target: document.getElementById('notification-target').value
    }),
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById('notification-status').textContent = 'Notification sent: ' + data.message;
    setTimeout(() => {
      document.getElementById('notification-status').textContent = '';
    }, 5000);
  })
  .catch(error => {
    console.error('Error sending notification:', error);
    document.getElementById('notification-status').textContent = 'Error: ' + error.message;
  });
}

// Add notification testing UI when document is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Check if we're on the dashboard page
  if (window.location.pathname === '/dashboard') {
    const dashboardContainer = document.querySelector('.container');
    if (dashboardContainer) {
      const notificationTester = document.createElement('div');
      notificationTester.className = 'notification-tester';

      // Check if Notification API is supported
      const notificationSupported = typeof Notification !== 'undefined';
      const permissionStatus = notificationSupported ? Notification.permission : 'not-supported';

      notificationTester.innerHTML = `
        <h3>Test Push Notifications</h3>
        <p>Send a test notification to verify your FCM setup:</p>
        <div class="notification-permission-status">
          <strong>Current Permission Status:</strong> 
          <span id="permission-status">${permissionStatus}</span>
          ${notificationSupported && Notification.permission !== 'granted' ? 
            '<button id="request-permission-btn">Request Permission</button>' : 
            (notificationSupported ? '<span class="permission-granted">✓ Notifications enabled</span>' : 
            '<span class="permission-not-supported">Notifications not supported in this browser</span>')}
        </div>
        <div class="notification-troubleshooting" ${Notification.permission !== 'denied' ? 'style="display:none"' : ''}>
          <p><strong>Troubleshooting:</strong> If notifications are blocked, please:</p>
          <ol>
            <li>Click the lock/info icon in your browser's address bar</li>
            <li>Find "Notifications" and change the setting to "Allow"</li>
            <li>Reload this page</li>
          </ol>
        </div>
        <div class="notification-controls" ${Notification.permission !== 'granted' ? 'style="display:none"' : ''}>
          <select id="notification-target">
            <option value="all">All Devices (Web & App)</option>
            <option value="web">Web Only</option>
            <option value="app">App Only</option>
          </select>
          <button onclick="sendTestNotification()">Send Test Notification</button>
        </div>
        <p id="notification-status"></p>
      `;

      // Add some basic styling
      const style = document.createElement('style');
      style.textContent = `
        .notification-tester {
          margin-top: 20px;
          padding: 15px;
          background-color: #f0f8ff;
          border-radius: 8px;
          border: 1px solid #ccc;
        }
        .notification-tester button {
          margin-top: 10px;
          padding: 5px 10px;
          background-color: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        .notification-tester select {
          padding: 5px;
          margin-right: 10px;
        }
        #notification-status {
          margin-top: 10px;
          font-weight: bold;
        }
        .notification-permission-status {
          margin: 10px 0;
          padding: 8px;
          background-color: #f8f8f8;
          border-radius: 4px;
        }
        .permission-granted {
          color: #4CAF50;
          font-weight: bold;
        }
        .notification-troubleshooting {
          margin: 10px 0;
          padding: 10px;
          background-color: #fff3cd;
          border: 1px solid #ffeeba;
          border-radius: 4px;
        }
        .notification-controls {
          margin-top: 15px;
        }
        #request-permission-btn {
          margin-left: 10px;
          background-color: #007bff;
        }
      `;
      document.head.appendChild(style);

      // Add the notification tester to the dashboard
      dashboardContainer.appendChild(notificationTester);

      // Add event listener for permission request button
      const permissionBtn = document.getElementById('request-permission-btn');
      if (permissionBtn) {
        permissionBtn.addEventListener('click', function() {
          Notification.requestPermission().then(function(permission) {
            document.getElementById('permission-status').textContent = permission;
            if (permission === 'granted') {
              document.querySelector('.notification-controls').style.display = 'block';
              document.querySelector('.notification-troubleshooting').style.display = 'none';
              permissionBtn.parentElement.removeChild(permissionBtn);
              const permissionGranted = document.createElement('span');
              permissionGranted.className = 'permission-granted';
              permissionGranted.textContent = '✓ Notifications enabled';
              document.getElementById('permission-status').parentElement.appendChild(permissionGranted);
              // Reload the page to initialize Firebase with the new permission
              window.location.reload();
            } else if (permission === 'denied') {
              document.querySelector('.notification-troubleshooting').style.display = 'block';
            }
          });
        });
      }
    }
  }
});