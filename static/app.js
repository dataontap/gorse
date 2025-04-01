
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('imeiForm');
    const requestEsimBtn = document.getElementById('requestEsim');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const imei1 = document.getElementById('imei1').value;
        const imei2 = document.getElementById('imei2').value;
        
        try {
            const response = await fetch('/api/imei', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    imei1: imei1,
                    imei2: imei2 || null
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
