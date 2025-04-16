
document.addEventListener('DOMContentLoaded', function() {
    const emailForm = document.getElementById('emailForm');
    const imeiForm = document.getElementById('imeiForm');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');

    if (emailForm) {
        emailForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            
            fetch('/customer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: email })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    step1.classList.remove('active');
                    step2.classList.add('active');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }

    if (imeiForm) {
        imeiForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const imei1 = document.getElementById('imei1').value;
            
            fetch('/imei', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ imei1: imei1 })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = '/static/success.html';
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
});
