
// Initialize arrays at the top level
const firstNames = ['Jenny', 'Mike', 'Sarah', 'Alex', 'Emma', 'James', 'Lisa', 'David'];
const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'];
const userTypes = ['Admin', 'Parent', 'Child', 'Family', 'Friend', 'Device', 'Car', 'Pet'];

document.addEventListener('DOMContentLoaded', () => {
    initializeAddUser();
    initializeSortControls();
    initializeBackToTop();
    initializeButtons();
    updateSortControlsVisibility();
});

function initializeButtons() {
    document.querySelectorAll('.btn-primary').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (btn.textContent.trim() === 'Buy') {
                addGlobalData();
            }
        });
    });

    document.querySelectorAll('.insight-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            toggleChart(e);
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
            const timestamp = new Date().toLocaleString();
            const userType = userTypes[Math.floor(Math.random() * userTypes.length)];

            createNewUserCard(firstName, lastName, usage, timestamp, userType);
            return false;
        });
    }
}

function createNewUserCard(firstName, lastName, usage, timestamp, userType) {
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
                <div class="usage-label">Data Usage</div>
                <div class="usage-amount">${usage}%</div>
            </div>
            <div class="policy-pills">
                ${getPolicies(userType).map(policy => `<span class="policy-pill">${policy}</span>`).join('')}
            </div>
            <div class="manage-section">
                <a href="#" class="manage-link">Manage ${userType.toLowerCase()} settings</a>
                <i class="fas fa-cog"></i>
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
    // Set newest as default active
    document.querySelector('[data-sort="newest"]').classList.add('active');
    
    sortIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            sortIcons.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            sortUsers(this.dataset.sort);
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
        if (sortType === 'newest') {
            const timeA = new Date(a.querySelector('.timestamp').textContent);
            const timeB = new Date(b.querySelector('.timestamp').textContent);
            return timeB - timeA;
        } else {
            const usageA = parseInt(a.querySelector('.usage-amount').textContent);
            const usageB = parseInt(b.querySelector('.usage-amount').textContent);
            return sortType === 'asc' ? usageA - usageB : usageB - usageA;
        }
    });

    cards.forEach(card => card.remove());
    cards.forEach(card => container.insertBefore(card, addUserContainer));
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

window.addGlobalData = function() {
    const dataAmountElement = document.querySelector('.data-amount');
    if (dataAmountElement) {
        let currentData = parseFloat(dataAmountElement.textContent);
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

window.toggleChart = function(event) {
    event.preventDefault();
    const chartDiv = event.target.closest('.insights-card').querySelector('.usage-chart');
    const link = event.target;

    if (chartDiv.style.display === 'none') {
        chartDiv.style.display = 'block';
        link.textContent = 'Hide details';
        if (!chartDiv.hasAttribute('data-initialized')) {
            initializeChart(chartDiv.closest('.insights-card'));
            chartDiv.setAttribute('data-initialized', 'true');
        }
    } else {
        chartDiv.style.display = 'none';
        link.textContent = 'See details';
    }
};
