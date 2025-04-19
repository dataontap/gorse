
document.addEventListener('DOMContentLoaded', () => {
    // Define variables first
    const firstNames = ['Jenny', 'Mike', 'Sarah', 'Alex', 'Emma', 'James', 'Lisa', 'David'];
    const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'];
    const userTypes = ['Admin', 'Parent', 'Child', 'Family', 'Friend', 'Device', 'Car', 'Pet'];

    // Initialize sort controls
    const sortIcons = document.querySelectorAll('.sort-icon');
    if (sortIcons) {
        sortIcons.forEach(icon => {
            icon.addEventListener('click', function() {
                document.querySelectorAll('.sort-icon').forEach(i => i.classList.remove('active'));
                this.classList.add('active');

                const sortType = this.dataset.sort;
                const container = document.querySelector('.container');
                const cards = Array.from(document.getElementsByClassName('user-card'));

                cards.forEach(card => card.classList.add('sorting'));

                if (sortType === 'newest') {
                    cards.sort((a, b) => {
                        const timeA = new Date(a.querySelector('.timestamp').textContent);
                        const timeB = new Date(b.querySelector('.timestamp').textContent);
                        return timeB - timeA;
                    });
                } else {
                    cards.sort((a, b) => {
                        const usageA = parseInt(a.querySelector('.usage-amount')?.textContent || '0');
                        const usageB = parseInt(b.querySelector('.usage-amount')?.textContent || '0');
                        return sortType === 'asc' ? usageA - usageB : usageB - usageA;
                    });
                }

                setTimeout(() => {
                    cards.forEach(card => card.remove());
                    const addUserContainer = document.querySelector('.add-user-container');
                    cards.forEach((card, index) => {
                        setTimeout(() => {
                            container.insertBefore(card, addUserContainer);
                            setTimeout(() => card.classList.remove('sorting'), 600);
                        }, index * 100);
                    });
                }, 300);
            });
        });
    }

    function generateIMEI() {
        return Array.from({length: 20}, () => Math.floor(Math.random() * 10)).join('');
    }

    function generateSIMNumber() {
        return Array.from({length: 20}, () => Math.floor(Math.random() * 10)).join('');
    }

    function generateDevice() {
        const makes = ['Apple', 'Samsung', 'Google', 'OnePlus'];
        const models = ['iPhone 14', 'Galaxy S23', 'Pixel 7', 'OnePlus 11'];
        const make = makes[Math.floor(Math.random() * makes.length)];
        const model = models[Math.floor(Math.random() * models.length)];
        return `${make} ${model}`;
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

    // Add User functionality
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
        });
    }

    // Back to top functionality
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            window.scrollTo({top: 0, behavior: 'smooth'});
        });
    }
});
