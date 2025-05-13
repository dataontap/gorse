
// Initialize Firebase for web
document.addEventListener('DOMContentLoaded', function() {
  // Firebase configuration
  const firebaseConfig = {
    apiKey: "AIzaSyAb1pMMVxPvRDIKE_kHU7vFLzW_3Iy2G0Y", // Use your actual Firebase API key here
    authDomain: "gorse-24e76.firebaseapp.com",
    projectId: "gorse-24e76",
    storageBucket: "gorse-24e76.firebasestorage.app",
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
        
        // Request permission and get token
        messaging.getToken({ vapidKey: 'BL-eBEYO9fXmsdQy9xKHrq6p2a_MuKQB4-WSnFYUbh-dCuOPOFLFouTYwF9stPGAA3_N9KQcRWzQz8F4mZFE9Kw' })
          .then((currentToken) => {
            if (currentToken) {
              console.log('FCM token:', currentToken);
              // Send token to server for targeting this device
              sendTokenToServer(currentToken);
            } else {
              console.log('No registration token available. Request permission to generate one.');
            }
          })
          .catch((err) => {
            console.log('An error occurred while retrieving token. ', err);
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
