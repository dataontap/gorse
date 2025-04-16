
document.addEventListener('DOMContentLoaded', function() {
    const emailForm = document.getElementById('emailForm');
    const imeiForm = document.getElementById('imeiForm');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');

    if (emailForm) {
        emailForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = document.getElementById('email');
            if (!emailInput) return;
            
            fetch('/customer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: emailInput.value })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && step1 && step2) {
                    step1.style.display = 'none';
                    step2.style.display = 'block';
                } else {
                    alert('Error: ' + (data.message || 'Unknown error occurred'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting the form');
            });
        });
    }

    if (imeiForm) {
        imeiForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const imeiInput = document.getElementById('imei1');
            if (!imeiInput) return;
            
            fetch('/imei', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ imei1: imeiInput.value })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = '/success.html';
                } else {
                    alert('Error: ' + (data.message || 'Unknown error occurred'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting the form');
            });
        });
    }
});
