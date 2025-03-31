
document.getElementById('requestEsim').addEventListener('click', async () => {
    try {
        // In a real Android app, this would be replaced with actual IMEI retrieval
        // For demo, we'll use mock data
        const imeiData = {
            imei1: "123456789012345", // This would come from Android TelephonyManager
            imei2: "987654321098765"  // Optional second IMEI
        };

        const response = await fetch('/api/imei', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(imeiData)
        });

        const result = await response.json();
        window.location.href = '/static/success.html';
    } catch (error) {
        alert('Error submitting IMEI information');
        console.error(error);
    }
});
