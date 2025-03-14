// JavaScript to make job listings more compact
document.addEventListener('DOMContentLoaded', function() {
    // Function to apply compact styling
    function makeJobListingsCompact() {
        // Target all job container parent elements
        const jobContainers = document.querySelectorAll('.job-container');
        jobContainers.forEach(container => {
            // Get the parent elements that Streamlit adds
            let parent = container.parentElement;
            while (parent && parent.className !== 'stContainer') {
                // Remove padding and margins
                parent.style.padding = '0';
                parent.style.margin = '0';
                parent.style.lineHeight = '1';
                
                // Move up to next parent
                parent = parent.parentElement;
            }
        });
        
        // Target checkboxes to make them more compact
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            // Make checkboxes smaller
            checkbox.style.width = '14px';
            checkbox.style.height = '14px';
            
            // Also adjust the parent container
            let parent = checkbox.parentElement;
            for (let i = 0; i < 3 && parent; i++) {
                parent.style.marginTop = '0';
                parent.style.marginBottom = '0';
                parent.style.paddingTop = '0';
                parent.style.paddingBottom = '0';
                parent = parent.parentElement;
            }
        });
    }
    
    // Initial call
    makeJobListingsCompact();
    
    // Set up a MutationObserver to detect when Streamlit updates the DOM
    const observer = new MutationObserver(function(mutations) {
        makeJobListingsCompact();
    });
    
    // Start observing the document body for DOM changes
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
});
