
// Firebase Cloud Messaging Service Worker

importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker
firebase.initializeApp({
  apiKey: "AIzaSyA1dLC68va6gRSyCA4kDQqH1ZWjFkyLivY",
  authDomain: "gorse-24e76.firebaseapp.com",
  projectId: "gorse-24e76",
  storageBucket: "gorse-24e76.firebasestorage.app",
  messagingSenderId: "212829848250",
  appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
  measurementId: "G-WHW3XT925P"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  
  const notificationTitle = payload.notification?.title || 'New Notification';
  const notificationOptions = {
    body: payload.notification?.body || 'You have a new notification',
    icon: '/static/tropical-border.png',  // Use an existing image
    badge: '/static/tropical-border.png',
    data: payload.data || {},
    requireInteraction: true,  // Keep notification until user interacts with it
    actions: [
      {
        action: 'view',
        title: 'View'
      }
    ]
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Notification click received.');
  
  event.notification.close();
  
  // Open a new window/tab or focus on existing one
  event.waitUntil(
    clients.matchAll({type: 'window', includeUncontrolled: true})
      .then(clientList => {
        if (clientList.length > 0) {
          return clientList[0].focus();
        }
        return clients.openWindow('/dashboard');
      })
  );
});
