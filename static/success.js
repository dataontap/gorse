
document.getElementById('deliveryMethod').addEventListener('change', function() {
    const emailField = document.getElementById('emailField');
    const phoneField = document.getElementById('phoneField');
    
    if (this.value === 'email') {
        emailField.style.display = 'block';
        phoneField.style.display = 'none';
    } else {
        emailField.style.display = 'none';
        phoneField.style.display = 'block';
    }
});

document.getElementById('deliveryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const deliveryMethod = document.getElementById('deliveryMethod').value;
    let contact;
    
    if (deliveryMethod === 'email') {
        contact = document.getElementById('email').value;
    } else {
        const countryCode = document.getElementById('countryCode').value;
        const phone = document.getElementById('phone').value;
        contact = countryCode + phone;
    }
    
    try {
        const response = await fetch('/api/delivery', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                method: deliveryMethod,
                contact: contact
            })
        });
        
        const result = await response.json();
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            Sweetz, your eSIM is on its way!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.success-content').prepend(alertDiv);
        
        // Redirect to progress page after 1.5 seconds
        setTimeout(() => {
            window.location.href = '/static/progress.html';
        }, 1500);
    } catch (error) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            Error sending eSIM details
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.success-content').prepend(alertDiv);
        console.error(error);
    }
});
