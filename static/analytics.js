/**
 * Simplified Google Analytics helper functions for Job Tracker
 * Basic implementation with minimal dependencies
 */

// Simple check if Google Analytics is available
function isGaReady() {
    return typeof gtag === 'function';
}

// Basic event tracking function
function trackEvent(category, action, label) {
    try {
        if (isGaReady()) {
            gtag('event', action, {
                'event_category': category,
                'event_label': label
            });
            return true;
        }
    } catch (error) {
        console.error('Error tracking event:', error);
    }
    return false;
}

// Basic page view tracking
function trackPageView(pageName) {
    try {
        if (isGaReady()) {
            gtag('event', 'page_view', {
                'page_title': pageName || document.title,
                'page_location': window.location.href
            });
            return true;
        }
    } catch (error) {
        console.error('Error tracking page view:', error);
    }
    return false;
}

// Basic job application tracking
function trackJobApply(jobId, company, title) {
    return trackEvent('Job', 'apply', `${company} - ${title}`);
}

// Basic search tracking
function trackSearch(searchTerm, resultCount) {
    return trackEvent('Search', 'search', searchTerm);
}

// Basic filter tracking
function trackFilter(filterType, filterValue) {
    return trackEvent('Filter', 'use', `${filterType}: ${filterValue}`);
}

// Basic login tracking
function trackLogin(method, success) {
    return trackEvent('User', 'login', method);
}

// Make functions globally available
window.trackPageView = trackPageView;
window.trackEvent = trackEvent;
window.trackJobApply = trackJobApply;
window.trackSearch = trackSearch;
window.trackFilter = trackFilter;
window.trackLogin = trackLogin;
