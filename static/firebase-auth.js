// Firebase Authentication handler using v9+ modular SDK
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js';
import { 
  getAuth, 
  onAuthStateChanged, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signInWithPopup, 
  GoogleAuthProvider,
  signOut 
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js';

document.addEventListener('DOMContentLoaded', function() {
  try {
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

    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    console.log("Firebase Auth initialized successfully");

    // Configure Google auth provider
    const googleProvider = new GoogleAuthProvider();

    // Track auth state changes
    onAuthStateChanged(auth, function(user) {
      if (user) {
        // User is signed in
        console.log("User is signed in:", user);

        // Store user ID in localStorage for client-side use
        localStorage.setItem('userId', user.uid);
        localStorage.setItem('userEmail', user.email);

        // Register user with our backend
        registerUserWithBackend(user);

        // Redirect to dashboard if on signup page, but allow login page access
        const currentPath = window.location.pathname;
        if (currentPath === '/' || currentPath === '/signup') {
          window.location.href = '/dashboard';
        }
        // Note: Login page (/login) is allowed for signed-in users
      } else {
        // User is signed out
        console.log("User is signed out");

        // Clear localStorage
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');

        // Redirect to home if on protected page
        const currentPath = window.location.pathname;
        const publicPages = ['/', '/signup', '/login'];
        if (!publicPages.includes(currentPath)) {
          window.location.href = '/';
        }
      }
    });

    // Register user with our backend API
    function registerUserWithBackend(firebaseUser) {
      // Send Firebase user info to backend
      fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          firebaseUid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          photoURL: firebaseUser.photoURL
        })
      })
      .then(response => response.json())
      .then(data => {
        console.log('User registered with backend:', data);
        if (data.userId) {
          localStorage.setItem('databaseUserId', data.userId);
        }
      })
      .catch(error => {
        console.error('Error registering user with backend:', error);
      });
    }

    // Expose auth functions to global scope
    window.firebaseAuth = {
      signInWithEmailPassword: function(email, password) {
        return signInWithEmailAndPassword(auth, email, password)
          .catch(error => {
            console.error("Auth error:", error);
            throw error;
          });
      },

      signInWithGoogle: function() {
        return signInWithPopup(auth, googleProvider)
          .catch(error => {
            console.error("Google sign-in error:", error);
            throw error;
          });
      },

      createUserWithEmailPassword: function(email, password) {
        return createUserWithEmailAndPassword(auth, email, password)
          .catch(error => {
            console.error("User creation error:", error);
            throw error;
          });
      },

      signOut: function() {
        return signOut(auth);
      },

      getCurrentUser: function() {
        return auth.currentUser;
      }
    };
  } catch (error) {
    console.error("Firebase Auth initialization error:", error);
  }
});