
// Firebase Cloud Messaging Service Worker

importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

firebase.initializeApp({
  apiKey: "AIzaSyAb1pMMVxPvRDIKE_kHU7vFLzW_3Iy2G0Y",
  authDomain: "gorse-24e76.firebaseapp.com",
  projectId: "gorse-24e76",
  storageBucket: "gorse-24e76.appspot.com",
  messagingSenderId: "212829848250",
  appId: "1:212829848250:web:0a20a7c404c23da87e3883"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/static/images/notification-icon.png'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
