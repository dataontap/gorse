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
        return firebase.auth().signInWithEmailAndPassword(email, password)
          .catch(function(error) {
            console.error("Auth error:", error);
            throw error;
          });
      },

      signInWithGoogle: function() {
        return firebase.auth().signInWithPopup(googleProvider)
          .catch(function(error) {
            console.error("Google sign-in error:", error);
            throw error;
          });
      },

      createUserWithEmailPassword: function(email, password) {
        return firebase.auth().createUserWithEmailAndPassword(email, password)
          .catch(function(error) {
            console.error("User creation error:", error);
            throw error;
          });
      },

      signOut: function() {
        return firebase.auth().signOut();
      },

      getCurrentUser: function() {
        return firebase.auth().currentUser;
      },

      sendPasswordResetEmail: function(email) {
        return firebase.auth().sendPasswordResetEmail(email)
          .catch(function(error) {
            console.error("Password reset error:", error);
            throw error;
          });
      },

      sendEmailVerification: function() {
        var user = firebase.auth().currentUser;
        if (user) {
          return user.sendEmailVerification()
            .catch(function(error) {
              console.error("Email verification error:", error);
              throw error;
            });
        }
        return Promise.reject(new Error("No user signed in"));
      }
    };
  } catch (error) {
    console.error("Firebase Auth initialization error:", error);
  }
});