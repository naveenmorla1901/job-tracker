/**
 * Google Analytics helper functions for Job Tracker
 * This file provides functions to track events and page views in the Job Tracker application
 */

// Track page view
function trackPageView(pageName) {
    if (typeof gtag === 'function') {
        gtag('event', 'page_view', {
            'page_title': pageName,
            'page_path': window.location.pathname + window.location.search
        });
    }
}

// Track user actions
function trackEvent(category, action, label, value) {
    if (typeof gtag === 'function') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label,
            'value': value
        });
    }
}

// Track job application clicks
function trackJobApply(jobId, company, title) {
    if (typeof gtag === 'function') {
        gtag('event', 'job_apply_click', {
            'event_category': 'Job Interaction',
            'event_label': `${company} - ${title}`,
            'job_id': jobId
        });
    }
}

// Track searches
function trackSearch(searchTerm, resultCount) {
    if (typeof gtag === 'function') {
        gtag('event', 'search', {
            'search_term': searchTerm,
            'result_count': resultCount
        });
    }
}

// Track filter usage
function trackFilter(filterType, filterValue) {
    if (typeof gtag === 'function') {
        gtag('event', 'filter_used', {
            'event_category': 'Filter',
            'event_label': `${filterType}: ${filterValue}`
        });
    }
}

// Track user login
function trackLogin(method) {
    if (typeof gtag === 'function') {
        gtag('event', 'login', {
            'method': method
        });
    }
}

// Track feature usage
function trackFeatureUsage(featureName) {
    if (typeof gtag === 'function') {
        gtag('event', 'feature_used', {
            'event_category': 'Feature',
            'event_label': featureName
        });
    }
}

// Automatically detect page changes in Streamlit
function setupStreamlitPageTracking() {
    // First page view
    trackPageView(document.title);
    
    // Monitor for page changes
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.type === 'childList' && mutation.addedNodes.length) {
                // This is an approximation - Streamlit doesn't have traditional page navigation
                setTimeout(() => {
                    // Use the current title as the page name
                    trackPageView(document.title);
                }, 300);
                break;
            }
        }
    });
    
    // Start observing the main content area
    setTimeout(() => {
        const mainContent = document.querySelector('.main');
        if (mainContent) {
            observer.observe(mainContent, { childList: true, subtree: true });
            console.log('Analytics page tracking initialized');
        }
    }, 1000);
}

// Initialize when the page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupStreamlitPageTracking);
} else {
    setupStreamlitPageTracking();
}
