
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
        const successAlert = document.createElement('div');
        successAlert.className = 'alert alert-success';
        successAlert.textContent = "Sweetz, your eSIM is on its way!";
        document.querySelector('.success-content').prepend(successAlert);
    } catch (error) {
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger';
        errorAlert.textContent = 'Error sending eSIM details';
        document.querySelector('.success-content').prepend(errorAlert);
        console.error(error);
    }
});
