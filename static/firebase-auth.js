// Firebase Authentication handler using Firebase SDK v8
// Global flag to prevent duplicate initialization
if (window.firebaseAuthLoaded) {
  console.log("Firebase auth script already loaded, skipping...");
  // Exit early by wrapping the rest in a conditional
} else {
window.firebaseAuthLoaded = true;

document.addEventListener('DOMContentLoaded', function() {
  // Prevent duplicate initialization
  if (window.firebaseInitialized) {
    console.log("Firebase already initialized, skipping...");
    return;
  }

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

      // Check if Firebase Auth is available
      if (!firebase.auth) {
        console.error("Firebase Auth module not available");
        if (initAttempts < maxAttempts) {
          setTimeout(initializeFirebaseAuth, 1000);
          return;
        } else {
          showFirebaseUnavailable();
          return;
        }
      }

      // Initialize Firebase if not already initialized
      try {
        if (!firebase.apps.length) {
          firebase.initializeApp(firebaseConfig);
          console.log("Firebase App initialized successfully");
        } else {
          console.log("Firebase App already initialized");
        }
      } catch (error) {
        if (error.code === 'app/duplicate-app') {
          console.log("Firebase app already exists, using existing instance");
        } else {
          console.error("Firebase App initialization error:", error);
        }
      }

      // Test Firebase Auth availability
      const auth = firebase.auth();
      if (!auth) {
        throw new Error("Firebase Auth not available");
      }

      console.log("Firebase Auth initialized successfully");
      
      // Mark as initialized to prevent duplicates
      window.firebaseInitialized = true;

      // Set up auth state listener only once
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
        <div class="firebase-unavailable-error" style="background: rgba(255, 107, 107, 0.15); border: 1px solid rgba(255, 107, 107, 0.3); border-radius: 8px; padding: 15px; margin-bottom: 20px;">
          <p style="color: #ff6b6b; text-align: center; margin: 10px 0;">
            🔥 Authentication service is temporarily unavailable.
          </p>
          <p style="color: #ff6b6b; text-align: center; margin: 10px 0; font-size: 14px;">
            Please refresh the page and try again.
          </p>
          <div style="text-align: center;">
            <button onclick="location.reload()" style="background: rgba(255, 107, 107, 0.2); border: 1px solid #ff6b6b; color: #ff6b6b; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
              🔄 Retry Connection
            </button>
          </div>
        </div>
        <div class="demo-mode-section" style="text-align: center;">
          <p style="color: #cccccc; margin-bottom: 15px; font-size: 16px;">
            Or explore without signing in:
          </p>
          <button onclick="enableDemoMode()" class="demo-mode-btn" style="background: rgba(116, 192, 252, 0.2); border: 1px solid #74c0fc; color: #74c0fc; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px;">
            🎮 Try Demo Mode
          </button>
        </div>
      `;
    }

    if (userInfo) {
      userInfo.innerHTML = `
        <div class="firebase-unavailable" style="text-align: center; padding: 20px;">
          <h2 style="color: #ff6b6b; margin-bottom: 15px;">🔥 Authentication Service Unavailable</h2>
          <p style="color: #cccccc; margin-bottom: 20px;">The authentication service is currently not available. You can:</p>
          <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 15px; margin-bottom: 20px;">
            <ul style="text-align: left; color: #cccccc; margin: 0; padding-left: 20px;">
              <li>Refresh the page to retry the connection</li>
              <li>Check back later when the service is restored</li>
              <li>Try demo mode to explore the platform features</li>
            </ul>
          </div>
          <button onclick="enableDemoMode()" style="background: rgba(116, 192, 252, 0.2); border: 1px solid #74c0fc; color: #74c0fc; padding: 12px 24px; border-radius: 8px; cursor: pointer;">
            🎮 Try Demo Mode
          </button>
        </div>
      `;
    }

    // Set up global auth functions with error handling
    setupFallbackAuthFunctions();
  }

  function setupAuthStateListener() {
    // Prevent multiple auth state listeners
    if (window.authStateListenerSetup) {
      console.log("Auth state listener already set up, skipping...");
      return;
    }
    window.authStateListenerSetup = true;

    // Configure Google auth provider
    const googleProvider = new firebase.auth.GoogleAuthProvider();

    // Global user data
    let currentUserData = null;
    let isProcessingAuth = false;

    // Auth state observer
    firebase.auth().onAuthStateChanged(async (user) => {
      // Prevent concurrent processing of auth state changes
      if (isProcessingAuth) {
        console.log('Auth state change already being processed, skipping...');
        return;
      }

      console.log('Auth state changed:', user ? 'signed in' : 'signed out');

      if (user) {
          isProcessingAuth = true;
          console.log('User is signed in:', user.uid);

          // Prevent duplicate registration requests for the same user
          const registrationKey = `registration_${user.uid}`;
          if (window.pendingRequests && window.pendingRequests[registrationKey]) {
            console.log('Registration already in progress for this user, skipping...');
            isProcessingAuth = false;
            return;
          }

          // Mark registration as in progress
          window.pendingRequests = window.pendingRequests || {};
          window.pendingRequests[registrationKey] = true;

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

              // Clear the pending registration
              delete window.pendingRequests[registrationKey];

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

                  // Set initial balance and load it asynchronously
                  currentUserData.dataBalance = 0;

                  // Load balance asynchronously with delay and deduplication
                  if (!window.balanceLoadingInProgress) {
                      window.balanceLoadingInProgress = true;
                      setTimeout(async () => {
                          try {
                              console.log('Loading user balance after authentication delay...');
                              const balanceResponse = await fetch(`/api/user/data-balance?firebaseUid=${user.uid}`);
                              const balanceData = await balanceResponse.json();

                              if (balanceData.status === 'success') {
                                  currentUserData.dataBalance = balanceData.dataBalance || 0;
                                  console.log('Balance loaded successfully:', currentUserData.dataBalance);

                                  // Update UI with new balance
                                  updateBalanceDisplays(currentUserData.dataBalance);

                                  // Update localStorage with new balance
                                  localStorage.setItem('currentUser', JSON.stringify(currentUserData));
                              } else {
                                  console.error('Balance API error:', balanceData);
                                  currentUserData.dataBalance = 0;
                              }
                          } catch (balanceError) {
                              console.error('Error fetching balance after delay:', balanceError);
                              currentUserData.dataBalance = 0;
                          } finally {
                              window.balanceLoadingInProgress = false;
                          }
                      }, 2000); // Wait 2 seconds after authentication before loading balance
                  }

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
          window.balanceLoadingInProgress = false;
          isProcessingAuth = false;
          updateAuthUI(null, null);
      }
      
      // Reset processing flag after successful processing
      if (user) {
          isProcessingAuth = false;
      }
    });

    function updateAuthUI(user, userData) {
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
                    <div class="demo-mode-section" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                        <p style="text-align: center; color: #cccccc; margin-bottom: 10px; font-size: 14px;">
                            Or explore without signing in:
                        </p>
                        <button onclick="enableDemoMode()" class="demo-mode-btn">
                            🎮 Try Demo Mode
                        </button>
                    </div>
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

        // Show success message
        const successMessage = document.createElement('div');
        successMessage.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(81, 207, 102, 0.2);
            border: 1px solid #51cf66;
            color: #51cf66;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-size: 14px;
        `;
        successMessage.textContent = '🎮 Demo Mode Activated! You can now explore the platform.';
        document.body.appendChild(successMessage);

        setTimeout(() => {
            if (document.body.contains(successMessage)) {
                document.body.removeChild(successMessage);
            }
        }, 3000);
    }

    function disableDemoMode() {
        localStorage.removeItem('demoMode');
        updateAuthUI(null, null);

        // Show exit message
        const exitMessage = document.createElement('div');
        exitMessage.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 193, 7, 0.2);
            border: 1px solid #ffc107;
            color: #ffc107;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-size: 14px;
        `;
        exitMessage.textContent = '👋 Demo Mode Deactivated. Sign in to access your account.';
        document.body.appendChild(exitMessage);

        setTimeout(() => {
            if (document.body.contains(exitMessage)) {
                document.body.removeChild(exitMessage);
            }
        }, 3000);
    }

    function showDemoData() {
        const userInfo = document.getElementById('user-info');
        if (userInfo) {
            userInfo.innerHTML = `
                <div class="demo-mode-active" style="text-align: center; padding: 20px;">
                    <h2 style="color: #74c0fc; margin-bottom: 15px;">🎮 Demo Mode Active</h2>
                    <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                        <p style="color: #cccccc; margin: 5px 0;"><strong>Name:</strong> Demo User</p>
                        <p style="color: #cccccc; margin: 5px 0;"><strong>Email:</strong> demo@example.com</p>
                        <p style="color: #cccccc; margin: 5px 0;"><strong>Data Balance:</strong> 5.5 GB</p>
                        <p style="color: #cccccc; margin: 5px 0;"><strong>Status:</strong> Demo Member</p>
                    </div>
                    <button onclick="disableDemoMode()" style="background: rgba(255, 193, 7, 0.2); border: 1px solid #ffc107; color: #ffc107; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                        Exit Demo Mode
                    </button>
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

    // Sign up function
    window.signUp = async function(email, password, displayName, imei) {
        try {
            console.log('Starting Firebase signup process...');

            // Create user with Firebase Auth
            const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
            const user = userCredential.user;

            console.log('Firebase user created:', user.uid);

            // Update user profile with display name
            if (displayName) {
                await user.updateProfile({
                    displayName: displayName
                });
            }

            // Register user in our database
            const registrationData = {
                firebaseUid: user.uid,
                email: user.email,
                displayName: displayName || user.displayName,
                photoURL: user.photoURL
            };

            console.log('Registering user in database:', registrationData);

            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(registrationData)
            });

            const result = await response.json();
            console.log('Database registration result:', result);

            if (result.status === 'success') {
                // Update IMEI if provided
                if (imei) {
                    await updateUserIMEI(user.uid, imei);
                }

                console.log('User successfully registered. User ID:', result.userId);
                console.log('Stripe Customer ID:', result.stripeCustomerId);

                // Verify user was created in all systems
                await verifyUserCreation(user.uid);

                console.log('Redirecting to dashboard...');
                // Use replace to prevent back button issues
                window.location.replace('/dashboard');
                return { success: true, user: user };
            } else {
                throw new Error(result.error || 'Failed to register user in database');
            }

        } catch (error) {
            console.error('Signup error:', error);

            // Show user-friendly error messages
            let errorMessage = 'An error occurred during signup.';

            if (error.code === 'auth/email-already-in-use') {
                errorMessage = 'This email address is already registered. Please try logging in instead.';
                // If user already exists, try to sign them in and redirect
                try {
                    const signInResult = await firebase.auth().signInWithEmailAndPassword(email, password);
                    console.log('User already exists, signed in successfully');
                    window.location.replace('/dashboard');
                    return { success: true, user: signInResult.user };
                } catch (signInError) {
                    console.error('Failed to sign in existing user:', signInError);
                    errorMessage += ' Please try logging in with your existing account.';
                }
            } else if (error.code === 'auth/weak-password') {
                errorMessage = 'Password should be at least 6 characters long.';
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = 'Please enter a valid email address.';
            } else if (error.message) {
                errorMessage = error.message;
            }

            // Display error to user
            const errorDiv = document.getElementById('error-message');
            if (errorDiv) {
                errorDiv.textContent = errorMessage;
                errorDiv.style.display = 'block';
            } else {
                alert(errorMessage);
            }

            return { success: false, error: errorMessage };
        }
    };

    // Function to verify user creation in all systems
    async function verifyUserCreation(firebaseUid) {
        try {
            console.log('Verifying user creation in all systems...');

            // Check user in our database
            const userResponse = await fetch(`/api/auth/current-user?firebaseUid=${firebaseUid}`);
            const userData = await userResponse.json();

            if (userData.status === 'success') {
                console.log('✓ User found in database:', {
                    userId: userData.userId,
                    email: userData.email,
                    stripeCustomerId: userData.stripeCustomerId,
                    oxioUserId: userData.oxioUserId
                });

                // Verify Stripe customer
                if (userData.stripeCustomerId) {
                    console.log('✓ Stripe customer ID recorded:', userData.stripeCustomerId);
                } else {
                    console.log('⚠ Stripe customer ID not found');
                }

                // Verify OXIO user
                if (userData.oxioUserId) {
                    console.log('✓ OXIO user ID recorded:', userData.oxioUserId);
                } else {
                    console.log('⚠ OXIO user ID not found');
                }

                return {
                    database: true,
                    stripe: !!userData.stripeCustomerId,
                    oxio: !!userData.oxioUserId
                };
            } else {
                console.log('✗ User not found in database');
                return { database: false, stripe: false, oxio: false };
            }
        } catch (error) {
            console.error('Error verifying user creation:', error);
            return { database: false, stripe: false, oxio: false };
        }
    }

    async function updateUserIMEI(firebaseUid, imei) {
      try {
          const response = await fetch('/api/auth/update-imei', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  firebaseUid: firebaseUid,
                  imei: imei
              })
          });

          const result = await response.json();
          console.log('Update IMEI result:', result);

          if (result.status === 'success') {
              console.log('IMEI updated successfully.');
              return { success: true };
          } else {
              throw new Error(result.error || 'Failed to update IMEI in database');
          }
      } catch (error) {
          console.error('IMEI update error:', error);
          return { success: false, error: error.message };
      }
    }

    // Make nested functions globally available
    window.enableDemoMode = enableDemoMode;
    window.disableDemoMode = disableDemoMode;
    window.isDemoMode = isDemoMode;
    window.showDemoData = showDemoData;
    window.getCurrentUser = getCurrentUser;
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

    // Make demo functions available even in fallback mode
    window.enableDemoMode = function() {
      localStorage.setItem('demoMode', 'true');
      showDemoData();
    };

    window.disableDemoMode = function() {
      localStorage.removeItem('demoMode');
    };

    window.isDemoMode = function() {
      return localStorage.getItem('demoMode') === 'true';
    };

    window.showDemoData = function() {
      const userInfo = document.getElementById('user-info');
      if (userInfo) {
        userInfo.innerHTML = `
          <div class="demo-mode-active" style="text-align: center; padding: 20px;">
            <h2 style="color: #74c0fc; margin-bottom: 15px;">🎮 Demo Mode Active</h2>
            <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 15px; margin-bottom: 20px;">
              <p style="color: #cccccc; margin: 5px 0;"><strong>Name:</strong> Demo User</p>
              <p style="color: #cccccc; margin: 5px 0;"><strong>Email:</strong> demo@example.com</p>
              <p style="color: #cccccc; margin: 5px 0;"><strong>Data Balance:</strong> 5.5 GB</p>
              <p style="color: #cccccc; margin: 5px 0;"><strong>Status:</strong> Demo Member</p>
            </div>
            <button onclick="disableDemoMode()" style="background: rgba(255, 193, 7, 0.2); border: 1px solid #ffc107; color: #ffc107; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
              Exit Demo Mode
            </button>
          </div>
        `;
      }
    };

    window.getCurrentUser = function() {
      if (localStorage.getItem('demoMode') === 'true') {
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

  // Start the initialization process
  initializeFirebaseAuth();
});
} // Close the conditional block