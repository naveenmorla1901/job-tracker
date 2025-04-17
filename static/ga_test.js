/**
 * Google Analytics Test Utility
 * This script helps verify that Google Analytics is working properly
 */

// Initialize test variables
let gaLoaded = false;
let eventsQueued = 0;
let eventsSent = 0;
let testsPassed = 0;
let testsFailed = 0;

// Keep track of test results
const testResults = {
    gaLoaded: false,
    cookiesEnabled: false,
    httpsProtocol: false,
    eventsTracked: false,
    dataLayerExists: false
};

// Test if Google Analytics is loaded
function testGALoaded() {
    console.log('Testing if Google Analytics is loaded...');
    if (typeof gtag === 'function') {
        console.log('✅ Google Analytics is loaded');
        gaLoaded = true;
        testResults.gaLoaded = true;
        testsPassed++;
    } else {
        console.error('❌ Google Analytics is not loaded');
        testsFailed++;
    }
}

// Test if cookies are enabled
function testCookies() {
    console.log('Testing if cookies are enabled...');
    if (navigator.cookieEnabled) {
        console.log('✅ Cookies are enabled');
        testResults.cookiesEnabled = true;
        testsPassed++;
    } else {
        console.error('❌ Cookies are disabled');
        testsFailed++;
    }
}

// Test HTTPS
function testHttps() {
    console.log('Testing if HTTPS is enabled...');
    if (window.location.protocol === 'https:') {
        console.log('✅ HTTPS is enabled');
        testResults.httpsProtocol = true;
        testsPassed++;
    } else {
        console.warn('⚠️ HTTPS is not enabled, which may affect Google Analytics');
        testsFailed++;
    }
}

// Test data layer
function testDataLayer() {
    console.log('Testing if dataLayer exists...');
    if (window.dataLayer && Array.isArray(window.dataLayer)) {
        console.log('✅ dataLayer exists');
        testResults.dataLayerExists = true;
        testsPassed++;
    } else {
        console.error('❌ dataLayer does not exist');
        testsFailed++;
    }
}

// Test sending an event
function testSendEvent() {
    console.log('Testing if events can be sent...');
    
    if (typeof gtag !== 'function') {
        console.error('❌ Cannot send event - gtag not defined');
        testsFailed++;
        return;
    }
    
    eventsQueued++;
    const testEventName = 'test_event_' + Math.floor(Math.random() * 1000);
    
    try {
        gtag('event', testEventName, {
            'event_category': 'Testing',
            'event_label': 'GA Test ' + new Date().toISOString(),
            'debug_mode': true
        });
        
        console.log('✅ Test event queued: ' + testEventName);
        eventsSent++;
        testResults.eventsTracked = true;
        testsPassed++;
    } catch (error) {
        console.error('❌ Error sending test event:', error);
        testsFailed++;
    }
}

// Run all tests
function runAllTests() {
    console.log('=== Starting Google Analytics Tests ===');
    
    testGALoaded();
    testCookies();
    testHttps();
    testDataLayer();
    
    if (gaLoaded) {
        testSendEvent();
    }
    
    // Output summary
    console.log('\n=== Test Summary ===');
    console.log(`Tests Passed: ${testsPassed}`);
    console.log(`Tests Failed: ${testsFailed}`);
    console.log(`Events Queued: ${eventsQueued}`);
    console.log(`Events Sent: ${eventsSent}`);
    
    return testResults;
}

// Delay test execution to ensure GA has time to load
setTimeout(runAllTests, 2000);

// Export test functions
window.gaTests = {
    runAllTests,
    testGALoaded,
    testCookies,
    testHttps,
    testDataLayer,
    testSendEvent,
    getResults: () => testResults
};
