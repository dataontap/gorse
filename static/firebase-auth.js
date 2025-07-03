
// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyA1dLC68va6gRSyCA4kDQqH1ZWjFkyLivY",
    authDomain: "gorse-24e76.firebaseapp.com",
    projectId: "gorse-24e76",
    storageBucket: "gorse-24e76.appspot.com",
    messagingSenderId: "212829848250",
    appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
    measurementId: "G-WHW3XT925P"
};

// Global variables for auth state
let auth;
let currentUser = null;

// Initialize Firebase
try {
    if (typeof firebase !== 'undefined') {
        firebase.initializeApp(firebaseConfig);
        auth = firebase.auth();
        console.log("Firebase initialized successfully");
        
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
    } else {
        console.error("Firebase SDK not loaded");
    }
} catch (error) {
    console.error("Firebase Auth initialization error:", error);
}

// Sign in with email and password
async function signInWithEmailPassword(email, password) {
    try {
        if (!auth) {
            throw new Error("Firebase Auth not initialized");
        }
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        console.log("Sign in successful:", userCredential.user.email);
        return userCredential;
    } catch (error) {
        console.error("Sign in error:", error);
        throw error;
    }
}

// Sign in with Google
async function signInWithGoogle() {
    try {
        if (!auth) {
            throw new Error("Firebase Auth not initialized");
        }
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await auth.signInWithPopup(provider);
        console.log("Google sign in successful:", result.user.email);
        return result;
    } catch (error) {
        console.error("Google sign in error:", error);
        throw error;
    }
}

// Sign out
async function signOut() {
    try {
        if (!auth) {
            throw new Error("Firebase Auth not initialized");
        }
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

// Make functions globally available
window.firebaseAuth = {
    signInWithEmailPassword: signInWithEmailPassword,
    signInWithGoogle: signInWithGoogle,
    signOut: signOut,
    getCurrentUser: () => currentUser
};

window.signOut = signOut;
window.signInWithEmailPassword = signInWithEmailPassword;
window.signInWithGoogle = signInWithGoogle;
