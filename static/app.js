document.addEventListener('DOMContentLoaded', () => {
    const emailForm = document.getElementById('emailForm');
    const imeiForm = document.getElementById('imeiForm');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');

    emailForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;

        try {
            const response = await fetch('/api/customer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })
            });

            if (response.ok) {
                step1.classList.remove('active');
                step2.classList.add('active');
            } else {
                const error = await response.json();
                alert(error.message || 'Error creating customer');
            }
        } catch (error) {
            console.error('Request error:', error);
            alert('Error submitting form');
        }
    });

    imeiForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const imei1 = document.getElementById('imei1').value;

        try {
            const response = await fetch('/api/imei', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ imei1 })
            });

            if (response.ok) {
                window.location.href = '/static/success.html';
            } else {
                const error = await response.json();
                alert(error.message || 'Error submitting IMEI');
            }
        } catch (error) {
            console.error('Request error:', error);
            alert('Error submitting form');
        }
    });

    document.querySelectorAll('.sort-icon').forEach(icon => {
            icon.addEventListener('click', function() {
                // Update active state
                document.querySelectorAll('.sort-icon').forEach(i => i.classList.remove('active'));
                this.classList.add('active');

                const sortType = this.dataset.sort;
                const container = document.querySelector('.container');
                const cards = Array.from(document.getElementsByClassName('user-card'));

                // Add sorting class to trigger animation
                cards.forEach(card => {
                    card.classList.add('sorting');
                });

                if (sortType === 'newest') {
                    // Sort by timestamp
                    cards.sort((a, b) => {
                        const timeA = new Date(a.querySelector('.timestamp').textContent);
                        const timeB = new Date(b.querySelector('.timestamp').textContent);
                        return timeB - timeA;
                    });
                } else {
                    // Sort by usage
                    cards.sort((a, b) => {
                        const usageA = parseInt(a.querySelector('.usage-amount')?.textContent || '0');
                        const usageB = parseInt(b.querySelector('.usage-amount')?.textContent || '0');
                        return sortType === 'asc' ? usageA - usageB : usageB - usageA;
                    });
                }

                // Stagger the reinsert animation
                setTimeout(() => {
                    // Remove all user cards
                    cards.forEach(card => card.remove());

                    // Add sorted cards back with staggered delay
                    const addUserContainer = document.querySelector('.add-user-container');
                    cards.forEach((card, index) => {
                        setTimeout(() => {
                            container.insertBefore(card, addUserContainer);
                            // Remove sorting class after animation
                            setTimeout(() => card.classList.remove('sorting'), 600);
                        }, index * 100);
                    });
                }, 300);
            });
        });
});