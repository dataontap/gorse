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
      `;
    }

    if (userInfo) {
      userInfo.innerHTML = `
        <div class="firebase-unavailable" style="text-align: center; padding: 20px;">
          <h2 style="color: #ff6b6b; margin-bottom: 15px;">🔥 Authentication Service Unavailable</h2>
          <p style="color: #cccccc; margin-bottom: 20px;">The authentication service is currently not available. Please:</p>
          <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 15px; margin-bottom: 20px;">
            <ul style="text-align: left; color: #cccccc; margin: 0; padding-left: 20px;">
              <li>Refresh the page to retry the connection</li>
              <li>Check back later when the service is restored</li>
            </ul>
          </div>
        </div>
      `;
    }

    // Set up global auth functions with error handling
    setupFallbackAuthFunctions();
  }

  function setupAuthStateListener() {
    // Check authentication state on page load
    firebase.auth().onAuthStateChanged(async function(user) {
        if (user) {
            console.log('Firebase user detected:', user.email);

            // Check if this is a different user than what's cached
            const cachedUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
            if (cachedUser && cachedUser.uid !== user.uid) {
                console.log('Different user detected, clearing cached data');
                localStorage.clear();
            }

            // Only update UI with basic Firebase data, don't make API calls automatically
            updateAuthUI(user, null);
        } else {
            console.log('No authenticated user');
            // Clear stored user data
            localStorage.removeItem('currentUser');
            updateAuthUI(null, null);
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
                `;
            }

            if (userInfo) {
                userInfo.innerHTML = `
                    <div class="demo-notice">
                        <p>👋 You're not signed in</p>
                        <p>Sign in to access your personal data</p>
                    </div>
                `;
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

    function getCurrentUser() {
        const user = JSON.parse(localStorage.getItem('currentUser') || 'null');
        return user;
    }

    // Function to load user data and balance
    async function loadUserData(user) {
        try {
            console.log('Loading user data for:', user.uid);

            // Register user in our database
            const registrationResponse = await fetch('/api/auth/register', {
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

            const registrationData = await registrationResponse.json();
            console.log('Registration response:', registrationData);

            // Get additional user data from our API
            const userResponse = await fetch(`/api/auth/current-user?firebaseUid=${user.uid}`);
            const userData = await userResponse.json();

            if (userData.status === 'success') {
                console.log('Got user data:', userData);

                // Create comprehensive user data object (without storing Firebase UID)
                const currentUserData = {
                    email: user.email,
                    displayName: user.displayName,
                    photoURL: user.photoURL,
                    userId: userData.userId,
                    stripeCustomerId: userData.stripeCustomerId,
                    founderStatus: userData.founderStatus,
                    oxioUserId: userData.oxioUserId,
                    metamaskAddress: userData.metamaskAddress,
                    oxioGroupId: userData.oxioGroupId,
                    dataBalance: 0 // Will be loaded separately
                };

                // Load data balance after a short delay to ensure user registration is complete
                setTimeout(async () => {
                    try {
                        const balanceResponse = await fetch(`/api/user/data-balance?firebaseUid=${user.uid}`);
                        const balanceData = await balanceResponse.json();

                        if (balanceData.status === 'success') {
                            currentUserData.dataBalance = balanceData.dataBalance;
                            console.log('Data balance loaded:', balanceData.dataBalance, 'GB');

                            // Update localStorage with new balance
                            localStorage.setItem('currentUser', JSON.stringify(currentUserData));
                            updateAuthUI(user, currentUserData); // Update UI with balance
                        } else {
                            console.error('Balance API error:', balanceData);
                            currentUserData.dataBalance = 0;
                            updateAuthUI(user, currentUserData); // Update UI with 0 balance
                        }
                    } catch (balanceError) {
                        console.error('Error fetching balance after delay:', balanceError);
                        currentUserData.dataBalance = 0;
                        updateAuthUI(user, currentUserData); // Update UI with 0 balance
                    }
                }, 2000); // Wait 2 seconds after authentication before loading balance

                console.log('Complete user data loaded:', currentUserData);

                // Store in localStorage
                localStorage.setItem('currentUser', JSON.stringify(currentUserData));

                // Update UI with real user data (without balance initially)
                updateAuthUI(user, currentUserData);

            } else {
                console.error('Failed to get user data:', userData);
                // Fallback to basic Firebase data
                updateAuthUI(user, null);
            }

        } catch (error) {
            console.error('Error loading user data:', error);
            // Fallback to basic Firebase data
            updateAuthUI(user, null);
        }
    }


    // Expose auth functions to global scope
    window.firebaseAuth = {
      signInWithEmailPassword: function(email, password) {
        if (!firebase || !firebase.auth) {
          console.error('Firebase auth not available for email sign-in');
          return Promise.reject(new Error('Authentication service not available'));
        }
        return firebase.auth().signInWithEmailAndPassword(email, password)
            .then(async (userCredential) => {
                const user = userCredential.user;
                console.log('Email/password sign-in successful:', user.email);

                // Load user data after successful login
                await loadUserData(user);

                // FCM token will be handled after user data is loaded
                registerFCMToken();

                // Force reload of profile page if we're on it
                if (window.location.pathname === '/profile') {
                    setTimeout(() => {
                        if (typeof loadFirebaseUserData === 'function') {
                            loadFirebaseUserData();
                        }
                    }, 1000);
                }

                return userCredential;
            })
            .catch((error) => {
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
            .then(async (result) => {
                const user = result.user;
                console.log('Google sign-in successful:', user.email);

                // Load user data after successful login
                await loadUserData(user);

                // FCM token will be handled after user data is loaded
                registerFCMToken();

                // Force reload of profile page if we're on it
                if (window.location.pathname === '/profile') {
                    setTimeout(() => {
                        if (typeof loadFirebaseUserData === 'function') {
                            loadFirebaseUserData();
                        }
                    }, 1000);
                }

                return result;
            })
            .catch((error) => {
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
        console.log('Starting Firebase sign out process...');

        // Clear all local storage completely
        localStorage.clear();
        sessionStorage.clear();

        if (!firebase || !firebase.auth) {
          console.error('Firebase auth not available during signout');
          window.location.href = '/';
          return Promise.resolve();
        }

        return firebase.auth().signOut()
          .then(() => {
            console.log('Firebase signOut completed successfully');

            // Force clear any remaining Firebase state
            if (firebase.auth().currentUser) {
              console.warn('User still exists after signOut, forcing reload');
            }

            // Small delay to ensure Firebase state is cleared
            setTimeout(() => {
              window.location.href = '/';
            }, 100);
          })
          .catch((error) => {
            console.error('Error during Firebase sign out:', error);
            // Force redirect even if signOut fails
            setTimeout(() => {
              window.location.href = '/';
            }, 100);
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

            // First sign out any existing user to prevent caching issues
            if (firebase.auth().currentUser) {
                console.log('Signing out existing user before signup');
                await firebase.auth().signOut();
                // Clear local storage to prevent cached user data
                localStorage.clear();
            }

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
    window.getCurrentUser = getCurrentUser;
    window.loadUserData = loadUserData; // Expose loadUserData
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

    window.getCurrentUser = function() {
      return null;
    };
  }

  // Send token to your server with deduplication
  function sendTokenToServer(token) {
    // Check if this token was already registered in this session
    const lastRegisteredToken = sessionStorage.getItem('lastRegisteredFCMToken');
    if (lastRegisteredToken === token) {
      console.log('FCM token already registered in this session, skipping duplicate registration');
      return;
    }

    // Get current user's Firebase UID if available
    let firebaseUid = null;
    let userEmail = null;
    if (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser) {
      firebaseUid = firebase.auth().currentUser.uid;
      userEmail = firebase.auth().currentUser.email;
      console.log('FCM token registration for authenticated user:', userEmail);
    } else {
      console.log('FCM token registration for unauthenticated session');
    }

    fetch('/api/register-fcm-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: token,
        firebaseUid: firebaseUid
      }),
    })
    .then(response => response.json())
    .then(data => {
      console.log('FCM token registered successfully:', {
        success: data.success || data.status,
        userEmail: userEmail,
        tokenPrefix: token.substring(0, 20) + '...'
      });
      // Store the token to prevent duplicate registrations
      sessionStorage.setItem('lastRegisteredFCMToken', token);
    })
    .catch((error) => {
      console.error('Error registering FCM token:', error);
    });
  }

  // Function to register FCM token, called after user is loaded
  function registerFCMToken() {
    if (typeof firebase === 'undefined' || !firebase.messaging) {
      console.log("Firebase Messaging not available, skipping token registration.");
      return;
    }

    // Check if FCM token registration is already in progress
    if (window.fcmRegistrationInProgress) {
      console.log('FCM token registration already in progress, skipping duplicate call');
      return;
    }

    window.fcmRegistrationInProgress = true;

    // Request permission for notifications
    firebase.messaging().requestPermission().then((permission) => {
      console.log('Notification permission granted:', permission);

      // Get the FCM token
      return firebase.messaging().getToken();
    }).then((currentToken) => {
      if (currentToken) {
        console.log('FCM Token:', currentToken);
        // Send the token to the server
        sendTokenToServer(currentToken);
      } else {
        console.log('No FCM token found. Request permission to receive notifications.');
      }
    }).catch((err) => {
      console.error('Unable to get permission to notify, or token:', err);
    }).finally(() => {
      // Reset the flag after completion
      window.fcmRegistrationInProgress = false;
    });
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