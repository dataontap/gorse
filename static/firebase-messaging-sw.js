// Firebase v9+ modular SDK for service worker
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');

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

// Initialize Firebase in service worker
firebase.initializeApp(firebaseConfig);

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

  // Navigate to notifications page when notification is clicked
  event.waitUntil(
    clients.matchAll({
      type: 'window'
    }).then(function(clientList) {
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url.includes(self.registration.scope) && 'focus' in client) {
          return client.focus().then(() => {
            return client.navigate('/notifications');
          });
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/notifications');
      }
    })
  );
});