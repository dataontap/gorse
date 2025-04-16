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
});