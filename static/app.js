
document.addEventListener('DOMContentLoaded', () => {
    const emailForm = document.getElementById('emailForm');
    const imeiForm = document.getElementById('imeiForm');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    let customerEmail = '';
    
    emailForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        customerEmail = email;
        
        try {
            const response = await fetch('/api/delivery', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    method: 'email',
                    contact: email
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                step1.classList.remove('active');
                step2.classList.add('active');
            } else {
                console.error('Server error:', result);
                alert('Error creating customer: ' + (result.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Request error:', error);
            alert('Error creating customer: ' + error.message);
        }
    });
    
    imeiForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const imei1 = document.getElementById('imei1').value;
        
        try {
            const response = await fetch('/api/imei', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    imei1: imei1,
                    email: customerEmail
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                window.location.href = '/static/success.html';
            } else {
                alert('Error requesting eSIM activation: ' + result.message);
            }
        } catch (error) {
            alert('Error requesting eSIM activation');
            console.error(error);
        }
    });
});
