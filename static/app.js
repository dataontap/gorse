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
});

function initializeProfileDropdown() {
    const profileDropdown = document.querySelector('.profile-dropdown');
    
    window.hideProfileDropdown = (event) => {
        event.preventDefault();
        profileDropdown.style.display = 'none';
        setTimeout(() => {
            window.location.href = event.target.closest('a').getAttribute('href');
        }, 300);
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

            if (window.location.pathname !== '/dashboard') {
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 300);
            }
        });
    });

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
    const body = document.body;
    const isDarkMode = localStorage.getItem('darkMode') === 'true';

    settingsToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        settingsSubmenu.style.display = settingsSubmenu.style.display === 'none' ? 'block' : 'none';
    });

    if (profileLink) {
        profileLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/profile';
        });
    }

    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.location.href = '/';
    });

    if (isDarkMode) {
        body.classList.add('dark-mode');
        darkModeToggle.querySelector('i').classList.replace('fa-moon', 'fa-sun');
        darkModeToggle.querySelector('span').textContent = 'Light Mode';
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
                        <div class="usage-label">Data Usage</div>
                        <div class="usage-amount">${usage}%</div>
                    </div>
                    <div class="metric screentime">
                        <div class="usage-label">Screentime</div>
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

window.showConfirmationDrawer = function(dataAmount, price) {
    document.getElementById('confirmDataAmount').textContent = `${dataAmount}GB`;
    document.getElementById('confirmPrice').textContent = `$${price}`;
    document.getElementById('confirmationDrawer').classList.add('show');
};

window.hideConfirmationDrawer = function() {
    document.getElementById('confirmationDrawer').classList.remove('show');
};

window.confirmPurchase = function() {
    hideConfirmationDrawer();
    const dataAmountElement = document.querySelector('.data-amount');
    const globalStatus = document.getElementById('globalStatus');
    
    if (dataAmountElement) {
        dataAmountElement.style.display = 'flex';
        globalStatus.style.display = 'block';
        
        let currentText = dataAmountElement.textContent || "0";
        let currentData = parseFloat(currentText.replace('GB', '') || "0");
        currentData += 10;
        dataAmountElement.innerHTML = `${currentData.toFixed(1)}<span>GB</span>`;

        const dotIndicator = document.querySelector('.dot-indicator');
        if (dotIndicator) {
            dotIndicator.classList.add('pulse');
            setTimeout(() => {
                dotIndicator.classList.remove('pulse');
            }, 1000);
        }
    }
};

window.addGlobalData = function() {
    showConfirmationDrawer(10, 20);
};

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