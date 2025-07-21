
// Firebase service worker for background messaging
self.importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
self.importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');

// Default Firebase configuration (API key will be set via message)
let firebaseConfig = {
  apiKey: "your-api-key-here",
  authDomain: "gorse-24e76.firebaseapp.com",
  projectId: "gorse-24e76",
  storageBucket: "gorse-24e76.appspot.com",
  messagingSenderId: "212829848250",
  appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
  measurementId: "G-WHW3XT925P"
};

// Listen for configuration messages
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'FIREBASE_CONFIG') {
    firebaseConfig.apiKey = event.data.apiKey;
    // Re-initialize Firebase with the correct API key
    if (!firebase.apps.length) {
      firebase.initializeApp(firebaseConfig);
    }
  }
});

// Initialize Firebase in service worker (will be re-initialized with correct key)
if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

// Retrieve an instance of Firebase Messaging so that it can handle background messages
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);

  // Customize notification here
  const notificationTitle = payload.notification?.title || 'GORSE Network';
  const notificationOptions = {
    body: payload.notification?.body || 'You have a new notification',
    icon: '/static/tropical-border.png',
    badge: '/static/tropical-border.png',
    data: payload.data || {},
    requireInteraction: false,
    silent: false
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click events
self.addEventListener('notificationclick', function(event) {
  console.log('[firebase-messaging-sw.js] Notification click received.');

  event.notification.close();

  // This looks to see if the current is already open and focuses if it is
  event.waitUntil(
    clients.matchAll({
      type: 'window'
    }).then(function(clientList) {
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});
