
function setupPasswordReset() {
    // Add password reset functionality to login forms
    const loginForms = document.querySelectorAll('form');
    
    loginForms.forEach(form => {
        const emailInput = form.querySelector('input[type="email"]');
        if (emailInput) {
            // Add "Forgot Password?" link
            const forgotLink = document.createElement('a');
            forgotLink.href = '#';
            forgotLink.textContent = 'Forgot Password?';
            forgotLink.style.cssText = 'display: block; margin-top: 10px; color: #007bff; text-decoration: none;';
            
            forgotLink.addEventListener('click', function(e) {
                e.preventDefault();
                const email = emailInput.value;
                if (!email) {
                    alert('Please enter your email address first');
                    return;
                }
                
                sendPasswordReset(email);
            });
            
            form.appendChild(forgotLink);
        }
    });
}

function sendPasswordReset(email) {
    if (window.firebaseAuth && window.firebaseAuth.sendPasswordResetEmail) {
        window.firebaseAuth.sendPasswordResetEmail(email)
            .then(() => {
                alert('Password reset email sent! Please check your inbox.');
            })
            .catch((error) => {
                console.error('Error sending password reset email:', error);
                alert('Error sending password reset email: ' + error.message);
            });
    } else {
        alert('Firebase authentication not available');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', setupPasswordReset);
