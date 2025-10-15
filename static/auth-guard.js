// Authentication Guard - Redirects unauthenticated users to login
// This script should be loaded AFTER firebase-init.js and firebase-auth.js

(function() {
    'use strict';
    
    // List of pages that don't require authentication
    const publicPages = ['/', '/login', '/signup', '/privacy', '/terms', '/about'];
    
    // Check if current page requires authentication
    const currentPath = window.location.pathname;
    const isPublicPage = publicPages.includes(currentPath);
    
    if (isPublicPage) {
        // Public page, no auth required
        return;
    }
    
    // Protected page - check authentication
    function checkAuth() {
        if (typeof firebase === 'undefined' || !firebase.auth) {
            console.error('Firebase not initialized');
            redirectToLogin();
            return;
        }
        
        // Check current user
        const currentUser = firebase.auth().currentUser;
        
        if (!currentUser) {
            console.log('No authenticated user found, redirecting to login...');
            redirectToLogin();
        } else {
            console.log('User authenticated:', currentUser.uid);
        }
    }
    
    function redirectToLogin() {
        // Store the intended destination
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = '/login';
    }
    
    // Wait for Firebase to initialize, then check auth
    if (typeof firebase !== 'undefined' && firebase.auth) {
        // Firebase already loaded
        firebase.auth().onAuthStateChanged(function(user) {
            if (!user) {
                redirectToLogin();
            }
        });
    } else {
        // Wait for Firebase to load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(checkAuth, 500); // Give Firebase time to initialize
        });
    }
})();
