
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
    requireInteraction: false,  // Allow auto-dismiss
    silent: false,
    actions: [
      {
        action: 'view',
        title: 'View'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ],
    // Auto-dismiss after 10 seconds if not interacted with
    tag: 'dismissible-notification'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Notification click received.', event.action);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    // Just close the notification, no further action
    return;
  }
  
  if (event.action === 'view' || !event.action) {
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
  }
});

// Auto-dismiss notifications after 10 seconds
self.addEventListener('notificationshow', event => {
  setTimeout(() => {
    self.registration.getNotifications({ tag: 'dismissible-notification' })
      .then(notifications => {
        notifications.forEach(notification => {
          notification.close();
        });
      });
  }, 10000); // 10 seconds
});
