// Firebase Authentication handler using v9+ modular SDK
// Remove import statements as we're using the Firebase SDK via script tags

document.addEventListener('DOMContentLoaded', function() {
  try {
    // Firebase configuration - using global Firebase object
    const firebaseConfig = {
      apiKey: "AIzaSyA1dLC68va6gRSyCA4kDQqH1ZWjFkyLivY",
      authDomain: "gorse-24e76.firebaseapp.com",
      projectId: "gorse-24e76",
      storageBucket: "gorse-24e76.appspot.com",
      messagingSenderId: "212829848250",
      appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
      measurementId: "G-WHW3XT925P"
    };

    // Initialize Firebase using global Firebase object
    const app = firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    console.log("Firebase Auth initialized successfully");

    // Configure Google auth provider
    const googleProvider = new firebase.auth.GoogleAuthProvider();

    // Track auth state changes
    firebase.auth().onAuthStateChanged(function(user) {
      if (user) {
        // User is signed in
        console.log("User is signed in:", user);

        // Store user ID in localStorage for client-side use
        localStorage.setItem('userId', user.uid);
        localStorage.setItem('userEmail', user.email);

        // Register user with our backend
        registerUserWithBackend(user);

        // Only auto-redirect from signup page, not from root page or login page
        // This allows users to stay logged out on the root page
        const currentPath = window.location.pathname;
        if (currentPath === '/signup') {
          window.location.href = '/dashboard';
        }
        // Root page and login page are allowed for signed-in users (no auto-redirect)
      } else {
        // User is signed out
        console.log("User is signed out");

        // Clear localStorage
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');

        // Only redirect to home if on protected pages, not from login page
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
        return firebase.auth().signInWithEmailAndPassword(email, password)
          .catch(error => {
            console.error("Auth error:", error);
            throw error;
          });
      },

      signInWithGoogle: function() {
        return firebase.auth().signInWithPopup(googleProvider)
          .catch(error => {
            console.error("Google sign-in error:", error);
            throw error;
          });
      },

      createUserWithEmailPassword: function(email, password) {
        return firebase.auth().createUserWithEmailAndPassword(email, password)
          .catch(error => {
            console.error("User creation error:", error);
            throw error;
          });
      },

      signOut: function() {
        return firebase.auth().signOut()
          .then(() => {
            // Clear all local storage
            localStorage.removeItem('userId');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('databaseUserId');
            console.log('User signed out successfully');
            
            // Redirect to login page after logout
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          })
          .catch((error) => {
            console.error('Error during sign out:', error);
          });
      },

      getCurrentUser: function() {
        return firebase.auth().currentUser;
      }
    };
  } catch (error) {
    console.error("Firebase Auth initialization error:", error);
  }
});