# Google Analytics Integration Guide

This document explains the Google Analytics integration in the Job Tracker application and provides troubleshooting steps for common issues.

## Current Implementation

The Job Tracker application uses Google Analytics 4 (GA4) to track user interactions. The tracking code has been enhanced to work better with Streamlit's single-page application architecture.

### Key Components

1. **Main GA4 Code**: Embedded in `dashboard.py` with enhanced configuration
2. **Analytics Helpers**: Functions in `static/analytics.js` for tracking different events
3. **Debug Tools**: Analytics debug page and testing utilities
4. **Admin Dashboard**: Analytics section in the admin dashboard

## Known Issues

The primary issues affecting Google Analytics tracking on the Job Tracker application:

1. **Non-HTTPS Deployment**: Google Analytics works best on secure (HTTPS) sites. Many browsers block tracking on non-secure sites.
2. **IP Address Instead of Domain**: Using a direct IP address instead of a domain name can affect tracking reliability.
3. **Multiple Implementation Conflicts**: Previous implementation had multiple conflicting GA scripts.

## Changes Made

The following changes have been implemented to improve Google Analytics tracking:

1. **Enhanced GA4 Configuration**:
   - Added IP anonymization
   - Configured transport mechanism
   - Added debug mode for troubleshooting
   - Improved cookie handling

2. **Improved Event Tracking**:
   - Better error handling
   - Event queuing for reliability
   - Enhanced page view tracking for Streamlit

3. **Debug Tools**:
   - Added analytics debug page
   - Created test utilities
   - Integrated admin dashboard

4. **Documentation**:
   - Added HTTPS setup guide
   - Created this integration guide
   - Added inline code comments

## Setup Instructions

### 1. Verify Google Analytics Property

1. Log in to your Google Analytics account: https://analytics.google.com/
2. Verify you're using the correct Measurement ID (G-EGVJQG5M34)
3. Check that data streams are properly configured
4. Ensure that enhanced measurement is enabled

### 2. Set Up HTTPS (Strongly Recommended)

For optimal tracking, setting up HTTPS is strongly recommended. Follow the detailed instructions in `ORACLE_HTTPS_SETUP.md`.

The three main options are:
- Using Oracle Cloud Load Balancer with SSL
- Using Nginx with Let's Encrypt
- Using Cloudflare (easiest option)

### 3. Register a Domain (Recommended)

Using a proper domain name instead of an IP address improves tracking reliability:
1. Register a domain (can use free services like Freenom)
2. Point the domain to your Oracle Cloud instance
3. Update your application's configuration to use the domain

### 4. Testing Your Implementation

Use the built-in testing tools to verify your implementation:

1. Navigate to the Analytics Dashboard in the admin section
2. Use the debug page to check the status of Google Analytics
3. Send test events and verify they appear in your GA4 real-time dashboard

## Troubleshooting

### Google Analytics Not Tracking Events

1. **Check Browser Console**: Look for errors related to Google Analytics
2. **Verify HTTPS**: Confirm you're using HTTPS or implement it following the guide
3. **Check for Ad Blockers**: Some users may have ad blockers that prevent tracking
4. **Verify Cookie Settings**: Make sure cookies are enabled in the browser
5. **Debug Mode**: Use the debug tool to check GA4 status

### Events Not Showing in GA4 Dashboard

1. **Check Property**: Verify you're looking at the correct GA4 property
2. **Time Delay**: GA4 can have a delay in processing events (especially for standard reports)
3. **Check Real-time**: Real-time reports should show events almost immediately
4. **Check Filters**: Ensure no filters are preventing events from being recorded

### HTTPS Setup Issues

If you're having trouble setting up HTTPS:
1. Review the detailed instructions in `ORACLE_HTTPS_SETUP.md`
2. Consider using Cloudflare as a simpler alternative
3. Check Oracle Cloud firewall rules to ensure ports 80 and 443 are open

## Best Practices

1. **Event Naming**: Use consistent, descriptive names for events
2. **Minimize Tracking**: Only track important user interactions
3. **Regular Testing**: Periodically verify tracking is working
4. **Privacy Compliance**: Ensure your tracking complies with privacy regulations

## Google Analytics Admin Dashboard

The new Analytics Dashboard in the admin section provides:
1. Real-time tracking status
2. Testing tools
3. Implementation diagnostics
4. Access to documentation

## Future Enhancements

Potential future improvements:
1. **User ID Tracking**: Associate events with specific user IDs
2. **E-commerce Tracking**: If applicable for your use case
3. **Custom Dimensions**: Add additional data for more detailed analysis
4. **Server-side Tracking**: For more reliable tracking regardless of client settings

For questions or issues, please refer to the Google Analytics documentation or contact the development team.
