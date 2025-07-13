The code implements Firebase authentication, user data retrieval from the backend, demo mode, and UI updates, ensuring a smooth user experience.
```

```replit_final_file
// Firebase Authentication handler using Firebase SDK v8
document.addEventListener('DOMContentLoaded', function() {
  console.log("Firebase auth script loading...");
  
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

  let initAttempts = 0;
  const maxAttempts = 10;

  // Wait for Firebase SDK to load with proper error handling
  function initializeFirebaseAuth() {
    try {
      initAttempts++;
      
      // Check if Firebase is loaded
      if (typeof firebase === 'undefined') {
        if (initAttempts < maxAttempts) {
          console.log(`Firebase SDK not loaded - attempt ${initAttempts}/${maxAttempts}, waiting...`);
          setTimeout(initializeFirebaseAuth, 1000);
          return;
        } else {
          console.error("Firebase SDK failed to load after maximum attempts");
          showFirebaseUnavailable();
          return;
        }
      }

      // Initialize Firebase if not already initialized
      if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
        console.log("Firebase App initialized successfully");
      } else {
        console.log("Firebase App already initialized");
      }

      // Test Firebase Auth availability
      const auth = firebase.auth();
      if (!auth) {
        throw new Error("Firebase Auth not available");
      }
      
      console.log("Firebase Auth initialized successfully");
      
      // Set up auth state listener
      setupAuthStateListener();
      
    } catch (error) {
      console.error("Firebase initialization error:", error);
      if (initAttempts < maxAttempts) {
        setTimeout(initializeFirebaseAuth, 2000);
      } else {
        showFirebaseUnavailable();
      }
    }
  }

  function showFirebaseUnavailable() {
    console.error("Firebase authentication is not available");
    
    // Update UI to show Firebase is unavailable
    const authContainer = document.getElementById('auth-container');
    const userInfo = document.getElementById('user-info');
    
    if (authContainer) {
      authContainer.innerHTML = `
        <div class="firebase-unavailable">
          <p style="color: #ff6b6b; text-align: center; margin: 20px 0;">
            🔥 Authentication service is temporarily unavailable
          </p>
          <button onclick="enableDemoMode()" class="demo-mode-btn">
            🎮 Try Demo Mode Instead
          </button>
          <button onclick="location.reload()" class="retry-btn" style="margin-top: 10px;">
            🔄 Retry Connection
          </button>
        </div>
      `;
    }

    if (userInfo) {
      userInfo.innerHTML = `
        <div class="firebase-unavailable">
          <h2>🔥 Authentication Service Unavailable</h2>
          <p>The authentication service is currently not available. You can:</p>
          <ul>
            <li>Try demo mode to explore the platform</li>
            <li>Refresh the page to retry the connection</li>
            <li>Check back later when the service is restored</li>
          </ul>
        </div>
      `;
    }

    // Set up global auth functions with error handling
    setupFallbackAuthFunctions();
  }

  function setupAuthStateListener() {
    // Configure Google auth provider
    const googleProvider = new firebase.auth.GoogleAuthProvider();

    // Global user data
    let currentUserData = null;

    // Auth state observer
    firebase.auth().onAuthStateChanged(async (user) => {
      console.log('Auth state changed:', user ? 'signed in' : 'signed out');

      if (user) {
          console.log('User is signed in:', user.uid);

          // Register user in backend and get full user data
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

              const result = await response.json();
              console.log('User registration result:', result);

              // Get full user data including balance
              const userDataResponse = await fetch(`/api/auth/current-user?firebaseUid=${user.uid}`);
              const userData = await userDataResponse.json();

              if (userData.status === 'success') {
                  currentUserData = {
                      uid: user.uid,
                      email: userData.email,
                      displayName: userData.displayName,
                      photoURL: userData.photoURL,
                      userId: userData.userId,
                      stripeCustomerId: userData.stripeCustomerId,
                      imei: userData.imei,
                      founderStatus: userData.founderStatus
                  };

                  // Get user balance
                  const balanceResponse = await fetch(`/api/user/data-balance?firebaseUid=${user.uid}`);
                  const balanceData = await balanceResponse.json();
                  currentUserData.dataBalance = balanceData.dataBalance || 0;

                  console.log('Complete user data loaded:', currentUserData);

                  // Store in localStorage
                  localStorage.setItem('currentUser', JSON.stringify(currentUserData));

                  // Update UI with real user data
                  updateAuthUI(user, currentUserData);
              } else {
                  console.error('Failed to get user data:', userData);
                  // Fallback to basic Firebase data
                  updateAuthUI(user, null);
              }

          } catch (error) {
              console.error('Error getting user data:', error);
              // Fallback to basic Firebase data
              updateAuthUI(user, null);
          }

      } else {
          console.log('User is signed out');
          currentUserData = null;
          localStorage.removeItem('currentUser');
          updateAuthUI(null, null);
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

     function updateAuthUI(user, userData = null) {
        const authContainer = document.getElementById('auth-container');
        const userInfo = document.getElementById('user-info');

        if (user && userData) {
            // User is signed in with complete data
            if (authContainer) {
                authContainer.innerHTML = `
                    <div class="user-profile">
                        <img src="${userData.photoURL || '/static/default-avatar.png'}" alt="Profile" class="profile-img">
                        <span class="user-name">${userData.displayName || userData.email}</span>
                        <span class="user-balance">Balance: ${userData.dataBalance}GB</span>
                        <button onclick="signOut()" class="sign-out-btn">Sign Out</button>
                    </div>
                `;
            }

            if (userInfo) {
                const founderBadge = userData.founderStatus === 'Y' ? '<span class="founder-badge">👑 Founder</span>' : '';
                userInfo.innerHTML = `
                    <h2>Welcome, ${userData.displayName || 'User'}! ${founderBadge}</h2>
                    <p>Email: ${userData.email}</p>
                    <p>User ID: ${userData.userId}</p>
                    <p>Data Balance: ${userData.dataBalance} GB</p>
                    <p>Status: ${userData.founderStatus === 'Y' ? 'Founding Member' : 'Member'}</p>
                    ${userData.imei ? `<p>IMEI: ${userData.imei}</p>` : ''}
                `;
            }

            // Update any balance displays on the page
            updateBalanceDisplays(userData.dataBalance);

        } else if (user) {
            // User is signed in but data is loading or unavailable
            if (authContainer) {
                authContainer.innerHTML = `
                    <div class="user-profile">
                        <img src="${user.photoURL || '/static/default-avatar.png'}" alt="Profile" class="profile-img">
                        <span class="user-name">${user.displayName || user.email}</span>
                        <span class="loading">Loading...</span>
                        <button onclick="signOut()" class="sign-out-btn">Sign Out</button>
                    </div>
                `;
            }

            if (userInfo) {
                userInfo.innerHTML = `
                    <h2>Welcome, ${user.displayName || 'User'}!</h2>
                    <p>Email: ${user.email}</p>
                    <p>Loading your data...</p>
                `;
            }
        } else {
            // User is signed out - show demo mode
            if (authContainer) {
                authContainer.innerHTML = `
                    <button onclick="signInWithGoogle()" class="sign-in-btn">
                        <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google" width="20">
                        Sign in with Google
                    </button>
                    <button onclick="enableDemoMode()" class="demo-mode-btn">
                        🎮 Try Demo Mode
                    </button>
                `;
            }

            if (userInfo) {
                userInfo.innerHTML = `
                    <div class="demo-notice">
                        <p>👋 You're not signed in</p>
                        <p>Sign in to access your personal data, or try demo mode</p>
                    </div>
                `;
            }

            // Show demo data if demo mode is active
            if (isDemoMode()) {
                showDemoData();
            }
        }
    }

    function updateBalanceDisplays(balance) {
        // Update balance displays throughout the app
        const balanceElements = document.querySelectorAll('.user-balance, .data-balance, #data-balance');
        balanceElements.forEach(element => {
            element.textContent = `${balance} GB`;
        });
    }

    function isDemoMode() {
        return localStorage.getItem('demoMode') === 'true';
    }

    function enableDemoMode() {
        localStorage.setItem('demoMode', 'true');
        showDemoData();
        updateAuthUI(null, null);
    }

    function disableDemoMode() {
        localStorage.removeItem('demoMode');
        updateAuthUI(null, null);
    }

    function showDemoData() {
        const userInfo = document.getElementById('user-info');
        if (userInfo) {
            userInfo.innerHTML = `
                <div class="demo-mode-active">
                    <h2>🎮 Demo Mode Active</h2>
                    <p>Name: Demo User</p>
                    <p>Email: demo@example.com</p>
                    <p>Data Balance: 5.5 GB</p>
                    <p>Status: Demo Member</p>
                    <button onclick="disableDemoMode()" class="exit-demo-btn">Exit Demo Mode</button>
                </div>
            `;
        }

        // Update balance displays with demo data
        updateBalanceDisplays(5.5);
    }

    function getCurrentUser() {
        const user = JSON.parse(localStorage.getItem('currentUser') || 'null');
        if (user) {
            return user;
        } else if (isDemoMode()) {
            return {
                uid: 'demo_user',
                email: 'demo@example.com',
                displayName: 'Demo User',
                userId: 1,
                dataBalance: 5.5,
                founderStatus: 'N'
            };
        }
        return null;
    }

    // Expose auth functions to global scope
    window.firebaseAuth = {
      signInWithEmailPassword: function(email, password) {
        if (!firebase || !firebase.auth) {
          console.error('Firebase auth not available for email sign-in');
          return Promise.reject(new Error('Authentication service not available'));
        }
        return firebase.auth().signInWithEmailAndPassword(email, password)
          .catch(error => {
            console.error("Auth error:", error);
            throw error;
          });
      },

      signInWithGoogle: function() {
        if (!firebase || !firebase.auth) {
          console.error('Firebase auth not available for Google sign-in');
          return Promise.reject(new Error('Authentication service not available'));
        }
        const googleProvider = new firebase.auth.GoogleAuthProvider();
        return firebase.auth().signInWithPopup(googleProvider)
          .catch(error => {
            console.error("Google sign-in error:", error);
            throw error;
          });
      },

      createUserWithEmailPassword: function(email, password) {
        if (!firebase || !firebase.auth) {
          console.error('Firebase auth not available for user creation');
          return Promise.reject(new Error('Authentication service not available'));
        }
        return firebase.auth().createUserWithEmailAndPassword(email, password)
          .catch(error => {
            console.error("User creation error:", error);
            throw error;
          });
      },

      signOut: function() {
        if (!firebase || !firebase.auth) {
          console.error('Firebase auth not available');
          // Clear localStorage and redirect anyway
          localStorage.removeItem('userId');
          localStorage.removeItem('userEmail');
          localStorage.removeItem('databaseUserId');
          localStorage.removeItem('currentUser');
          window.location.href = '/';
          return Promise.resolve();
        }

        return firebase.auth().signOut()
          .then(() => {
            // Clear all local storage
            localStorage.removeItem('userId');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('databaseUserId');
            localStorage.removeItem('currentUser');
            console.log('User signed out successfully');

            // Redirect to home page after logout  
            window.location.href = '/';
          })
          .catch((error) => {
            console.error('Error during sign out:', error);
            // Clear localStorage and redirect anyway
            localStorage.removeItem('userId');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('databaseUserId');
            localStorage.removeItem('currentUser');
            window.location.href = '/';
          });
      },

      getCurrentUser: function() {
        if (!firebase || !firebase.auth) {
          return null;
        }
        return firebase.auth().currentUser;
      }
    };
  }

  function setupFallbackAuthFunctions() {
    // Set up fallback auth functions when Firebase is not available
    window.firebaseAuth = {
      signInWithEmailPassword: function(email, password) {
        return Promise.reject(new Error('Authentication service not available'));
      },

      signInWithGoogle: function() {
        return Promise.reject(new Error('Authentication service not available'));
      },

      createUserWithEmailPassword: function(email, password) {
        return Promise.reject(new Error('Authentication service not available'));
      },

      signOut: function() {
        localStorage.clear();
        window.location.href = '/';
        return Promise.resolve();
      },

      getCurrentUser: function() {
        return null;
      }
    };
  }

    // Make functions globally available
    window.signInWithGoogle = function() {
      console.log("signInWithGoogle called");
      if (window.firebaseAuth && window.firebaseAuth.signInWithGoogle) {
        return window.firebaseAuth.signInWithGoogle();
      } else {
        console.error('Firebase auth not available');
        alert('Authentication service not available. Please refresh the page and try again.');
        return Promise.reject(new Error('Authentication service not available'));
      }
    };

    window.signOut = function() {
      console.log("signOut called");
      if (window.firebaseAuth && window.firebaseAuth.signOut) {
        return window.firebaseAuth.signOut();
      } else {
        console.error('Firebase auth not available');
        localStorage.clear();
        window.location.href = '/';
      }
    };

    window.enableDemoMode = function() {
      localStorage.setItem('demoMode', 'true');
      showDemoData();
      updateAuthUI(null, null);
    };

    window.disableDemoMode = function() {
      localStorage.removeItem('demoMode');
      updateAuthUI(null, null);
    };

    window.getCurrentUser = function() {
      const user = JSON.parse(localStorage.getItem('currentUser') || 'null');
      if (user) {
        return user;
      } else if (isDemoMode()) {
        return {
          uid: 'demo_user',
          email: 'demo@example.com',
          displayName: 'Demo User',
          userId: 1,
          dataBalance: 5.5,
          founderStatus: 'N'
        };
      }
      return null;
    };

  } catch (error) {
    console.error("Firebase Auth initialization error:", error);
  }
});