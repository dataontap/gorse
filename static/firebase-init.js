// Initialize Firebase for web
document.addEventListener('DOMContentLoaded', function() {
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

  try {
    // Initialize Firebase
    if (!firebase.apps.length) {
      firebase.initializeApp(firebaseConfig);
    }

    // Initialize Firebase Cloud Messaging
    if ('serviceWorker' in navigator && firebase.messaging.isSupported()) {
      const messaging = firebase.messaging();

      // Register service worker
      navigator.serviceWorker.register('/static/firebase-messaging-sw.js')
        .then((registration) => {
          messaging.useServiceWorker(registration);

          // First explicitly request notification permission
          Notification.requestPermission().then((permission) => {
            console.log('Notification permission status:', permission);

            if (permission === 'granted') {
              // Now get the token after permission is granted
              messaging.getToken()
                .then((currentToken) => {
                  if (currentToken) {
                    console.log('FCM token:', currentToken);
                    // Send token to server for targeting this device
                    sendTokenToServer(currentToken);
                    // Show success message to user
                    showNotificationStatus('Notifications enabled successfully!');
                  } else {
                    console.log('No registration token available. Request permission to generate one.');
                    showNotificationStatus('Failed to get notification token. Please try again.');
                  }
                })
                .catch((err) => {
                  console.log('An error occurred while retrieving token. ', err);
                  console.log('Error details:', JSON.stringify(err));
                  showNotificationStatus('Error setting up notifications: ' + err.message);

                  // Special handling for common errors
                  if (err.code === 'messaging/permission-blocked') {
                    showNotificationStatus('Notification permission blocked. Please reset permissions in your browser settings.');
                  } else if (err.code === 'installations/request-failed') {
                    showNotificationStatus('Firebase installation failed. Please verify your Firebase project settings in Firebase Console.');
                  }
                });
            } else {
              console.log('Permission denied for notifications');
              showNotificationStatus('Notification permission denied. Please enable notifications in your browser settings and reload the page.');
            }
          });
        })
        .catch((err) => {
          console.log('Service worker registration failed: ', err);
          showNotificationStatus('Error registering service worker: ' + err.message);
        });

      // Handle foreground messages
      messaging.onMessage((payload) => {
        console.log('Message received in foreground: ', payload);

        // Create and show notification for foreground message
        if (Notification.permission === 'granted') {
          // Try to use the notification from the payload if available
          const notificationTitle = payload.notification?.title || 'New Notification';
          const notificationOptions = {
            body: payload.notification?.body || 'You have a new notification',
            icon: '/static/tropical-border.png', // Use an existing image
            data: payload.data,
            requireInteraction: true // Keep notification until user interacts with it
          };

          // Create and show the notification
          const notification = new Notification(notificationTitle, notificationOptions);

          // Handle notification click
          notification.onclick = function() {
            console.log('Notification clicked');
            window.focus();
            notification.close();
          };

          // Also show an in-app notification
          showInAppNotification(notificationTitle, notificationOptions.body);
        }
      });
    } else {
      console.log('Firebase messaging not supported in this browser');
      showNotificationStatus('Push notifications are not supported in this browser.');
    }
  } catch (error) {
    console.error('Firebase initialization error:', error);
    showNotificationStatus('Firebase initialization failed: ' + error.message);
  }
});

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
    statusElement.style.bottom = '20px';
    statusElement.style.right = '20px';
    statusElement.style.padding = '10px 15px';
    statusElement.style.backgroundColor = '#f0f8ff';
    statusElement.style.border = '1px solid #ccc';
    statusElement.style.borderRadius = '4px';
    statusElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    statusElement.style.zIndex = '1000';
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