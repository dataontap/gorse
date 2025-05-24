
// Firebase Authentication handler
document.addEventListener('DOMContentLoaded', function() {
  // Firebase configuration is already initialized in firebase-init.js
  try {
    // Initialize auth
    if (!firebase.apps.length) {
      // Initialize Firebase if not already done
      firebase.initializeApp({
        apiKey: "AIzaSyA1dLC68va6gRSyCA4kDQqH1ZWjFkyLivY",
        authDomain: "gorse-24e76.firebaseapp.com",
        projectId: "gorse-24e76",
        storageBucket: "gorse-24e76.appspot.com",
        messagingSenderId: "212829848250",
        appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
        measurementId: "G-WHW3XT925P"
      });
    }
    
    const auth = firebase.auth();
    
    // Configure Google auth provider
    const googleProvider = new firebase.auth.GoogleAuthProvider();
    
    // Track auth state changes
    auth.onAuthStateChanged(function(user) {
      if (user) {
        // User is signed in
        console.log("User is signed in:", user);
        
        // Store user ID in localStorage for client-side use
        localStorage.setItem('userId', user.uid);
        localStorage.setItem('userEmail', user.email);
        
        // Register user with our backend
        registerUserWithBackend(user);
        
        // Redirect to dashboard if on login/signup page
        const currentPath = window.location.pathname;
        if (currentPath === '/' || currentPath === '/signup') {
          window.location.href = '/dashboard';
        }
      } else {
        // User is signed out
        console.log("User is signed out");
        
        // Clear localStorage
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');
        
        // Redirect to home if on protected page
        const currentPath = window.location.pathname;
        const publicPages = ['/', '/signup'];
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
        return auth.signInWithEmailAndPassword(email, password);
      },
      
      signInWithGoogle: function() {
        return auth.signInWithPopup(googleProvider);
      },
      
      createUserWithEmailPassword: function(email, password) {
        return auth.createUserWithEmailAndPassword(email, password);
      },
      
      signOut: function() {
        return auth.signOut();
      },
      
      getCurrentUser: function() {
        return auth.currentUser;
      }
    };
  } catch (error) {
    console.error("Firebase Auth initialization error:", error);
  }
});
