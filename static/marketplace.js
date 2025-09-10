// Global menu toggle function (matches other pages)
function toggleMenu(menuIcon) {
    console.log('toggleMenu called with:', menuIcon);
    const menuDropdown = menuIcon.querySelector('.menu-dropdown');
    console.log('menuDropdown found:', menuDropdown);

    if (!menuDropdown) {
        console.error('Menu dropdown not found!');
        return;
    }

    if (menuDropdown.style.display === 'block') {
        menuDropdown.style.display = 'none';
        console.log('Menu closed');
    } else {
        menuDropdown.style.display = 'block';
        console.log('Menu opened');
    }

    console.log('Menu toggled:', menuDropdown.style.display);
}

// Close menu when clicking outside
document.addEventListener('click', function(e) {
    const menuDropdown = document.querySelector('.menu-dropdown');
    const menuIcon = document.querySelector('.menu-icon');

    if (menuDropdown && menuIcon && !menuIcon.contains(e.target)) {
        menuDropdown.style.display = 'none';
    }
});

// Notification tester functionality for marketplace
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

document.addEventListener('DOMContentLoaded', function() {
    initializeMarketplace();
    initializeServiceCarousel();
    initializeAuctionCountdown();
    initializeCartPreview();
    initializeBackToTop();
    
    // Initialize offers cards
    setTimeout(() => {
        populateOfferCards();
        setTimeout(() => {
            initializeCardStack();
        }, 200);
    }, 100);
});

function initializeMarketplace() {
    // Implement dark mode compatibility
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }

    // Initialize dark mode toggle functionality
    initializeDarkModeToggle();

    // Handle add to cart buttons
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productCard = this.closest('.product-card');
            const productName = productCard.querySelector('h3').textContent;
            const productPrice = productCard.querySelector('.current-price').textContent;

            // Animation for adding to cart
            button.textContent = 'Added ✓';
            button.disabled = true;

            // Show cart preview
            const cartPreview = document.querySelector('.cart-preview');
            if (cartPreview) {
                cartPreview.style.bottom = '0';

                // Hide after 3 seconds
                setTimeout(() => {
                    cartPreview.style.bottom = '-400px';
                    // Reset button
                    button.textContent = 'Add to Cart';
                    button.disabled = false;
                }, 3000);
            }

            // You would typically send this to a cart API
            console.log(`Added to cart: ${productName} - ${productPrice}`);
        });
    });

    // Add hover effect to service cards
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function initializeServiceCarousel() {
    // Allow horizontal scrolling with mouse drag
    const servicesCarousel = document.querySelector('.services-carousel');
    if (!servicesCarousel) return;

    let isDown = false;
    let startX;
    let scrollLeft;

    servicesCarousel.addEventListener('mousedown', (e) => {
        isDown = true;
        servicesCarousel.style.cursor = 'grabbing';
        startX = e.pageX - servicesCarousel.offsetLeft;
        scrollLeft = servicesCarousel.scrollLeft;
    });

    servicesCarousel.addEventListener('mouseleave', () => {
        isDown = false;
        servicesCarousel.style.cursor = 'grab';
    });

    servicesCarousel.addEventListener('mouseup', () => {
        isDown = false;
        servicesCarousel.style.cursor = 'grab';
    });

    servicesCarousel.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - servicesCarousel.offsetLeft;
        const walk = (x - startX) * 2; // Scroll speed
        servicesCarousel.scrollLeft = scrollLeft - walk;
    });

    // Same for auctions container
    const auctionsContainer = document.querySelector('.auctions-container');
    if (auctionsContainer) {
        let auctionIsDown = false;
        let auctionStartX;
        let auctionScrollLeft;

        auctionsContainer.addEventListener('mousedown', (e) => {
            auctionIsDown = true;
            auctionsContainer.style.cursor = 'grabbing';
            auctionStartX = e.pageX - auctionsContainer.offsetLeft;
            auctionScrollLeft = auctionsContainer.scrollLeft;
        });

        auctionsContainer.addEventListener('mouseleave', () => {
            auctionIsDown = false;
            auctionsContainer.style.cursor = 'grab';
        });

        auctionsContainer.addEventListener('mouseup', () => {
            auctionIsDown = false;
            auctionsContainer.style.cursor = 'grab';
        });

        auctionsContainer.addEventListener('mousemove', (e) => {
            if (!auctionIsDown) return;
            e.preventDefault();
            const x = e.pageX - auctionsContainer.offsetLeft;
            const walk = (x - auctionStartX) * 2;
            auctionsContainer.scrollLeft = auctionScrollLeft - walk;
        });
    }

    // And for recently viewed
    const recentlyViewedContainer = document.querySelector('.recently-viewed-container');
    if (recentlyViewedContainer) {
        let recentIsDown = false;
        let recentStartX;
        let recentScrollLeft;

        recentlyViewedContainer.addEventListener('mousedown', (e) => {
            recentIsDown = true;
            recentlyViewedContainer.style.cursor = 'grabbing';
            recentStartX = e.pageX - recentlyViewedContainer.offsetLeft;
            recentScrollLeft = recentlyViewedContainer.scrollLeft;
        });

        recentlyViewedContainer.addEventListener('mouseleave', () => {
            recentIsDown = false;
            recentlyViewedContainer.style.cursor = 'grab';
        });

        recentlyViewedContainer.addEventListener('mouseup', () => {
            recentIsDown = false;
            recentlyViewedContainer.style.cursor = 'grab';
        });

        recentlyViewedContainer.addEventListener('mousemove', (e) => {
            if (!recentIsDown) return;
            e.preventDefault();
            const x = e.pageX - recentlyViewedContainer.offsetLeft;
            const walk = (x - recentStartX) * 2;
            recentlyViewedContainer.scrollLeft = recentScrollLeft - walk;
        });
    }
}

function initializeAuctionCountdown() {
    // Simulate countdown timers for auctions
    const timeLeftElements = document.querySelectorAll('.time-left');

    timeLeftElements.forEach(element => {
        // Parse initial time
        const timeText = element.textContent.trim();
        const timeMatch = timeText.match(/(\d+)h\s+(\d+)m/);

        if (timeMatch) {
            let hours = parseInt(timeMatch[1]);
            let minutes = parseInt(timeMatch[2]);
            let totalSeconds = (hours * 60 * 60) + (minutes * 60);

            // Update every second
            const interval = setInterval(() => {
                totalSeconds--;

                if (totalSeconds <= 0) {
                    clearInterval(interval);
                    element.innerHTML = '<i class="fas fa-clock"></i> Ended';
                    element.style.color = '#e74c3c';

                    // Find the corresponding bid button and disable it
                    const auctionCard = element.closest('.auction-card');
                    if (auctionCard) {
                        const bidButton = auctionCard.querySelector('.place-bid');
                        if (bidButton) {
                            bidButton.disabled = true;
                            bidButton.textContent = 'Auction Ended';
                        }
                    }
                    return;
                }

                const newHours = Math.floor(totalSeconds / 3600);
                const newMinutes = Math.floor((totalSeconds % 3600) / 60);
                const newSeconds = totalSeconds % 60;

                element.innerHTML = `<i class="fas fa-clock"></i> ${newHours}h ${newMinutes}m ${newSeconds}s left`;

                // Change color when less than 30 minutes left
                if (totalSeconds < 1800) {
                    element.style.color = '#e74c3c';
                }
            }, 1000);
        }
    });

    // Initialize long-press bid functionality
    const bidButtons = document.querySelectorAll('.place-bid');

    bidButtons.forEach(button => {
        let pressTimer;
        let isPressed = false;

        // Create gavel animation element
        const gavelAnimation = document.createElement('div');
        gavelAnimation.className = 'gavel-animation';
        gavelAnimation.innerHTML = '<i class="fas fa-gavel"></i>';

        // Find the current-bid element to place the gavel next to the price
        const auctionCard = button.closest('.auction-card');
        const currentBidElement = auctionCard.querySelector('.current-bid');
        currentBidElement.appendChild(gavelAnimation);

        // Create count number element
        const countNumber = document.createElement('div');
        countNumber.className = 'count-number';
        gavelAnimation.appendChild(countNumber);

        let countInterval;
        let currentCount = 0;

        // Start timer when mouse/touch is down
        const startPress = () => {
            isPressed = true;
            button.classList.add('pressing');

            // Show gavel and start counting
            gavelAnimation.classList.add('show');
            currentCount = 0;

            // Animate gavel and update count every second
            countInterval = setInterval(() => {
                if (isPressed) {
                    currentCount++;
                    countNumber.textContent = currentCount;

                    // Pulsate the gavel
                    gavelAnimation.classList.remove('pulsate');
                    void gavelAnimation.offsetWidth; // Force reflow
                    gavelAnimation.classList.add('pulsate');

                    // After 3 counts, complete the bid
                    if (currentCount === 3) {
                        clearInterval(countInterval);
                    }
                }
            }, 1000);

            pressTimer = setTimeout(() => {
                if (isPressed) {
                    completeBid(button);
                }
            }, 3000); // 3 second press required
        };

        // Cancel timer if mouse/touch is up or leaves button
        const cancelPress = () => {
            if (isPressed) {
                clearTimeout(pressTimer);
                clearInterval(countInterval);
                button.classList.remove('pressing');
                gavelAnimation.classList.remove('show');
                countNumber.textContent = '';
                isPressed = false;
            }
        };

        // Complete the bid process
        const completeBid = (button) => {
            // Make the button stay blue
            button.classList.remove('pressing');
            button.classList.add('bid-complete');

            // Hide the gavel animation
            const gavelAnimation = button.parentElement.querySelector('.gavel-animation');
            if (gavelAnimation) {
                gavelAnimation.classList.remove('show');
                gavelAnimation.classList.remove('pulsate');
                const countNumber = gavelAnimation.querySelector('.count-number');
                if (countNumber) {
                    countNumber.textContent = '';
                }
            }

            // Simulate successful bid
            const auctionCard = button.closest('.auction-card');
            const bidAmount = auctionCard.querySelector('.bid-amount');
            const currentAmount = parseInt(bidAmount.textContent.replace('$', ''));
            bidAmount.textContent = '$' + (currentAmount + 5); // Add $5 to current bid

            // Show MY TOP BID indicator next to the price
            const topBidIndicator = auctionCard.querySelector('.top-bid-indicator');
            topBidIndicator.classList.add('show');

            // Update bid count
            const bidsCount = auctionCard.querySelector('.bids-count');
            const currentBids = parseInt(bidsCount.textContent.match(/\d+/)[0]);
            bidsCount.innerHTML = `<i class="fas fa-gavel"></i> ${currentBids + 1} bids`;

            // Button text confirms action
            button.textContent = 'Bid Placed!';

            // Reset after 3 seconds and disable the button
            setTimeout(() => {
                button.textContent = 'You are top bidder';
                button.classList.remove('bid-complete');
                button.classList.add('disabled');
                button.disabled = true;

                // Keep MY TOP BID showing to indicate user is current top bidder
            }, 3000);
        };

        // Add event listeners for mouse
        button.addEventListener('mousedown', startPress);
        button.addEventListener('mouseup', cancelPress);
        button.addEventListener('mouseleave', cancelPress);

        // Add event listeners for touch
        button.addEventListener('touchstart', (e) => {
            e.preventDefault(); // Prevent default touch behavior
            startPress();
        });
        button.addEventListener('touchend', cancelPress);
        button.addEventListener('touchcancel', cancelPress);
    });
}

function initializeDarkModeToggle() {
    const settingsToggle = document.getElementById('settingsToggle');
    const settingsSubmenu = document.querySelector('.settings-submenu');
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Initialize settings toggle
    if (settingsToggle && settingsSubmenu) {
        settingsToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            settingsSubmenu.style.display = settingsSubmenu.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Initialize dark mode toggle
    if (darkModeToggle) {
        // Check if dark mode preference exists, if not set it to true (dark mode default)
        const darkModePreference = localStorage.getItem('darkMode');
        const isDarkMode = darkModePreference === null ? true : darkModePreference === 'true';
        const icon = darkModeToggle.querySelector('i');
        const textSpan = darkModeToggle.querySelector('span');

        // Set initial state and localStorage for new users
        if (isDarkMode) {
            body.classList.add('dark-mode');
            if (darkModePreference === null) {
                localStorage.setItem('darkMode', 'true');
            }
            icon.classList.replace('fa-moon', 'fa-sun');
            textSpan.textContent = 'Light Mode';
        }

        darkModeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            body.classList.toggle('dark-mode');
            const isDark = body.classList.contains('dark-mode');

            icon.classList.replace(isDark ? 'fa-moon' : 'fa-sun', 
                                 isDark ? 'fa-sun' : 'fa-moon');
            textSpan.textContent = isDark ? 'Light Mode' : 'Dark Mode';
            localStorage.setItem('darkMode', isDark);
        });
    }
}

function initializeCartPreview() {
    // Handle quantity buttons
    const minusButtons = document.querySelectorAll('.quantity-btn.minus');
    const plusButtons = document.querySelectorAll('.quantity-btn.plus');

    minusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const quantityElement = this.nextElementSibling;
            let quantity = parseInt(quantityElement.textContent);
            if (quantity > 1) {
                quantity--;
                quantityElement.textContent = quantity;
                updateCartTotals();
            }
        });
    });

    plusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const quantityElement = this.previousElementSibling;
            let quantity = parseInt(quantityElement.textContent);
            quantity++;
            quantityElement.textContent = quantity;
            updateCartTotals();
        });
    });

    // Update totals when quantity changes
    function updateCartTotals() {
        let subtotal = 0;

        document.querySelectorAll('.cart-item').forEach(item => {
            const price = parseFloat(item.querySelector('.item-price').textContent.replace('$', ''));
            const quantity = parseInt(item.querySelector('.quantity').textContent);
            subtotal += price * quantity;
        });

        const subtotalElement = document.querySelector('.subtotal span:last-child');
        const totalElement = document.querySelector('.total span:last-child');

        if (subtotalElement && totalElement) {
            subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
            totalElement.textContent = `$${subtotal.toFixed(2)}`;
        }
    }

    // Cart header click to toggle
    const minimizeCartBtn = document.querySelector('.minimize-cart');
    if (minimizeCartBtn) {
        minimizeCartBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent event bubbling
            const cartPreview = document.querySelector('.cart-preview');
            if (cartPreview.style.bottom === '0px') {
                cartPreview.style.bottom = '-400px';
                this.innerHTML = '<i class="fas fa-chevron-up"></i>';
            } else {
                cartPreview.style.bottom = '0px';
                this.innerHTML = '<i class="fas fa-chevron-down"></i>';
            }
        });
    }

    // Make entire cart header still clickable
    const cartHeader = document.querySelector('.cart-header');
    if (cartHeader) {
        cartHeader.addEventListener('click', function(e) {
            // Don't trigger if minimize button was clicked
            if (e.target.closest('.minimize-cart')) {
                return;
            }

            const cartPreview = document.querySelector('.cart-preview');
            const minimizeBtn = document.querySelector('.minimize-cart');

            if (cartPreview.style.bottom === '0px') {
                cartPreview.style.bottom = '-400px';
                if (minimizeBtn) {
                    minimizeBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Expand';
                }
            } else {
                cartPreview.style.bottom = '0px';
                if (minimizeBtn) {
                    minimizeBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Minimize';
                }
            }
        });
    }
}

// QR code functionality - copied from dashboard
function toggleQRCode(event) {
    event.stopPropagation();
    const popup = document.getElementById('qrCodePopup');

    if (popup.style.display === 'block') {
        popup.style.display = 'none';
    } else {
        popup.style.display = 'block';

        // Generate QR code if it doesn't exist yet
        if (!document.querySelector('#qrcode canvas')) {
            new QRCode(document.getElementById("qrcode"), {
                text: "https://gorse.dotmobile.app",
                width: 150,
                height: 150,
                colorDark: "#333333",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    }
}

function generateRandomLinkCode() {
    return Math.random().toString(36).substring(2, 12);
}

function initializeBackToTop() {
    // Create back to top button
    const backToTopButton = document.createElement('button');
    backToTopButton.className = 'back-to-top';
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i> Back to Top';
    document.body.appendChild(backToTopButton);

    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        const scrollPosition = window.pageYOffset;
        const screenHeight = window.innerHeight;
        const threshold = screenHeight * 2; // 2x screen height

        if (scrollPosition > threshold) {
            backToTopButton.classList.add('visible');
        } else {
            backToTopButton.classList.remove('visible');
        }
    });

    // Smooth scroll to top when clicked
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Close QR code popup when clicking outside
document.addEventListener('click', function(e) {
    const popup = document.getElementById('qrCodePopup');
    const icon = document.querySelector('.qr-code-icon');

    if (popup && popup.style.display === 'block' && !popup.contains(e.target) && e.target !== icon) {
        popup.style.display = 'none';
    }
});

// Offer cards functionality
let currentCardIndex = 2;
let cardStack = [];
let currentSubscriptionStatus = null;

function populateOfferCards() {
    const offersSection = document.querySelector('.offers-section');
    if (!offersSection) {
        console.log('Offers section not found');
        return;
    }

    // Get dismissed offers from localStorage
    const dismissedOffers = JSON.parse(localStorage.getItem('dismissedOffers') || '[]');

    // Define all possible offers
    const allOffers = [
        {
            id: 'global_data',
            title: 'Truly Global Data',
            description: ['10000MB no expiry data for $20', 'Priority fast 5G+ when available', 'Share infinitely with any member', 'Works on most of planet Earth +10km above it'],
            price: '$20',
            buttonText: 'Buy',
            buttonClass: 'btn-primary',
            action: "showConfirmationDrawer(10, 20, 'global_data_10gb')",
            alwaysShow: true
        },
        {
            id: 'basic_membership',
            title: 'Become a Member',
            description: [
                'Access available connectivity services globally',
                'Priority (QCI 8) fast 5G+ in most (100+) places',
                'Link multi-accounts with one payment method',
                'Yearly, leave anytime, refundable unused data'
            ],
            price: '$24/year',
            buttonText: 'Subscribe',
            buttonClass: 'btn-primary',
            action: "showConfirmationDrawer(10, 24, 'basic_membership')",
            showCondition: shouldShowBasicMembership
        },
        {
            id: 'full_membership',
            title: 'Unlimited Talk + Text',
            description: ['North America Talk + Text (SMS + RCS, no MMS)', 'Global access to Calling + Texting through Wi-Fi', 'Select brand new or Port your own CAN number', 'Yearly service (use as is or with the mobile data)'],
            price: '$66/year',
            buttonText: 'Coming Soon',
            buttonClass: 'btn-secondary',
            action: "alert('Coming soon!')",
            disabled: true,
            alwaysShow: true
        }
    ];

    // Filter offers based on conditions and dismissal status
    const availableOffers = allOffers.filter(offer => {
        // Check if offer is dismissed
        if (dismissedOffers.includes(offer.id)) return false;

        if (offer.alwaysShow) return true;
        if (offer.showCondition) return offer.showCondition();
        return true;
    });

    console.log('Available offers:', availableOffers.length);

    // Handle case when all offers are dismissed
    if (availableOffers.length === 0) {
        offersSection.innerHTML = `
            <div class="no-offers-message" style="text-align: center; padding: 40px; color: rgba(255, 255, 255, 0.7);">
                <p>All offers have been dismissed.</p>
                <button onclick="clearDismissedOffers()" style="background: rgba(255, 255, 255, 0.2); border: none; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 10px;">
                    Show All Offers Again
                </button>
            </div>
        `;
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

function initializeCardStack() {
    if (!cardStack || cardStack.length === 0) {
        console.log('No cards to initialize');
        return;
    }

    updateCardPositions();
    updateIndicators();
}

function updateCardPositions() {
    if (!cardStack || cardStack.length === 0) return;

    cardStack.forEach((card, index) => {
        const offset = index - currentCardIndex;
        const isActive = index === currentCardIndex;
        
        if (isActive) {
            card.style.transform = 'translateX(0) scale(1)';
            card.style.opacity = '1';
            card.style.zIndex = '10';
        } else if (offset > 0) {
            card.style.transform = `translateX(${offset * 20}px) scale(${1 - offset * 0.05})`;
            card.style.opacity = `${1 - offset * 0.3}`;
            card.style.zIndex = `${10 - offset}`;
        } else {
            card.style.transform = `translateX(${offset * 20}px) scale(${1 + offset * 0.05})`;
            card.style.opacity = `${1 + offset * 0.3}`;
            card.style.zIndex = `${10 + offset}`;
        }
        
        card.style.transition = 'all 0.3s ease';
        card.style.position = 'absolute';
        card.style.top = '0';
        card.style.left = '0';
        card.style.width = '100%';
        card.style.height = '100%';
    });
}

function updateIndicators() {
    const indicators = document.querySelectorAll('.indicator-dot');
    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentCardIndex);
    });
}

function goToCard(index) {
    currentCardIndex = index;
    updateCardPositions();
    updateIndicators();
}

function dismissOfferCard(offerId) {
    // Add to dismissed offers
    const dismissedOffers = JSON.parse(localStorage.getItem('dismissedOffers') || '[]');
    if (!dismissedOffers.includes(offerId)) {
        dismissedOffers.push(offerId);
        localStorage.setItem('dismissedOffers', JSON.stringify(dismissedOffers));
    }

    // Animate current card out
    const currentCard = cardStack[currentCardIndex];
    const direction = Math.random() > 0.5 ? 1 : -1;

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

function clearDismissedOffers() {
    localStorage.removeItem('dismissedOffers');
    populateOfferCards();
    setTimeout(() => {
        initializeCardStack();
    }, 100);
}

// Placeholder function for confirmation drawer
function showConfirmationDrawer(amount, price, productType) {
    alert(`Purchase: ${amount}GB for $${price} (${productType})`);
}

// Make functions globally available
window.dismissOfferCard = dismissOfferCard;
window.clearDismissedOffers = clearDismissedOffers;
window.showConfirmationDrawer = showConfirmationDrawer;