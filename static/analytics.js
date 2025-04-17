/**
 * Enhanced Google Analytics helper functions for Job Tracker
 * This file provides functions to track events and page views in the Job Tracker application
 * Optimized for Google Analytics 4 with debug capabilities and error handling
 */

// Check if Google Analytics is loaded and ready
function isGaReady() {
    return typeof gtag === 'function';
}

// Safely execute Google Analytics calls with error handling
function safeGtag(command, action, params) {
    try {
        if (isGaReady()) {
            gtag(command, action, params);
            return true;
        } else {
            console.warn('Google Analytics not loaded yet. Command queued for later execution.');
            // Queue commands to be executed when GA loads
            window.gtagQueue = window.gtagQueue || [];
            window.gtagQueue.push([command, action, params]);
            return false;
        }
    } catch (error) {
        console.error('Error executing Google Analytics command:', error);
        return false;
    }
}

// Process queued commands when GA becomes available
function processGtagQueue() {
    if (!window.gtagQueue || !isGaReady()) return;
    
    console.log(`Processing ${window.gtagQueue.length} queued GA commands`);
    
    while (window.gtagQueue.length > 0) {
        const [command, action, params] = window.gtagQueue.shift();
        gtag(command, action, params);
    }
}

// Enhanced track page view with error handling and additional params
function trackPageView(pageName, additionalParams = {}) {
    const params = {
        'page_title': pageName || document.title,
        'page_location': window.location.href,
        'page_path': window.location.pathname + window.location.search,
        'send_to': 'G-EGVJQG5M34',
        ...additionalParams
    };
    
    const success = safeGtag('event', 'page_view', params);
    if (success && window.debugAnalytics) {
        console.log('Page view tracked:', params);
    }
    return success;
}

// Enhanced track user actions with error handling
function trackEvent(category, action, label, value, additionalParams = {}) {
    const params = {
        'event_category': category,
        'event_label': label,
        'value': value,
        'send_to': 'G-EGVJQG5M34',
        ...additionalParams
    };
    
    const success = safeGtag('event', action, params);
    if (success && window.debugAnalytics) {
        console.log(`Event tracked: ${action}`, params);
    }
    return success;
}

// Track job application clicks with enhanced parameters
function trackJobApply(jobId, company, title, method = 'click', additionalParams = {}) {
    return trackEvent(
        'Job Interaction', 
        'job_apply', 
        `${company} - ${title}`, 
        null, 
        {
            'job_id': jobId,
            'application_method': method,
            'interaction_type': 'application',
            ...additionalParams
        }
    );
}

// Enhanced search tracking
function trackSearch(searchTerm, resultCount, filterApplied = false, additionalParams = {}) {
    return trackEvent(
        'Search', 
        'search', 
        searchTerm, 
        resultCount, 
        {
            'search_term': searchTerm,
            'result_count': resultCount,
            'filters_applied': filterApplied,
            ...additionalParams
        }
    );
}

// Enhanced filter usage tracking
function trackFilter(filterType, filterValue, additionalParams = {}) {
    return trackEvent(
        'Filter', 
        'filter_used', 
        `${filterType}: ${filterValue}`, 
        null, 
        {
            'filter_type': filterType,
            'filter_value': filterValue,
            ...additionalParams
        }
    );
}

// Enhanced user login tracking
function trackLogin(method, success = true, additionalParams = {}) {
    return trackEvent(
        'User', 
        'login', 
        method, 
        null, 
        {
            'method': method,
            'success': success,
            ...additionalParams
        }
    );
}

// Enhanced feature usage tracking
function trackFeatureUsage(featureName, additionalParams = {}) {
    return trackEvent(
        'Feature', 
        'feature_used', 
        featureName, 
        null,
        additionalParams
    );
}

// Enhanced automatic page change detection for Streamlit
function setupStreamlitPageTracking(options = {}) {
    const config = {
        debounceTime: 300,  // ms to wait before registering a page change
        observeAttributes: false,
        debug: false,
        ...options
    };
    
    window.debugAnalytics = config.debug;
    
    // Check for queued commands and process them
    if (isGaReady()) {
        processGtagQueue();
    } else {
        // Set up a watcher to check when GA becomes available
        const gaCheckInterval = setInterval(() => {
            if (isGaReady()) {
                clearInterval(gaCheckInterval);
                processGtagQueue();
                console.log('Google Analytics now available, processed queued commands');
            }
        }, 500);
    }
    
    // Track initial page view
    trackPageView(document.title);
    
    // Debounced page change handler
    let pageChangeTimer;
    const handlePageChange = () => {
        clearTimeout(pageChangeTimer);
        pageChangeTimer = setTimeout(() => {
            trackPageView(document.title);
        }, config.debounceTime);
    };
    
    // Monitor for Streamlit page changes using MutationObserver
    const observer = new MutationObserver((mutations) => {
        let shouldTrack = false;
        
        for (const mutation of mutations) {
            // Check for new nodes that might indicate a page change
            if (mutation.type === 'childList' && mutation.addedNodes.length) {
                shouldTrack = true;
                break;
            }
            
            // Optionally check for attribute changes
            if (config.observeAttributes && mutation.type === 'attributes') {
                shouldTrack = true;
                break;
            }
        }
        
        if (shouldTrack) {
            handlePageChange();
        }
    });
    
    // Start observing the main content area once Streamlit is fully loaded
    setTimeout(() => {
        const mainContent = document.querySelector('.main');
        if (mainContent) {
            observer.observe(mainContent, { 
                childList: true, 
                subtree: true,
                attributes: config.observeAttributes
            });
            if (window.debugAnalytics) {
                console.log('Enhanced analytics tracking initialized for Streamlit');
            }
        } else {
            console.warn('Could not find Streamlit main content for analytics tracking');
        }
    }, 2000);
    
    // Also track hash changes (can happen in Streamlit)
    window.addEventListener('hashchange', handlePageChange);
    
    // Track when visibility changes (user tabs back to the app)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            if (window.debugAnalytics) {
                console.log('User returned to the page, tracking event');
            }
            trackEvent('Visibility', 'return_to_page', document.title);
        }
    });
    
    return {
        trackPageView,
        trackEvent,
        trackJobApply,
        trackSearch,
        trackFilter,
        trackLogin,
        trackFeatureUsage
    };
}

// Enable debug mode during development/troubleshooting
window.debugAnalytics = true;

// Initialize tracking automatically
let analyticsTracker;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        analyticsTracker = setupStreamlitPageTracking({ debug: true });
    });
} else {
    analyticsTracker = setupStreamlitPageTracking({ debug: true });
}

// Make these functions globally available
window.trackPageView = trackPageView;
window.trackEvent = trackEvent;
window.trackJobApply = trackJobApply;
window.trackSearch = trackSearch;
window.trackFilter = trackFilter;
window.trackLogin = trackLogin;
window.trackFeatureUsage = trackFeatureUsage;
