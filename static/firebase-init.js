// Prevent duplicate Firebase initialization
if (window.firebaseInitLoaded) {
  console.log("Firebase init script already loaded, skipping...");
} else {
window.firebaseInitLoaded = true;

document.addEventListener('DOMContentLoaded', async function() {
  // Single Firebase configuration
  const firebaseConfig = {
    apiKey: window.CURRENT_KEY || "AIzaSyA1dLC68va6gRSyCA4kDQqH1ZWjFkyLivY",
    authDomain: "gorse-24e76.firebaseapp.com",
    projectId: "gorse-24e76",
    storageBucket: "gorse-24e76.appspot.com",
    messagingSenderId: "212829848250",
    appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
    measurementId: "G-WHW3XT925P"
  };

  // Initialize Firebase only once globally
  if (typeof firebase !== 'undefined' && !window.firebaseInitialized) {
    try {
      // Check if Firebase is already initialized
      if (firebase.apps.length === 0) {
        const app = firebase.initializeApp(firebaseConfig);
        console.log("Firebase initialized successfully");
        window.firebaseInitialized = true;
      } else {
        console.log("Firebase already initialized, using existing app");
        window.firebaseInitialized = true;
      }
      const auth = firebase.auth();
    } catch (error) {
      if (error.code === 'app/duplicate-app') {
        console.log("Firebase app already exists, using existing instance");
        window.firebaseInitialized = true;
      } else {
        console.error("Firebase initialization error:", error);
      }
    }
  } else if (!firebase) {
    console.error("Firebase SDK not loaded");
  }

  try {
    // Initialize Firebase Cloud Messaging only if supported
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      // Dynamically import Firebase modules
      const { initializeApp } = await import('https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js');
      const { getMessaging, getToken, onMessage } = await import('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging.js');

      // Initialize Firebase
      const app = initializeApp(firebaseConfig);
      const messaging = getMessaging(app);

      // Register service worker and wait for it to be ready
      const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js', {
        scope: '/'
      });

      console.log('Service worker registered successfully');

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;

      // Request notification permission
      const permission = await Notification.requestPermission();
      console.log('Notification permission status:', permission);

      if (permission === 'granted') {
        // Get FCM token with service worker registration
        const currentToken = await getToken(messaging, {
          serviceWorkerRegistration: registration
        });

        if (currentToken) {
          console.log('FCM token:', currentToken);
          // Send token to server for targeting this device
          registerFCMToken(currentToken);
          // Show success message to user
          showNotificationStatus('Notifications enabled successfully!');
        } else {
          console.log('No registration token available. Request permission to generate one.');
          showNotificationStatus('Failed to get notification token. Please try again.');
        }
      } else {
        throw new Error('Notification permission denied');
      }
        // Handle foreground messages
      onMessage(messaging, (payload) => {
        console.log('Message received in foreground: ', payload);

        // Show a custom dismissible notification for foreground messages
        if (Notification.permission === 'granted') {
          const notificationTitle = payload.notification?.title || 'New Notification';
          const notificationOptions = {
            body: payload.notification?.body || 'You have a new notification',
            icon: '/static/tropical-border.png',
            badge: '/static/tropical-border.png',
            requireInteraction: false,
            silent: false,
            tag: 'foreground-notification',
            data: payload.data || {}
          };

          const notification = new Notification(notificationTitle, notificationOptions);

          // Auto-dismiss after 8 seconds
          setTimeout(() => {
            notification.close();
          }, 8000);

          // Handle click to focus window
          notification.onclick = function() {
            window.focus();
            this.close();
          };
        }

        // Also show an in-app notification
        const title = payload.notification?.title || 'New Notification';
        const body = payload.notification?.body || 'You have a new notification';
        showInAppNotification(title, body);
      });

    } else {
      console.log('Firebase messaging not supported in this browser');
      showNotificationStatus('Push notifications are not supported in this browser.');
    }
  } catch (err) {
    console.log('Error in Firebase messaging setup: ', err);
    console.log('Error details:', JSON.stringify(err));

    // Special handling for common errors
    if (err.message === 'Notification permission denied') {
      showNotificationStatus('Notification permission denied. Please enable notifications in your browser settings and reload the page.');
    } else if (err.code === 'messaging/permission-blocked') {
      showNotificationStatus('Notification permission blocked. Please reset permissions in your browser settings.');
    } else if (err.code === 'installations/request-failed') {
      showNotificationStatus('Firebase installation failed. Please verify your Firebase project settings in Firebase Console.');
    } else if (err.code === 'messaging/use-sw-after-get-token') {
      showNotificationStatus('Service worker setup error. Please refresh the page.');
    } else if (err.message && err.message.includes('no active Service Worker')) {
      showNotificationStatus('Service worker registration failed. Please refresh the page and try again.');
    } else {
      showNotificationStatus('Error setting up notifications: ' + err.message);
    }
  } finally {
      // Mark initialization as complete
      window.firebaseInitializing = false;
    }
});
} // Close Firebase init conditional

// Register FCM token with server (with deduplication)
async function registerFCMToken(token) {
    // Prevent duplicate registrations of the same token
    if (window.lastRegisteredToken === token || window.fcmTokenRegistering) {
        console.log('Token already registered or registration in progress, skipping...');
        return;
    }

    window.fcmTokenRegistering = true;

    // Add timestamp to prevent rapid duplicate calls
    const now = Date.now();
    if (window.lastTokenRequest && (now - window.lastTokenRequest) < 5000) {
        console.log('Token request too soon after previous request, skipping...');
        window.fcmTokenRegistering = false;
        return;
    }
    window.lastTokenRequest = now;

    try {
        const response = await fetch('/api/register-fcm-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: token
            })
        });

        const result = await response.json();
        console.log('Token registered with server:', result);

        // Store the registered token to prevent duplicates
        window.lastRegisteredToken = token;
    } catch (error) {
        console.error('Error registering token with server:', error);
    } finally {
        window.fcmTokenRegistering = false;
    }
}

// Send token to your server
function sendTokenToServer(token) {
  fetch('/api/register-fcm-token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token: token }),
  })
  .then(response => response.json())
  .then(data => {
    console.log('Token registered with server:', data);
  })
  .catch((error) => {
    console.error('Error registering token:', error);
  });
}

// Function to display notification status to the user
function showNotificationStatus(message) {
  // Look for notification status element
  let statusElement = document.getElementById('notification-status');

  // If we don't have a status element in the notification tester, create a floating one
  if (!statusElement) {
    statusElement = document.createElement('div');
    statusElement.id = 'notification-status-floating';
    statusElement.style.position = 'fixed';
    statusElement.style.top = '20px';
    statusElement.style.left = '50%';
    statusElement.style.transform = 'translateX(-50%)';
    statusElement.style.padding = '12px 20px';
    statusElement.style.backgroundColor = '#2c3e50';
    statusElement.style.color = '#ffffff';
    statusElement.style.border = '2px solid #3498db';
    statusElement.style.borderRadius = '8px';
    statusElement.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
    statusElement.style.zIndex = '10000';
    statusElement.style.fontSize = '14px';
    statusElement.style.fontWeight = '500';
    statusElement.style.maxWidth = '90vw';
    statusElement.style.textAlign = 'center';
    document.body.appendChild(statusElement);

    // Auto remove after 8 seconds
    setTimeout(() => {
      if (document.body.contains(statusElement)) {
        document.body.removeChild(statusElement);
      }
    }, 8000);
  }

  statusElement.textContent = message;
}

// Function to display in-app notification
function showInAppNotification(title, message) {
  // Create notification element
  const notificationElement = document.createElement('div');
  notificationElement.style.position = 'fixed';
  notificationElement.style.top = '20px';
  notificationElement.style.right = '20px';
  notificationElement.style.left = '20px';
  notificationElement.style.maxWidth = '600px';
  notificationElement.style.margin = '0 auto';
  notificationElement.style.padding = '15px';
  notificationElement.style.backgroundColor = '#2c3e50';
  notificationElement.style.color = '#ffffff';
  notificationElement.style.border = '2px solid #3498db';
  notificationElement.style.borderRadius = '8px';
  notificationElement.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
  notificationElement.style.zIndex = '10000';
  notificationElement.style.transform = 'translateY(-100%)';
  notificationElement.style.transition = 'transform 0.3s ease';
  notificationElement.innerHTML = `
    <div class="notification-header">
      <strong style="color: #ffffff; font-size: 16px;">${title}</strong>
      <span class="close-notification" style="color: #ffffff; font-size: 20px; font-weight: bold;">&times;</span>
    </div>
    <div style="margin-top: 8px; color: #ecf0f1; line-height: 1.4; font-size: 14px;">${message}</div>
  `;

  // Style the header
  const header = notificationElement.querySelector('.notification-header');
  header.style.display = 'flex';
  header.style.justifyContent = 'space-between';
  header.style.marginBottom = '10px';

  // Style the close button
  const closeBtn = notificationElement.querySelector('.close-notification');
  closeBtn.style.cursor = 'pointer';
  closeBtn.style.fontSize = '20px';
  closeBtn.style.fontWeight = 'bold';

  // Add the notification to the page
  document.body.appendChild(notificationElement);

  // Trigger animation
  setTimeout(() => {
    notificationElement.style.transform = 'translateY(0)';
  }, 100);

  // Add click handler for close button
  closeBtn.addEventListener('click', () => {
    notificationElement.style.transform = 'translateY(-100%)';
    setTimeout(() => {
      if (document.body.contains(notificationElement)) {
        document.body.removeChild(notificationElement);
      }
    }, 300);
  });

  // Auto-remove after 8 seconds
  setTimeout(() => {
    if (document.body.contains(notificationElement)) {
      notificationElement.style.transform = 'translateY(-100%)';
      setTimeout(() => {
        if (document.body.contains(notificationElement)) {
          document.body.removeChild(notificationElement);
        }
      }, 300);
    }
  }, 8000);
}