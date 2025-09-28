document.addEventListener('DOMContentLoaded', async function() {
  // Firebase configuration - using global Firebase object
  const firebaseConfig = {
    apiKey: window.CURRENT_KEY || "AIzaSyA1dLC68va6gRSyCA4kDQqH1ZWjFkyLivY",
    authDomain: "gorse-24e76.firebaseapp.com",
    projectId: "gorse-24e76",
    storageBucket: "gorse-24e76.appspot.com",
    messagingSenderId: "212829848250",
    appId: "1:212829848250:web:e1e7c3b584e4bb537e3883",
    measurementId: "G-WHW3XT925P"
  };

  // Initialize Firebase (only if not already initialized)
  if (typeof firebase !== 'undefined') {
    try {
      if (!firebase.apps.length) {
        const app = firebase.initializeApp(firebaseConfig);
        console.log("Firebase App initialized successfully");
      } else {
        console.log("Firebase App already initialized, skipping duplicate initialization");
      }
    } catch (error) {
      console.error("Firebase initialization error:", error);
    }
  } else {
    console.error("Firebase SDK not loaded");
  }

  try {
    // Initialize Firebase Cloud Messaging only if supported
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      // Dynamically import Firebase modules
      const { initializeApp } = await import('https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js');
      const { getMessaging, getToken, onMessage } = await import('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging.js');

      // Use existing Firebase app or initialize new one
      let app;
      if (firebase.apps && firebase.apps.length > 0) {
        app = firebase.apps[0]; // Use existing Firebase v8 app
      } else {
        app = initializeApp(firebaseConfig); // Initialize new v9 app for messaging
      }
      const messaging = getMessaging(app);

      // Register service worker and wait for it to be ready
      const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js', {
        scope: '/'
      });

      console.log('Service worker registered successfully');

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;
      
      console.log('Firebase messaging service worker ready. Notification permissions will be requested after user authentication.');
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
    if (err.code === 'installations/request-failed') {
      console.log('Firebase installation failed. Please verify your Firebase project settings in Firebase Console.');
    } else if (err.code === 'messaging/use-sw-after-get-token') {
      console.log('Service worker setup error. Please refresh the page.');
    } else if (err.message && err.message.includes('no active Service Worker')) {
      console.log('Service worker registration failed. Please refresh the page and try again.');
    } else {
      console.log('Error setting up Firebase messaging: ' + err.message);
    }
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