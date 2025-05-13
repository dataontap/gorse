
// Initialize Firebase for web
document.addEventListener('DOMContentLoaded', function() {
  // Firebase configuration
  const firebaseConfig = {
    apiKey: "AIzaSyAb1pMMVxPvRDIKE_kHU7vFLzW_3Iy2G0Y", 
    authDomain: "gorse-24e76.firebaseapp.com",
    projectId: "gorse-24e76",
    storageBucket: "gorse-24e76.appspot.com",
    messagingSenderId: "212829848250",
    appId: "1:212829848250:web:0a20a7c404c23da87e3883"
  };

  // Initialize Firebase
  firebase.initializeApp(firebaseConfig);

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
                  showNotificationStatus('Firebase installation failed. Please check your Firebase configuration.');
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
      });
      
    // Handle foreground messages
    messaging.onMessage((payload) => {
      console.log('Message received in foreground: ', payload);
      // Create notification for foreground message
      const notification = new Notification(payload.notification.title, {
        body: payload.notification.body,
        icon: '/static/images/notification-icon.png'
      });
    });
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
