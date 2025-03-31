
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
        alert(result.message);
    } catch (error) {
        alert('Error sending eSIM details');
        console.error(error);
    }
});
