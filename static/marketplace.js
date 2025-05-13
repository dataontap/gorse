document.addEventListener('DOMContentLoaded', function() {
    initializeMarketplace();
    initializeServiceCarousel();
    initializeAuctionCountdown();
    initializeCartPreview();
});

function initializeMarketplace() {
    // Implement dark mode compatibility
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }

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
                text: "https://replit.dev/link/" + generateRandomLinkCode(),
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

// Close QR code popup when clicking outside
document.addEventListener('click', function(e) {
    const popup = document.getElementById('qrCodePopup');
    const icon = document.querySelector('.qr-code-icon');

    if (popup && popup.style.display === 'block' && !popup.contains(e.target) && e.target !== icon) {
        popup.style.display = 'none';
    }
});