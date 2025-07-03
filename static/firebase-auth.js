// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyDjjW2ot6L1XpKYtYU8KUnTj4IXmOaHfqw",
    authDomain: "dotmobile-1c6d0.firebaseapp.com",
    databaseURL: "https://dotmobile-1c6d0-default-rtdb.firebaseio.com",
    projectId: "dotmobile-1c6d0",
    storageBucket: "dotmobile-1c6d0.appspot.com",
    messagingSenderId: "885084103094",
    appId: "1:885084103094:web:c2e93ab65f45f9bfd94c58",
    measurementId: "G-LPC0CTF5KC"
};

// Initialize Firebase
try {
    firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    console.log("Firebase initialized successfully");
} catch (error) {
    console.error("Firebase Auth initialization error:", error);
}

// Global variables for auth state
let currentUser = null;

// Auth state observer
auth.onAuthStateChanged(async (user) => {
    if (user) {
        currentUser = user;
        console.log("User signed in:", user.email);

        // Register user with backend
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    firebaseUid: user.uid,
                    email: user.email,
                    displayName: user.displayName,
                    photoURL: user.photoURL
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log("User registered with backend:", result);
            } else {
                console.error("Failed to register user with backend");
            }
        } catch (error) {
            console.error("Error registering user with backend:", error);
        }

        // Update UI for signed in user
        updateUIForSignedInUser(user);
    } else {
        currentUser = null;
        console.log("User signed out");
        updateUIForSignedOutUser();
    }
});

// Sign in with email and password
async function signInWithEmail(email, password) {
    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        console.log("Sign in successful:", userCredential.user.email);
        return { success: true, user: userCredential.user };
    } catch (error) {
        console.error("Sign in error:", error);
        return { success: false, error: error.message };
    }
}

// Sign out
async function signOut() {
    try {
        await auth.signOut();
        console.log("Sign out successful");
        return { success: true };
    } catch (error) {
        console.error("Sign out error:", error);
        return { success: false, error: error.message };
    }
}

// Update UI for signed in user
function updateUIForSignedInUser(user) {
    // Hide sign in forms
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.style.display = 'none';
    }

    // Show user info if elements exist
    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
        userInfo.style.display = 'block';
        userInfo.innerHTML = `
            <p>Welcome, ${user.displayName || user.email}!</p>
            <button onclick="signOut()" class="btn-secondary">Sign Out</button>
        `;
    }

    // Auto-redirect to dashboard if on login page
    if (window.location.pathname === '/login' || window.location.pathname === '/') {
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1000);
    }
}

// Update UI for signed out user
function updateUIForSignedOutUser() {
    // Show sign in forms
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.style.display = 'block';
    }

    // Hide user info
    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
        userInfo.style.display = 'none';
    }

    // Redirect to login if on protected pages
    const protectedPages = ['/dashboard', '/profile', '/network', '/payments', '/marketplace', '/tokens'];
    if (protectedPages.includes(window.location.pathname)) {
        window.location.href = '/login';
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log("Firebase Auth initialized");

    // Set up login form if it exists
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const result = await signInWithEmail(email, password);

            if (result.success) {
                console.log("Login successful");
            } else {
                alert("Login failed: " + result.error);
            }
        });
    }
});

// Make functions globally available
window.signOut = signOut;
window.signInWithEmail = signInWithEmail;